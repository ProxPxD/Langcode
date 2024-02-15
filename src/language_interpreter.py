from typing import Optional

from src.constants import SimpleTerms, complex_yaml_type
from src.language import Language
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
        self._interpret_graphemes(config.graphemes)
        self._interpret_morphemes(config.morphemes)

    def _interpret_general(self, config: DotDict) -> None:
        pass

    def _interpret_graphemes(self, config: DotDict) -> None:
        self._interpret_units_from(config, SimpleTerms.GRAPHEME)

    def _interpret_morphemes(self, config: DotDict) -> None:
        self._interpret_units_from(config, SimpleTerms.MORPHEME)

    def _interpret_units_from(self, config: DotDict, kind: str) -> None:
        for name, config in config.elems.items():
            self._language.add_unit(name, config, kind)

