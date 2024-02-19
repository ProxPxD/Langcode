from typing import Optional

from src.constants import SimpleTerms, complex_yaml_type
from src.language_components import Language
from tests.lang_code_test import DotDict


class LangaugeInterpreter:
    def __init__(self):
        self._language: Optional[Language] = None

    def create(self, name: str, config: dict) -> Language:  # TODO: get name from general
        self._language = Language(name)
        dot_dict = DotDict(config)
        self._interpret(dot_dict)
        return self._language

    def _interpret(self, config: DotDict) -> None:
        self._interpret_general(config.general)
        self._interpret_features(config.features)
        self._interpret_units_from(config.graphemes, SimpleTerms.GRAPHEME)
        self._interpret_units_from(config.morphemes, SimpleTerms.MORPHEME)

    def _interpret_general(self, config: DotDict) -> None:
        pass

    def _interpret_features(self, config: DotDict) -> None:
        self._interpret_unit_features(config.graphemes, SimpleTerms.GRAPHEME)
        self._interpret_unit_features(config.morphemes, SimpleTerms.MORPHEME)

    def _interpret_unit_features(self, config: DotDict, kind: str) -> None:
        for name, subconfig in config.items():
            self._language.add_feature(name, subconfig, kind)

    def _interpret_units_from(self, config: DotDict, kind: str) -> None:
        self._interpret_units_from_elems(config, kind)
        self._interpret_units_from_features(config, kind)

    def _interpret_units_from_elems(self, config: DotDict, kind: str) -> None:
        for name, config in config.elems.items():
            self._language.add_unit(name, config, kind)

    def _interpret_units_from_features(self, config: DotDict, kind: str) -> None:
        for feature, elems in config.features.items():
            self._interpret_units_from_feature(elems, feature, kind)

    def _interpret_units_from_feature(self, config: DotDict, feature: str, kind: str) -> None:
        pass  # self._language.add_feature()