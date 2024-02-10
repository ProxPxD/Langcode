from __future__ import annotations

from dataclasses import field, dataclass
from pathlib import Path
from typing import Optional

import yaml

from tests.abstractTest import AbstractTest

yaml_types = dict | bool | str | int


class Paths:
    LANGUAGES = Path(__file__).parent / 'languages'
    DEFAULTS = LANGUAGES / 'general_defaults.yaml'


class DotDict:
    _orig_defaults = yaml.safe_load(open(Paths.DEFAULTS, 'r'))

    def __init__(self, d: yaml_types, *, defaults: Optional[dict] = None):
        self._curr: dict = d
        self._defaults = defaults if defaults is None else self._orig_defaults

    def __getattr__(self, item: str) -> DotDict:
        default = self._defaults[item]
        value = self._curr.get(item, default) if isinstance(self._curr, dict) else False
        return DotDict(value, defaults=default)

    def get(self) -> yaml_types:
        return self._curr

    def __call__(self):
        return self.get()


class AbstractLangCodeTest(AbstractTest):
    accepted_similarity = .5
