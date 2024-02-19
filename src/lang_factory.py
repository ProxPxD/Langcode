from pathlib import Path

from src.data_normalizer import DataNormalizer
from src.language_components import Language
from src.language_interpreter import LangaugeInterpreter
from src.loaders import ILoader, IPath, LangDataLoader


class LangFactory(ILoader, IPath):
    def __init__(self, path: str | Path = '', language: str = '', **kwargs):
        super().__init__(**kwargs)
        self._lang_data_loader: LangDataLoader = LangDataLoader(path, language)
        self._data_normalizer: DataNormalizer = DataNormalizer()
        self._lang_interpreter: LangaugeInterpreter = LangaugeInterpreter()

    @property
    def path(self) -> Path:
        return self._lang_data_loader.path

    @path.setter
    def path(self, path: str | Path) -> None:
        self._lang_data_loader.path = path

    def load(self, language: str = None, **kwargs) -> Language:
        raw_data = self._lang_data_loader.load(language, **kwargs)
        normalised_data = self._data_normalizer.normalize(raw_data)
        lang = self._lang_interpreter.create(language, normalised_data)
        return lang
