from __future__ import annotations

from typing import Optional, Sequence

import pydash as _
# noinspection PyUnresolvedReferences
from neomodel import StructuredNode, StringProperty, RelationshipTo, StructuredRel, DoesNotExist, MultipleNodesReturned, NeomodelPath, NodeMeta, config, Property, \
    RelationshipFrom  # For some reason, the neomodel requires to import it
from pydash import chain as c
from toolz import itemmap

from src import utils
from src.constants import CT, ST
from src.exceptions import AmbiguousNameException, DoNotExistException, LangCodeException
from src.lang_typing import YamlType, Config, ComplexYamlType
from src.neomodel_mixins import ICorePropertied, INeo4jFormatable, INeo4jHierarchied, FeaturesNotHierarchied
from src.relationships import Features, Belongs, IsSuperOf
from src.utils import adjust_str, exceptions_to, is_str, is_, is_yaml_type, is_nothing_instance_of_none

config.DATABASE_URL = 'bolt://neo4j_username:neo4j_password@localhost:7687'


class INameProperty(StructuredNode):
    name = StringProperty(required=True)


# class IKindProperty(StructuredNode):
#     kind = StringProperty()


class CoreProperties(ICorePropertied, INameProperty):
    __core_properties_classes_or_names = [INameProperty]


class LangCodeNode(INeo4jFormatable, StructuredNode):
    # TODO: resolve as in: https://stackoverflow.com/questions/5189699/how-to-make-a-class-property
    # @classmethod
    # @property
    # def main_label(cls) -> str:
    #     return cls.__class__.__name__

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__custom_property_names: set = set()

    @classmethod
    def get_from_all(cls, raises: bool = True, **kwargs) -> Optional[LangCodeNode]:
        try:
            return cls.nodes.get(**kwargs)
        except MultipleNodesReturned:
            exception = AmbiguousNameException(**kwargs)
        except DoesNotExist:
            exception = DoNotExistException(**kwargs)
        except Exception as e:
            exception = e

        if raises and exception:
            raise exception
        return None

    @classmethod
    def get_from_all_if_not_already(cls, raises: bool = True, **kwargs) -> Optional[LangCodeNode]:
        potential = next(iter(kwargs.values())) if len(kwargs) == 1 else kwargs.get('name')
        if potential and is_(Feature, potential):
            return potential
        return cls.get_from_all(raises, **kwargs)

    @classmethod
    @exceptions_to(true=AmbiguousNameException, false=DoesNotExist, if_none=True)
    def is_node_existing(cls, **kwargs):  # The name to minimalize the chances for the name to be a property
        return cls.get_from_all(raises=True, **kwargs)

    @adjust_str('self.')
    def __repr__(self):
        return f'{self:label}({self.name=}, {self.kind=})'


class Feature(LangCodeNode, INeo4jHierarchied):
    type = StringProperty(
        choices=utils.map_conf_list_to_dict(CT.FEATURE_TYPES)
    )
    children = RelationshipTo(
        cls_name='Feature',  # TODO: check if "Feature.__class__.__name__" can work
        relation_type=IsSuperOf.rel_name,
        model=IsSuperOf,
    )

    @adjust_str('self.')
    def __repr__(self):
        repr: str = super().__repr__()
        return repr[:-1] + f', {self.type=})'

    def is_leaf(self) -> bool:
        return not self.children.manager.is_connected()

    def add_subfeature(self, child: Features) -> None:
        self.children.manager.connect(child)


class IPropertiedNode:
    def set_property(self, key: str, val: YamlType) -> None:
        setattr(self, key, val)

    def get_property(self, key: str) -> YamlType:
        return getattr(self, key)

    def has_property(self, key: str) -> bool:
        return hasattr(self, key)


# TODO: work on kind
class Unit(LangCodeNode, IPropertiedNode):
    features = RelationshipTo(
        cls_name=Feature.__class__.__name__,
        relation_type=Features.rel_name,
        model=Features,
    )

    def set_new_conf(self, conf: Config) -> None:
        self.clean_conf()
        self.update_conf(conf)

    def clean_conf(self) -> None:
        c(self.__class__.__all_properties__).keys().without(self.core_property_names).for_each(self.__delattr__)  # TODO: make sure that for_each executes the statement

    def update_conf(self, conf: Config) -> None:
        itemmap(_.spread(self.set_conf_entry), conf or {})

    def set_conf_entry(self, key: str, val: YamlType) -> None:
        try:
            feature = Feature.get_from_all(name=key)
            self.set_feature(feature, val)
        except DoNotExistException:
            self.set_property(key, val)
        except Exception:  # TODO: potential verbosity increase
            raise

    def set_feature(self, feature: Features | str, val: YamlType | Feature):
        # TODO: think of and analyze a critical section to differentiate the exceptions of
        #  - non-existance
        #  - non-connnection
        #  PS: add retries as decorator
        feature = Feature.get_from_all(name=feature) if is_str(feature) else feature
        match val:
            case descendant if is_(Feature, descendant):
                self._set_feature_with_descendant(feature, descendant)
            case str() | int() if descendant := feature.get_descendant(name=val, __raises=False):  # TODO: potential improvement depending on feature conf
                self._connect_feature(descendant)
            case list() if descendants := feature.get_descendants(_.map_(val, lambda v: {'name': v}), __raises=False) and is_nothing_instance_of_none(descendant):
                _.for_each(descendants, self._connect_feature)
            case dict() if hierarchied_dict := self._map_dict_to_hierarchied_dict({feature.name: val}):
                features: list[Feature] = utils.get_nested_dict_leafs(hierarchied_dict)
                _.for_each(features, self._connect_feature)
            case _ if is_yaml_type(val):
                self._connect_feature(feature, val)
            case _:
                raise ValueError

    def _connect_feature(self, feature: Feature, val: YamlType = None) -> None:
        rel_properties = {ST.VAL: val} if val is not None else {}
        self.features.manager.connect(feature, rel_properties)

    def _set_feature_with_descendant(self, feature: Feature, descendant: Feature) -> None:
        if not feature.has_descendant(name=descendant):
            raise FeaturesNotHierarchied(feature, descendant)
        self._connect_feature(descendant)

    @exceptions_to(false=LangCodeException, if_false=None)  # TODO: rename parameters
    def _map_dict_to_hierarchied_dict(self, to_map: dict[str, YamlType]) -> dict[Feature, ComplexYamlType | Feature]:
        unhierarchied_dict = {}
        to_checks = list(to_map.keys())
        while to_checks:
            parent = to_checks.pop()
            parent = Feature.get_from_all_if_not_already(name=parent)
            children = to_map[parent.name].keys()
            to_checks.extend(children)
            children = parent.get_descendants(children)
            unhierarchied_dict[parent] = parent.get_descendants(children)

        return utils.build_nested_dict(unhierarchied_dict)

    def get_feature(self, feature_name: str) -> Feature:
        return Feature.get_in_direct_hierarchy(self, name=feature_name, n=0)

    @exceptions_to(flow_to_bool=True)
    def is_(self, feature_name: str) -> bool:
        return self.get_feature(feature_name)

    def get_feature_values(self, feature_name: str) -> Sequence[YamlType]:
        feature = self.get_feature(feature_name)
        values = feature.get_all_next_down(__connected_node=self)
        return c(values).map_(_.property_('name')).value()


    #
    # def get_feature_value(self, feature_name: str) -> YamlType:
    #     try:
    #         feature = Feature.get_one_next_down_for(name=feature_name, n=0, __connected_node=self)
    #     except DoNotExistException:
    #

    # @exceptions_to(flow_to_bool=True)
    # def has_feature(self, feature_name: str):
    #     return self.get_feature(feature_name)
    #

class Morpheme(Unit):
    pass


class Grapheme(Unit):
    pass


class Language(LangCodeNode):
    features = RelationshipFrom(
        cls_name=LangCodeNode.__class__.__name__,
        relation_type=Belongs.rel_name,
        model=Belongs,
    )


