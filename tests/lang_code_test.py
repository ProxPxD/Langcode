from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import yaml
from toolz import valfilter

from src.data_normalizer import DataNormalizer
from src.dot_dict import DotDict
from src.lang_factory import LangaugeInterpreter, LangFactory
from src.language import Language
from src.loaders import LangDataLoader
from tests.abstractTest import AbstractTest

yaml_types = dict | bool | str | int | None


@dataclass
class Paths:
    LANGUAGES = Path(__file__).parent / 'languages'
    DEFAULTS = LANGUAGES / 'general_defaults.yaml'


class AbstractLangCodeTest(AbstractTest):
    accepted_similarity = .5

    defaults = yaml.safe_load(open(Paths.DEFAULTS, 'r'))
    data_loader = LangDataLoader(Paths.LANGUAGES)
    lang_interpreter = LangaugeInterpreter()
    data_normalizer = DataNormalizer()
    lang_factory = LangFactory(Paths.LANGUAGES)

    not_language_files = ('general_defaults', )
    all_paths: list[Path]
    all_langs: list[str]
    all_data: dict[str, dict]
    all_test_properties: dict[str, DotDict]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loaded_langs = {}
        self.maxDiff = None

    def load_lang(self, name: str) -> Language:
        if name not in self._loaded_langs:
            self._loaded_langs[name] = self.lang_factory.load(name)
        return self._loaded_langs[name]

    @classmethod
    def init(cls):
        cls.all_paths = [path for path in Paths.LANGUAGES.iterdir() if path.stem not in cls.not_language_files]
        cls.all_langs = [path.stem for path in cls.all_paths]
        cls.all_data = {lang: cls.data_loader.load(lang) for lang in cls.all_langs}
        cls.all_test_properties: dict[str, DotDict] = {lang: DotDict(data.get('general'), defaults=cls.defaults).test_properties for lang, data in cls.all_data.items()}

    @classmethod
    def get_langs_where(cls, condition: Callable[[DotDict], bool] = lambda _: True) -> Iterable[str]:
        return valfilter(condition, cls.all_test_properties).keys()

    @classmethod
    def get_normalised_data(cls, lang_name: str) -> DotDict:
        raw_data = cls.data_loader.load(lang_name)
        data = cls.data_normalizer.normalize(raw_data)
        dotdict = DotDict(data)
        return dotdict

AbstractLangCodeTest.init()
