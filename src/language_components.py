from __future__ import annotations

from typing import Type, Iterable

import neomodel
from neomodel import (StructuredNode, StringProperty, RelationshipTo, StructuredRel, DoesNotExist, MultipleNodesReturned, NeomodelPath)

from src.constants import SimpleTerms, yaml_type
from src.exceptions import AmbiguousNameException, DoNotExistException, AmbiguousSubFeaturesException


class IName(StructuredNode):
    name = StringProperty(unique_index=True, required=True)


class IKind(StructuredNode):
    kind = StringProperty()


class LangCodeNode(StructuredNode, IName, IKind):
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
    def _get_from_all(cls, node_class: Type[StructuredNode], name: str | StringProperty, kind: str | StringProperty) -> LangCodeNode:
        try:
            node = node_class.nodes.get(name=name, kind=kind)
        except MultipleNodesReturned:
            raise AmbiguousNameException(name=name, kind=kind)
        except DoesNotExist:
            raise DoNotExistException(name=name, kind=kind)
        except:
            raise
        return node


class Featuring(StructuredRel):
    rel_name = 'FEATURES'


class IsSuperOf(StructuredRel):
    rel_name = 'IS_SUPER'


class Feature(LangCodeNode):
    children = RelationshipTo(
        cls_name='Feature',  # TODO: check if "Feature.__class__.__nam/e__" can work
        relation_type=IsSuperOf.rel_name,
        model=IsSuperOf,
    )


class Unit(LangCodeNode, IName, IKind):
    features = RelationshipTo(
        cls_name=Feature.__class__.__name__,
        relation_type=Featuring.rel_name,
        model=Featuring,
    )

    def _get_paths_down_for(self, feature_name: str) -> yaml_type:
        feature: Feature = self._get_from_all(Feature, feature_name, self.kind)
        feature_hierarchy_part = f'{feature:node}-[:{IsSuperOf.rel_name}*]-(:{feature:label})'
        paths: list[NeomodelPath] = neomodel.db.cypher_query(f'MATCH p = {feature_hierarchy_part}<-[:{Featuring.rel_name}]-{self:node} return p')
        return paths

    def _get_all_nth(self, feature_name: str, n: int) -> Iterable[yaml_type]:
        paths = self._get_paths_down_for(feature_name)
        n -= int(n < 0)
        features = map(lambda p: p.nodes[:-1][n], paths)
        return features

    def get_all_leafs(self, feature_name: str) -> Iterable[yaml_type]:
        return self._get_all_nth(feature_name, -1)

    def get_all_next(self, feature_name: str) -> Iterable[yaml_type]:
        return self._get_all_nth(feature_name, 1)

    def get_one(self, feature_name: str) -> yaml_type:
        next_features = list(self.get_all_next(feature_name))
        if not next_features:
            raise DoNotExistException(feature_name, self.kind)
        if len(next_features) > 1:
            raise AmbiguousSubFeaturesException(feature_name, self.kind)
        return next_features[1]

    def is_(self, feature_name: str) -> bool:
        paths = self._get_paths_down_for(feature_name)
        return bool(paths)


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

    def add_feature(self, name, config: yaml_type, kind: str) -> None:
        if self._is_complex_feature(config):
            for subname, subconfig in config.items():
                self.add_feature(subname, subconfig, kind)
        feature = Feature(name=name, kind=kind, tree=config)
        self._features.setdefault(kind, {}).setdefault(name, feature)

    def _is_complex_feature(self, config: yaml_type) -> bool:
        return isinstance(config, dict)
