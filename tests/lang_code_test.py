from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, Iterable, Sequence

import yaml
from toolz import valfilter, valmap

from src.data_normalizer import DataNormalizer
from src.dot_dict import DotDict
from src.lang_factory import LangaugeInterpreter, LangFactory
from src.loaders import LangDataLoader
from src.utils import to_list
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

    @classmethod
    def init(cls):
        cls.all_paths = [path for path in Paths.LANGUAGES.iterdir() if path.stem not in cls.not_language_files]
        cls.all_langs = [path.stem for path in cls.all_paths]
        cls.all_data = {lang: cls.data_loader.load(lang) for lang in cls.all_langs}
        cls.all_test_properties: dict[str, DotDict] = {lang: DotDict(data.get('general'), defaults=cls.defaults).test_properties for lang, data in cls.all_data.items()}

    @classmethod
    def get_langs_where(cls, condition: Callable[[DotDict], bool] = lambda _: True) -> Iterable[str]:
        return valfilter(condition, cls.all_test_properties).keys()


AbstractLangCodeTest.init()
