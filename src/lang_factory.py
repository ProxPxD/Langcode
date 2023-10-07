from pathlib import Path

from abc import ABC, abstractmethod
import yaml

from src.exceptions import InvalidYamlException, InvalidPathException
from src.constants import LangData
from src.schemas import SchemaValidator


class IPath:
    def __init__(self, path: str | Path = '', **kwargs):
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, path: str | Path) -> None:
        self._path = Path(path)

    def get_path(self) -> Path:
        return self.path

    def set_path(self, path: str | Path) -> None:
        self._path = path

    def set_path_if_not_node(self, path: str | Path, set_path=True) -> None:
        if set_path and path is not None:
            self.path = Path(path)


class ILoader(ABC, IPath):
    @abstractmethod
    def load(self, path: str | Path = None, **kwargs):
        pass


class YamlFileLoader(ILoader, IPath):
    def load(self, path: str | Path = None, **kwargs) -> dict | list:
        self.set_path_if_not_node(path, **kwargs)
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return data

    def is_yaml(self, path: Path) -> bool:
        return path.suffix in ('.yaml', '.yml')


class YamlLoader(YamlFileLoader, ILoader):
    def load(self, path: str | Path = None, **kwargs) -> dict:
        self.set_path_if_not_node(path, **kwargs)
        data = self._load_single(path)
        return data

    def _load_single(self, path: Path) -> dict | list:
        if path.is_dir():
            return {file.stem: self._load_single(file) for file in self.path.iterdir()}
        elif path.is_file() and self.is_yaml(path):
            return super().load(path, set_path=False)
        else:
            raise InvalidPathException


class LangDataLoader(ILoader, IPath):
    def __init__(self, path: str | Path = '', language: str = '', **kwargs):
        super().__init__(**kwargs)
        self.language: str = language
        self._yaml_loader = YamlLoader(path)

    def load(self, language: str = None, **kwargs) -> dict:
        if language is not None:
            self.language = language
        lang_data = self._yaml_loader.load(self.true_path, **kwargs)
        return lang_data

    @property
    def path(self) -> Path:
        return self._yaml_loader.path

    @path.setter
    def path(self, path: str | Path) -> None:
        self._yaml_loader.path = path

    @property
    def true_path(self) -> Path:
        lang_path = self.path / self.language
        if self.path.is_dir() and lang_path.exists():
            return lang_path
        elif not self.language:
            return self.path
        raise InvalidPathException


class LangFactory(ILoader, IPath):
    def __init__(self, path: str | Path = '', language: str = '', **kwargs):
        super().__init__(**kwargs)
        self._lang_data_loader: LangDataLoader = LangDataLoader(path, language)

    @property
    def path(self) -> Path:
        return self._lang_data_loader.path

    @path.setter
    def path(self, path: str | Path) -> None:
        self._lang_data_loader.path = path

    def load(self, language: str = None, **kwargs):
        lang_data = self._lang_data_loader.load(language, **kwargs)
        if not SchemaValidator.validate(lang_data, LangData.LANGUAGE):
            raise InvalidYamlException

