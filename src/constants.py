from dataclasses import dataclass
from pathlib import Path


basic_yaml_type = str | int | bool | None
complex_yaml_type = dict | list
yaml_type = basic_yaml_type | complex_yaml_type


@dataclass(frozen=True)
class SimpleTerms:
    LANGUAGES = 'languages'
    LANGUAGE = 'language'
    GENERAL = 'general'
    NATIVE_NAME = 'native-name'
    FEATURES = 'features'
    RULES = 'rules'
    MORPHOLOGY = 'morphology'
    MORPHEMES = 'morphemes'
    MORPHEME = 'morpheme'
    ORTHOGRAPHY = 'orthography'
    SCRIPT = 'script'
    GRAPHEMES = 'graphemes'
    GRAPHEME = 'grapheme'
    ELEMS = 'elems'
    FORM = 'form'
    COMPOUND = 'compound'


@dataclass(frozen=True)
class ComplexTerms:
    UNTIS = (SimpleTerms.GRAPHEMES, SimpleTerms.MORPHEMES)
    UNIT = (SimpleTerms.GRAPHEME, SimpleTerms.MORPHEME)
    UNIT_SUBKEYS = (SimpleTerms.ELEMS, SimpleTerms.FEATURES)
    FORMING_KEYS = (SimpleTerms.FORM, SimpleTerms.COMPOUND)


@dataclass(frozen=True)
class Paths:
    LANGUAGES = Path(__file__).parent / SimpleTerms.LANGUAGES
