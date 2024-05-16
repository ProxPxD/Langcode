

class IName:
    def __init__(self, name: str):
        super().__init__(name=name)
        self.name = name


class Language(IName):  # TODO: think if should be neo4j node
    def __init__(self, name: str):
        super().__init__(name=name)

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
        return self._units.get(ST.MORPHEME, [])

    @property
    def graphemes(self) -> dict[str, list[Unit]]:
        return self._units.get(ST.GRAPHEME, [])

    def add_morpheme(self, name: str, config: dict) -> None:
        self.add_unit(name, config, ST.MORPHEME)

    def add_grapheme(self, name: str, config: dict) -> None:
        self.add_unit(name, config, ST.GRAPHEME)

    def add_unit(self, name: str, config: dict, kind: str) -> None:
        unit = Unit(name=name, kind=kind, features=config)
        self._units.setdefault(kind, {}).setdefault(name, []).append(unit)

    def add_grapheme_feature(self, name: str, config: dict) -> None:
        self.add_feature(name, config, ST.GRAPHEME)

    def add_morpheme_feature(self, name: str, config: dict) -> None:
        self.add_feature(name, config, ST.MORPHEME)

    def add_feature(self, name, config: YamlType, kind: Kind) -> None:
        if self._is_complex_feature(config):
            for subname, subconfig in config.items():
                self.add_feature(subname, subconfig, kind)
        feature = Feature(name=name, kind=kind, tree=config)
        self._features.setdefault(kind, {}).setdefault(name, feature)

    def _is_complex_feature(self, config: YamlType) -> bool:
        return isinstance(config, dict)
