from __future__ import annotations

from typing import Optional, Sequence, Iterator, Type

import pydash as _
# noinspection PyUnresolvedReferences
from neomodel import StructuredNode, StringProperty, RelationshipTo, StructuredRel, DoesNotExist, MultipleNodesReturned, NeomodelPath, config, \
    RelationshipFrom  # For some reason, the neomodel requires to import it
from pydash import chain as c
from toolz import itemmap
from typing_extensions import deprecated

from src import utils, relationships
from src.constants import CT, ST
from src.exceptions import AmbiguousNodeException, DoNotExistException, LangCodeException
from src.lang_typing import YamlType, Config, ComplexYamlType
from src.neomodel_mixins import ICorePropertied, INeo4jFormatable, INeo4jHierarchied, FeaturesNotHierarchied, IRelationQuerable, FullQueryRel
from src.relationships import Features, Belongs, IsSuperOf, HasKind
from src.utils import adjust_str, exceptions_to, is_, is_yaml_type, is_nothing_instance_of_none

config.DATABASE_URL = 'bolt://neo4j:password@localhost:7687'


class INameProperty(StructuredNode):
    name = StringProperty(required=True)


class CoreProperties(ICorePropertied, INameProperty):
    _core_properties_classes_or_names = [INameProperty]


class LangCodeNode(IRelationQuerable):
    # TODO: resolve as in: https://stackoverflow.com/questions/5189699/how-to-make-a-class-property
    # @classmethod
    # @property
    # eme main_label(cls) -> str:
    #     return cls.__class__.__name__

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init(self) -> None:
        raise NotImplementedError

    @classmethod
    def _get_one_by_props_rough(cls, *, raises: bool = True, **kwargs) -> Optional[LangCodeNode]:
        try:
            return cls.nodes.get(**kwargs)
        except MultipleNodesReturned:
            exception = AmbiguousNodeException(**kwargs)
        except DoesNotExist:
            exception = DoNotExistException(**kwargs)
        except Exception as e:
            exception = e

        if raises and exception:
            raise exception
        return None

    @classmethod
    def get_one_by_props(cls, id_name: str | LangCodeNode = None, *, raises: bool = True, **kwargs) -> Optional[LangCodeNode]:
        potential = id_name if not kwargs else kwargs.get('name')
        if potential and is_(LangCodeNode, potential):
            return potential
        kwargs.setdefault('name', potential)
        return cls._get_one_by_props_rough(raises=raises, **kwargs)

    @classmethod
    @exceptions_to(true=AmbiguousNodeException, false=DoesNotExist, if_none=True)
    def is_node_existing(cls, **kwargs):  # The name to minimalize the chances for the name to be a property
        return cls._get_one_by_props_rough(raises=True, **kwargs)

    @deprecated('Use get_one_by_rels_props or get_all_by_rels_props instead')
    def get_relateds(self, *rel_or_rel_props: Type[StructuredRel] | tuple[Type[StructuredRel], dict]) -> Sequence[LangCodeNode]:
        to_dicted_tuple = c().apply_if(lambda rel: (rel, {}), is_(StructuredRel))
        rel_props: Iterator[tuple[StructuredRel, dict]] = map(to_dicted_tuple, rel_or_rel_props)
        all_nodes = []
        for rel, props in rel_props:
            if isinstance(node := props.get('name'), StructuredNode):
                props['name'] = node.name
            nodes, _ = self.cypher(f"MATCH (:{self:label} {self.all_properties} )-[:{rel.get_rel_name()}]-(n {props} ) RETURN (n)")
            all_nodes.extend(nodes) 
        return all_nodes

    @adjust_str('self.')
    def __repr__(self):
        return f'{self:label}({self.name=}, {self.kind=})'

# Lang-wise


class LangWiseCommonNode(LangCodeNode):
    pass


class Kind(LangCodeNode):
    kinded = relationships.create_rel(RelationshipFrom, 'Kinded', HasKind)


class IIdentifier(LangCodeNode):
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)


class IConfigurable(LangCodeNode):
    def __init__(self, conf: Config = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._conf = conf

    def init(self) -> None:
        if self._conf is not None:
            self.set_conf(self._conf)
            self._conf = None

    def set_conf(self, conf: Config) -> None:
        self.clean_conf()
        self.update_conf(conf)

    def clean_conf(self) -> None:
        c(self.__class__.__all_properties__).keys().without(self.core_property_names).for_each(self.__delattr__)  # TODO: make sure that for_each executes the statement

    def update_conf(self, conf: Config) -> None:
        c(conf or {}).apply(dict.items).map_(_.spread(self.set_conf_entry)).value()

    def set_conf_entry(self, key: str, val: YamlType) -> None:
        raise NotImplementedError


class LangSpecificNode(IIdentifier, IConfigurable, LangCodeNode):
    lang = relationships.create_rel(RelationshipTo, 'Language', Belongs)

    def _adjust_own_rels(self, rels: Sequence[FullQueryRel]) -> list[FullQueryRel]:
        return self._adjust_own_rels_if_saved(rels, lambda rels: [(Belongs, Language, self.lang.single()), *rels])


class Kinded(LangSpecificNode):
    kind = relationships.create_rel(RelationshipTo, Kind, HasKind)

    def _adjust_own_rels(self, rels: Sequence[FullQueryRel]) -> list[FullQueryRel]:
        return self._adjust_own_rels_if_saved(rels, lambda rels: [(HasKind, LangWiseCommonNode, self.kind.single()), *rels])


class IPropertiedNode:
    def set_property(self, key: str, val: YamlType) -> None:
        setattr(self, key, val)

    def get_property(self, key: str) -> YamlType:
        return getattr(self, key)

    def has_property(self, key: str) -> bool:
        return hasattr(self, key)


class Feature(IPropertiedNode, Kinded, INeo4jHierarchied):
    type = StringProperty(
        choices=utils.map_conf_list_to_dict(CT.FEATURE_TYPES)
    )
    children = relationships.create_rel(RelationshipTo, 'Feature', IsSuperOf)

    @adjust_str('self.')
    def __repr__(self):
        repr: str = super().__repr__()
        return repr[:-1] + f', {self.type=})'

    def is_leaf(self) -> bool:
        return not self.children.manager.is_connected()

    def add_subfeature(self, child: Features | str) -> None:
        child = self.get_one_own_by_rels_props(from_node_props=child)  # TODO: automate label in own methods
        self.children.manager.connect(child)

    def set_conf_entry(self, key: str, val: YamlType) -> None:
        raise NotImplementedError


# TODO: work on kind
class Unit(Kinded, IPropertiedNode):
    features = relationships.create_rel(RelationshipTo, Feature, Features)

    def set_conf_entry(self, key: str, val: YamlType) -> None:
        try:
            feature = self.get_one_own_by_rels_props(from_node=Feature, from_node_props=key)
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
        feature = self.get_one_own_by_rels_props(from_node_props=feature)
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
            parent = self.get_one_own_by_rels_props(from_node=Feature, from_node_props=parent)
            children = to_map[parent.name].keys()
            to_checks.extend(children)
            children = parent.get_descendants(children)
            unhierarchied_dict[parent] = parent.get_descendants(children)

        return utils.build_nested_dict(unhierarchied_dict)

    def get_feature(self, feature_name: str) -> Feature:
        return Feature.get_one_nth_down_for(name=feature_name, n=0, __connected_node=self)

    @exceptions_to(flow_to_bool=True)
    def is_(self, feature_name: str) -> bool:
        return self.get_feature(feature_name)

    def get_feature_values(self, feature_name: str) -> Sequence[YamlType]:
        feature = self.get_feature(feature_name)
        values = feature.get_all_next_down(__connected_node=self)
        return c(values).map_(_.property_('name')).value()


class Language(LangCodeNode):
    units = relationships.create_rel(RelationshipFrom, Unit, Belongs)
    features = relationships.create_rel(RelationshipFrom, LangCodeNode, Belongs)

    def _adjust_own_rels(self, rels: Sequence[FullQueryRel]) -> Sequence[FullQueryRel]:
        return [(Belongs, Language, self), *super()._adjust_own_rels(rels)]

    def add_unit(self, kind: str, unit: Unit | str, conf: dict = None) -> None:
        unit = self.get_unit(kind, unit)  # TODO: get_or_create?
        unit.set_conf(conf)

    def get_unit(self, kind: str, unit: str) -> Unit:
        unit = self.get_one_by_rels_props(from_node=Unit, name=unit, rels=((HasKind, LangWiseCommonNode, kind),))
        return unit

    def add_feature(self, kind: str, feature: Feature | str, **conf) -> None:
        feature = self.get_feature(kind, feature)
        feature.set_conf(conf)

    def get_feature(self, kind: str, feature: Features | str) -> Feature:
        # TODO: Get Or Create?
        feature = self.get_one_own_by_rels_props(from_node=Feature, name=feature, rels=((HasKind, LangWiseCommonNode, kind),))
        return feature
