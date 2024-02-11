from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, Iterable

import yaml
from toolz import valfilter

from src.loaders import LangDataLoader
from tests.abstractTest import AbstractTest

yaml_types = dict | bool | str | int | None


@dataclass
class Paths:
    LANGUAGES = Path(__file__).parent / 'languages'
    DEFAULTS = LANGUAGES / 'general_defaults.yaml'


class DotDict:
    _orig_defaults = yaml.safe_load(open(Paths.DEFAULTS, 'r'))

    def __init__(self, d: yaml_types | DotDict, *, defaults: Optional[dict] = None):
        self._curr: dict = d if isinstance(d, yaml_types) else d()
        self._defaults = defaults if defaults is not None else self._orig_defaults

    def __getattr__(self, item: str) -> DotDict:
        default = self._defaults[item]
        value = self._curr.get(item, default) if isinstance(self._curr, dict) else False
        return DotDict(value, defaults=default)

    def get(self) -> yaml_types:
        return self._curr

    def __call__(self):
        return self.get()

    def __bool__(self):
        return self.get()


class AbstractLangCodeTest(AbstractTest):
    accepted_similarity = .5

    data_loader = LangDataLoader(Paths.LANGUAGES)

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
        cls.all_test_properties = {lang: DotDict(data.get('general')).test_properties for lang, data in cls.all_data.items()}

    @classmethod
    def get_langs_where(cls, condition: Callable[[DotDict], bool] = lambda _: True) -> Iterable[str]:
        return valfilter(condition, cls.all_test_properties).keys()


AbstractLangCodeTest.init()
