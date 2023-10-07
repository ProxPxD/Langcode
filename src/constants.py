from dataclasses import dataclass
from pathlib import Path


@dataclass
class LangData:
    LANGUAGES = 'languages'
    LANGUAGE = 'language'
    GENERAL = 'general'
    NATIVE_NAME = 'native-name'
    FEATURES = 'features'
    MORPHEMES = 'morphemes'
    GRAPHEMES = 'graphemes'
    FORM = 'form'
    COMPOUND = 'compound'

    FORMING_KEYS = (FORM, COMPOUND)


@dataclass
class Paths:
    LANGUAGES = Path(__file__).parent / LangData.LANGUAGES
