from typing import Optional

from src.constants import SimpleTerms, complex_yaml_type
from src.language import Language


class LangaugeInterpreter:
    def __init__(self):
        self._language: Optional[Language] = None

    def create(self, name: str, config: dict) -> Language:  # TODO: get name from general
        self._language = Language(name)
        self._interpret(config)
        return self._language

    def _interpret(self, config: dict) -> None:
        self._interpret_general(config.get(SimpleTerms.GENERAL))
        self._interpret_graphemes(config.get(SimpleTerms.GRAPHEMES))
        self._interpret_morphemes(config.get(SimpleTerms.MORPHEMES))

    def _interpret_general(self, config: dict) -> None:
        pass

    def _interpret_graphemes(self, config: dict) -> None:
        self._interpret_units_from(config, SimpleTerms.GRAPHEME)

    def _interpret_morphemes(self, config: dict) -> None:
        self._interpret_units_from(config, SimpleTerms.MORPHEME)

    def _interpret_units_from(self, config: complex_yaml_type, kind: str) -> None:
        units = config.get(SimpleTerms.ELEMS, {}).items()
        for name, config in units:
            self._language.add_unit(name, config, kind)

