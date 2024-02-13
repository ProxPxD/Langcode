from pathlib import Path

from src.constants import LangData
from src.language import Language
from src.loaders import ILoader, IPath, LangDataLoader


class LangaugeInterpreter:
    def __init__(self):
        self._language = None

    def create(self, name: str, data: dict) -> Language:
        self._language = Language(name)
        self._interpret_orthography(data.get(LangData.ORTHOGRAPHY))
        self._interpret_morphology(data.get(LangData.MORPHOLOGY))

    def _interpret_orthography(self, orthography: dict) -> None:
        self._interpret_graphemes(orthography.get(LangData.GRAPHEMES))
        self._interpret_grapheme_rules(orthography.get(LangData.RULES))

    def _interpret_morphology(self, morphology: dict) -> None:
        self._interpret_morphemes(morphology.get(LangData.MORPHEMES))
        self._interpret_morpheme_rules(morphology.get(LangData.RULES))

    def _interpret_graphemes(self, graphemes: dict) -> None:
        raise NotImplementedError

    def _interpret_grapheme_rules(self, grapheme_rules: dict) -> None:
        raise NotImplementedError

    def _interpret_morphemes(self, morphemes: dict) -> None:
        raise NotImplementedError

    def _interpret_morpheme_rules(self, morpheme_rules: dict) -> None:
        raise NotImplementedError


class LangFactory(ILoader, IPath):
    def __init__(self, path: str | Path = '', language: str = '', **kwargs):
        super().__init__(**kwargs)
        self._lang_data_loader: LangDataLoader = LangDataLoader(path, language)
        self._lang_interpreter = LangaugeInterpreter()

    @property
    def path(self) -> Path:
        return self._lang_data_loader.path

    @path.setter
    def path(self, path: str | Path) -> None:
        self._lang_data_loader.path = path

    def load(self, language: str = None, **kwargs) -> Language:
        lang_data = self._lang_data_loader.load(language, **kwargs)
        lang = self._lang_interpreter.create(language, lang_data)
        return lang
