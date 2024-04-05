from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


@dataclass(frozen=True)
class SimpleTerms:
    LANGUAGES = 'languages'
    LANGUAGE = 'language'
    GENERAL = 'general'
    NATIVE_NAME = 'native-name'
    FEATURES = 'features'
    FEATURE = 'feature'
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
    TYPE = 'type'
    JOINT = 'joint'
    DISJOINT = 'disjoint'
    VAL = 'val'


@dataclass(frozen=True)
class ComplexTerms:
    UNTIS = (SimpleTerms.GRAPHEMES, SimpleTerms.MORPHEMES)
    UNIT = (SimpleTerms.GRAPHEME, SimpleTerms.MORPHEME)
    UNIT_SUBKEYS = (SimpleTerms.ELEMS, SimpleTerms.FEATURES)
    FORMING_KEYS = (SimpleTerms.FORM, SimpleTerms.COMPOUND)
    FEATURE_TYPES = (SimpleTerms.JOINT, SimpleTerms.DISJOINT)


@dataclass(frozen=True)
class Paths:
    LANGUAGES = Path(__file__).parent / str(SimpleTerms.LANGUAGES)


ST = SimpleTerms
CT = ComplexTerms
