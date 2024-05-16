from __future__ import annotations

import operator as op
from typing import Iterable, Dict, Optional

import neomodel
import pydash as _
# noinspection PyUnresolvedReferences
from neomodel import StructuredNode, StringProperty, RelationshipTo, StructuredRel, DoesNotExist, MultipleNodesReturned, NeomodelPath, NodeMeta, config, \
    Property  # For some reason, the neomodel requires to import it
from pydash import chain as c
from toolz import keyfilter, itemmap

from src import utils
from src.constants import CT
from src.exceptions import AmbiguousNameException, DoNotExistException, AmbiguousSubFeaturesException, CannotCreatePropertyException, PropertyNotFound
from src.lang_typing import YamlType, Config, BasicYamlType
from src.utils import is_dict, adjust_str, exceptions_to

config.DATABASE_URL = 'bolt://neo4j_username:neo4j_password@localhost:7687'


class IName(StructuredNode):
    name = StringProperty(required=True)


class IKind(StructuredNode):
    kind = StringProperty()


class IPropertied:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__custom_property_names: set = set()

    @property
    def custom_property_names(self) -> set:
        return self.__custom_property_names.copy()

    @property
    def _core_property_names(self) -> Iterable[str]:
        interface_to_name = c().get('__name__').tail().snake_case()
        interfaces_to_names = c().map_(interface_to_name)
        return interfaces_to_names((IName, IKind))

    def get_property(self, name: str) -> YamlType:
        if name not in self.custom_property_names:
            raise PropertyNotFound(self, name)
        return self.__getattribute__(name)

    @exceptions_to()
    def has_property(self, name: str) -> bool:
        return self.get_property(name)

    def set_property(self, name: str, val: YamlType = None) -> None:
        if name not in self.custom_property_names and hasattr(self, name):
            raise CannotCreatePropertyException(name)
        self.__custom_property_names.add(name)
        setattr(self, name, val)

    def remove_property(self, name: str) -> None:
        if self.has_property(name):
            self.__delattr__(name)


class LangCodeNode(IName, IKind, StructuredNode, IPropertied):
    # TODO: resolve as in: https://stackoverflow.com/questions/5189699/how-to-make-a-class-property
    # @classmethod
    # @property
    # def main_label(cls) -> str:
    #     return cls.__class__.__name__

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__custom_property_names: set = set()

    def __format__(self, format_spec) -> str:
        match format_spec:
            case 'label' | 'l': return self.__class__.__name__
            case 'kind': return str(self.kind)
            case 'name': return str(self.name)
            case 'properties' | 'props': return f'{{ name: {self.name}, kind: {self.kind} }}'
            case 'node' | 'n': return f'(:{self:label} {self:properties})'
            case _: raise ValueError(f'Format spec {format_spec} has not been defined')

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
    @exceptions_to(true=AmbiguousNameException, false=DoesNotExist, if_none=True)
    def is_node_existing(cls, **kwargs):  # The name to minimalize the chances for the name to be a property
        return cls.get_from_all(raises=True, **kwargs)

    @adjust_str('.self')
    def __repr__(self):
        return f'{self.__class__.__name__}({self.name=}, {self.kind=})'


class Featuring(StructuredRel):
    rel_name = 'FEATURES'


class IsSuperOf(StructuredRel):
    rel_name = 'IS_SUPER'


class Feature(LangCodeNode):
    type = StringProperty(
        choices=utils.map_conf_list_to_dict(CT.FEATURE_TYPES)
    )
    children = RelationshipTo(
        cls_name='Feature',  # TODO: check if "Feature.__class__.__name__" can work
        relation_type=IsSuperOf.rel_name,
        model=IsSuperOf,
    )

    @adjust_str('.self')
    def __repr__(self):
        repr: str = super().__repr__()
        return repr[:-1] + f', {self.type=})'

    def is_leaf(self) -> bool:
        return not self.children.manager.is_connected()


class Unit(LangCodeNode):
    features = RelationshipTo(
        cls_name=Feature.__class__.__name__,
        relation_type=Featuring.rel_name,
        model=Featuring,
    )

    def _get_paths_down_for(self, feature_name: str) -> YamlType:
        feature: Feature = Feature.get_from_all(feature_name, self.kind)
        feature_hierarchy_part = f'{feature:node}-[:{IsSuperOf.rel_name}*]-(:{feature:label})'
        paths: list[NeomodelPath] = neomodel.db.cypher_query(f'MATCH p = {feature_hierarchy_part}<-[:{Featuring.rel_name}]-{self:node} return p')
        return paths

    def _get_all_nth(self, feature_name: str, n: int) -> Iterable[YamlType]:
        n -= int(n < 0)
        paths = self._get_paths_down_for(feature_name)
        features = c(paths).drop_right().nth(n).value()
        return features

    def get_all_leafs(self, feature_name: str) -> Iterable[YamlType]:
        return self._get_all_nth(feature_name, -1)

    def get_all_next(self, feature_name: str) -> Iterable[YamlType]:
        return self._get_all_nth(feature_name, 1)

    def get_next(self, feature_name: str) -> YamlType:
        match len(all_nexts := list(self.get_all_next(feature_name))):
            case 0: return None
            case 1: return all_nexts[0]
            case _: return all_nexts

    def get_one_next(self, feature_name: str) -> YamlType:
        match next_node := self.get_next(feature_name):
            case None: raise DoNotExistException(feature_name, self.kind)
            case list(): raise AmbiguousSubFeaturesException(feature_name, self.kind)
            case _: return next_node

    def is_(self, feature_name: str) -> bool:
        paths = self._get_paths_down_for(feature_name)
        return bool(paths)

    def set_conf(self, conf: Config) -> None:
        self.clean_conf()
        self.update_conf(conf)

    def clean_conf(self) -> None:
        c(self.__class__.__all_properties__).keys().without(self._core_property_names).for_each(self.__delattr__)  # TODO: make sure that for_each executes the statement

    def update_conf(self, conf: Config) -> None:
        itemmap(_.spread(self.set_conf_entry), conf or {})

    def set_conf_entry(self, key: str, val: YamlType) -> None:
        self

    def set_feature(self, feature_name: str, val: BasicYamlType | Dict) -> None:
        # TODO: think how to handle lists
        # TODO: think of and analyze a critical section to differentiate the exceptions of
        #  - non-existance
        #  - non-connnection
        #  PS: add retries as decorator
        feature = Feature.get_from_all(name=feature_name, kind=self.kind, raises=False)
        featuring_feature = Feature.get_from_all(name=val, kind=self.kind, raises=False)
        if not feature:
            setattr(self, feature_name, val)  # Either a dict or not
        elif feature and featuring_feature:
            self.features.manager.connect(featuring_feature)
        elif feature and not featuring_feature and not is_dict(val):
            self.features.manager.connect(feature, {'val': val})
        elif feature and not featuring_feature and is_dict(val):
            self.update_conf(val)  # TODO: add validation by feature type
        else:
            raise ValueError

