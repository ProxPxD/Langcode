from __future__ import annotations

from typing import Iterable, Dict, Optional, Callable

import neomodel
from neomodel import (StructuredNode, StringProperty, RelationshipTo, StructuredRel, DoesNotExist, MultipleNodesReturned, NeomodelPath)
# noinspection PyUnresolvedReferences
from neomodel import NodeMeta  # For some reason, the neomodel requires to import it

from src import utils
from src.constants import SimpleTerms, ComplexTerms
from src.exceptions import AmbiguousNameException, DoNotExistException, AmbiguousSubFeaturesException
from src.lang_typing import YamlType, Kind, Config, BasicYamlType
from src.utils import is_dict


def adjust_str(old: str, new: str = ''):
    def decorator(func: Callable[..., str]):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs).replace(old, new)
        return wrapper
    return decorator


class IName(StructuredNode):
    name = StringProperty(unique_index=True, required=True)


class IKind(StructuredNode):
    kind = StringProperty()


class LangCodeNode(IName, IKind, StructuredNode):
    # TODO: resolve as in: https://stackoverflow.com/questions/5189699/how-to-make-a-class-property
    # @classmethod
    # @property
    # def main_label(cls) -> str:
    #     return cls.__class__.__name__

    def __format__(self, format_spec) -> str:
        match format_spec:
            case 'label' | 'l': return self.__class__.__name__
            case 'properties' | 'props': return f'{{ name: {self.name}, kind: {self.kind} }}'
            case 'node' | 'n': return f'(:{self:label} {self:properties})'
            case _: raise ValueError(f'Format spec {format_spec} has not been defined')

    @classmethod
    def _get_from_all(cls, raises: bool = True, **kwargs) -> Optional[LangCodeNode]:
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

    @adjust_str('.self')
    def __repr__(self):
        return f'{self.__class__.__name__}({self.name=}, {self.kind=})'


class Featuring(StructuredRel):
    rel_name = 'FEATURES'


class IsSuperOf(StructuredRel):
    rel_name = 'IS_SUPER'


class Feature(LangCodeNode):
    type = StringProperty(
        choices=utils.map_conf_list_to_dict(ComplexTerms.FEATURE_TYPES)
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


class Unit(LangCodeNode, IName, IKind):
    features = RelationshipTo(
        cls_name=Feature.__class__.__name__,
        relation_type=Featuring.rel_name,
        model=Featuring,
    )

    def _get_paths_down_for(self, feature_name: str) -> YamlType:
        feature: Feature = Feature._get_from_all(feature_name, self.kind)
        feature_hierarchy_part = f'{feature:node}-[:{IsSuperOf.rel_name}*]-(:{feature:label})'
        paths: list[NeomodelPath] = neomodel.db.cypher_query(f'MATCH p = {feature_hierarchy_part}<-[:{Featuring.rel_name}]-{self:node} return p')
        return paths

    def _get_all_nth(self, feature_name: str, n: int) -> Iterable[YamlType]:
        paths = self._get_paths_down_for(feature_name)
        n -= int(n < 0)
        features = map(lambda p: p.nodes[:-1][n], paths)
        return features

    def get_all_leafs(self, feature_name: str) -> Iterable[YamlType]:
        return self._get_all_nth(feature_name, -1)

    def get_all_next(self, feature_name: str) -> Iterable[YamlType]:
        return self._get_all_nth(feature_name, 1)

    def get_one_next(self, feature_name: str) -> YamlType:
        next_features = list(self.get_all_next(feature_name))
        if not next_features:
            raise DoNotExistException(feature_name, self.kind)
        if len(next_features) > 1:
            raise AmbiguousSubFeaturesException(feature_name, self.kind)
        return next_features[1]

    def get_next(self, feature_name: str) -> YamlType:
        match len(all_nexts := list(self.get_all_next(feature_name))):
            case 0: return None
            case 1: return all_nexts[0]
            case _: return all_nexts

    def is_(self, feature_name: str) -> bool:
        paths = self._get_paths_down_for(feature_name)
        return bool(paths)

    def load_conf(self, conf: Config) -> None:
        for feature_name, val in conf.items():
            self.connect_feature(feature_name, val)

    def connect_feature(self, feature_name: str, val: BasicYamlType | Dict) -> None:
        # TODO: think how to handle lists
        # TODO: think of and analyze a critical section to differentiate the exceptions of
        #  - non-existance
        #  - non-connnection
        #  PS: add retries
        feature = Feature._get_from_all(name=feature_name, kind=self.kind, raises=False)
        featuring_feature = Feature._get_from_all(name=val, kind=self.kind, raises=False)
        if not feature:
            setattr(self, feature_name, val)  # Either a dict or not
        elif feature and featuring_feature:
            self.features.manager.connect(featuring_feature)
        elif feature and not featuring_feature and not is_dict(val):
            self.features.manager.connect(feature, {'val': val})
        elif feature and not featuring_feature and is_dict(val):
            self.load_conf(val)  # TODO: add validation by feature type
        else:
            raise ValueError


class Language(IName):
    def __init__(self, name: str):
        super().__init__(name=name)
        self._units: dict[str, dict[str, list[Unit]]] = {}
        self._features: dict[str, dict[str, Feature]] = {}

    def __repr__(self):
        return f'{self.name}({self._units=})'

    def __str__(self):
        return self.name

    def get_units(self, kind: str = None) -> dict:
        return self._units[kind] if kind and self._units.get(kind) else self._units

    @property
    def units(self) -> dict:
        return self._units

    @property
    def morphemes(self) -> dict[str, list[Unit]]:
        return self._units.get(SimpleTerms.MORPHEME, [])

    @property
    def graphemes(self) -> dict[str, list[Unit]]:
        return self._units.get(SimpleTerms.GRAPHEME, [])

    def add_morpheme(self, name: str, config: dict) -> None:
        self.add_unit(name, config, SimpleTerms.MORPHEME)

    def add_grapheme(self, name: str, config: dict) -> None:
        self.add_unit(name, config, SimpleTerms.GRAPHEME)

    def add_unit(self, name: str, config: dict, kind: str) -> None:
        unit = Unit(name=name, kind=kind, features=config)
        self._units.setdefault(kind, {}).setdefault(name, []).append(unit)

    def add_grapheme_feature(self, name: str, config: dict) -> None:
        self.add_feature(name, config, SimpleTerms.GRAPHEME)

    def add_morpheme_feature(self, name: str, config: dict) -> None:
        self.add_feature(name, config, SimpleTerms.MORPHEME)

    def add_feature(self, name, config: YamlType, kind: Kind) -> None:
        if self._is_complex_feature(config):
            for subname, subconfig in config.items():
                self.add_feature(subname, subconfig, kind)
        feature = Feature(name=name, kind=kind, tree=config)
        self._features.setdefault(kind, {}).setdefault(name, feature)

    def _is_complex_feature(self, config: YamlType) -> bool:
        return isinstance(config, dict)
