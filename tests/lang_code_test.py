from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, Iterable, Sequence

import yaml
from toolz import valfilter, valmap

from src.loaders import LangDataLoader
from src.utils import to_list
from tests.abstractTest import AbstractTest

yaml_types = dict | bool | str | int | None


@dataclass
class Paths:
    LANGUAGES = Path(__file__).parent / 'languages'
    DEFAULTS = LANGUAGES / 'general_defaults.yaml'


class DotDict:
    orig_defaults = yaml.safe_load(open(Paths.DEFAULTS, 'r'))

    def __init__(self, d: yaml_types | DotDict, *, defaults: Optional[dict] = None):
        self._curr: yaml_types = d if isinstance(d, yaml_types) else d()
        self._defaults = defaults if defaults is not None else self.orig_defaults

    def __getitem__(self, path: str | Sequence[str]) -> DotDict:
        path = to_list(path)
        curr_value, curr_defaults = self._curr, self._defaults
        while path:
            item = path.pop(0)
            curr_value = curr_value.get(item, curr_defaults) if isinstance(curr_value, dict) else False
        return DotDict(curr_value, defaults=curr_defaults)

    def __getattr__(self, path: str | Sequence[str]) -> DotDict:
        return self[path]

    def get(self) -> yaml_types:
        return self._curr

    def __call__(self):
        return self.get()

    def __bool__(self):
        curr = self.get()
        if not isinstance(curr, dict):
            return bool(curr)
        sub_dot_dicts = (DotDict(val, defaults=self._defaults[key]) for key, val in curr.items())
        return any(map(bool, sub_dot_dicts))

    def __contains__(self, path: str | Sequence[str]):
        path = to_list(path)
        is_present = True
        curr_value = self._curr
        while path:
            item = path.pop(0)
            is_present = is_present and ((item in curr_value) if isinstance(curr_value, dict) else False)
            curr_value = curr_value.get(item)
        return is_present

    def keys(self) -> Iterable[str]:
        yield from self._curr.keys() if isinstance(self._curr, dict) else (None, )

    def values(self):
        yield from self._curr.values() if isinstance(self._curr, dict) else (self._curr, )

    def items(self):
        yield from zip(self.keys(), self.values())

    def __str__(self):
        return f'{self.__class__.__name__}({self._curr})'


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
        cls.all_test_properties: dict[str, DotDict] = {lang: DotDict(data.get('general')).test_properties for lang, data in cls.all_data.items()}

    @classmethod
    def get_langs_where(cls, condition: Callable[[DotDict], bool] = lambda _: True) -> Iterable[str]:
        return valfilter(condition, cls.all_test_properties).keys()


AbstractLangCodeTest.init()
