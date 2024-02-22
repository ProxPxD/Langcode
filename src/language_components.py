from __future__ import annotations

from typing import Any, Optional

from src.constants import SimpleTerms, yaml_type
from src.dot_dict import DotDict

from neomodel import (config, StructuredNode, StringProperty, IntegerProperty,
    UniqueIdProperty, RelationshipTo, StructuredRel)


class IName(StructuredNode):
    name = StringProperty(unique_index=True, required=True)


class IKind(StructuredNode):
    kind = StringProperty()


class Feature(StructuredNode, IName, IKind):
    pass


class Featuring(StructuredRel):
    rel_name = 'features'


class Unit(StructuredNode, IName, IKind):
    features = RelationshipTo(Feature.__class__.__name__, Featuring.rel_name, model=Featuring)

    def get(self, feature_name: str) -> yaml_type:
        # consonant
        # vowel
        # - horizontal
        #   - front
        #   - back
        # - vertical
        #   - high
        #   - mid
        #   - low
        feature = Feature.nodes.get(name=feature_name)

        self.features.manager.all_relationships

    def is_(self, feature_name: str) -> bool:

        raise NotImplementedError


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
