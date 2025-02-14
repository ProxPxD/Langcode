from pathlib import Path

from src.language_components import Language
from src.loading.loaders import IFileLoader, IPathable, LangDataFileLoader
from src.interpreting.schema_validator import LanguageSchema


class LangFactory(IFileLoader, IPathable):
    def __init__(self, path: str | Path = '', language: str = '', **kwargs):
        super().__init__(**kwargs)
        self._lang_data_loader: LangDataFileLoader = LangDataFileLoader(path, language)

    @property
    def path(self) -> Path:
        return self._lang_data_loader.path

    @path.setter
    def path(self, path: str | Path) -> None:
        self._lang_data_loader.path = path

    def load(self, language: str = None, **kwargs) -> Language:
        raw_data = self._lang_data_loader.load(language, **kwargs)
        lang = LanguageSchema(**raw_data).to_lang(language)
        return lang
