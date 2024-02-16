from typing import Any, Iterable, Optional

from iteration_utilities import flatten

from src.constants import SimpleTerms, yaml_type


class IName:
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self._name: str = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        raise NotImplementedError


class IKind:
    def __init__(self, kind: str, **kwargs):
        super().__init__(**kwargs)
        self._kind: str = kind

    @property
    def kind(self) -> str:
        return self._kind

    @kind.setter
    def kind(self, kind: str) -> None:
        raise NotImplementedError  # TODO: probably never allowed


class Unit(IName, IKind):
    def __init__(self, name: str, kind: str, features: Optional[dict] = None):
        super().__init__(name=name, kind=kind)
        self._features = features or {}

    def __getitem__(self, key: str) -> yaml_type:
        # TODO: make available nested values
        return self._features[key]

    def __setitem__(self, key: str, value: yaml_type) -> None:
        self._features[key] = value

    def __contains__(self, item: yaml_type):
        # TODO: adjust to nested values when implemented
        return item in self._features

    def get(self, key: str, default: Any = None):
        return self[key] if key in self else default

    def __repr__(self):
        return self.kind.capitalize() + f'({self.name=}, {self._features=})'


class Feature(IName, IKind):
    def __init__(self, name: str, kind: str, tree: Optional[dict] = None):
        super().__init__(name=name, kind=kind)


class Language(IName):
    def __init__(self, name: str):
        super().__init__(name=name)
        self._units: dict[str, list[Unit]] = {}
        self._features: dict[str, list[Feature]] = {}

    def __repr__(self):
        return f'{self.name}({self._units=})'

    def __str__(self):
        return self.name

    @property
    def units(self) -> Iterable[Unit]:
        return flatten(self._units.values())

    @property
    def morphemes(self) -> Iterable[Unit]:
        return self._units.get(SimpleTerms.MORPHEME, [])

    @property
    def graphemes(self) -> Iterable[Unit]:
        return self._units.get(SimpleTerms.GRAPHEME, [])

    def add_morpheme(self, name: str, config: dict) -> None:
        self.add_unit(name, config, SimpleTerms.MORPHEME)

    def add_grapheme(self, name: str, config: dict) -> None:
        self.add_unit(name, config, SimpleTerms.GRAPHEME)

    def add_unit(self, name: str, config: dict, kind: str) -> None:
        unit = Unit(name=name, kind=kind, features=config)
        self._units.setdefault(kind, []).append(unit)

    def add_grapheme_feature(self, name: str, config: dict) -> None:
        self.add_feature(name, config, SimpleTerms.GRAPHEME)

    def add_morpheme_feature(self, name: str, config: dict) -> None:
        self.add_feature(name, config, SimpleTerms.MORPHEME)

    def add_feature(self, name, config: yaml_type, kind: str) -> None:
        if self._is_complex_feature(config):
            for subname, subconfig in config.items():
                self.add_feature(subname, subconfig, kind)
        feature = Feature(name=name, kind=kind, tree=config)
        self._features.setdefault(kind, []).append(feature)

    def _is_complex_feature(self, config: yaml_type) -> bool:
        return isinstance(config, dict)
