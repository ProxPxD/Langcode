from __future__ import annotations

from typing import Iterable, Sequence, Optional

from src.constants import yaml_type
from src.utils import to_list


class DotDict:
    def __init__(self, d: yaml_type | DotDict, *, defaults: Optional[dict] = None):
        self._curr: yaml_type = d if isinstance(d, yaml_type) else d()
        self._defaults = defaults

    def _get_default(self, item: str, curr_defaults: Optional[dict] = None) -> yaml_type:
        curr_defaults = curr_defaults or self._defaults
        return curr_defaults[item] if curr_defaults is not None else None

    def __getitem__(self, path: str | Sequence[str]) -> DotDict:
        path = to_list(path)
        curr_value, curr_defaults = self._curr, self._defaults
        while path:
            item = path.pop(0)
            curr_defaults = self._get_default(item, curr_defaults)
            curr_value = curr_value.get(item, curr_defaults) if isinstance(curr_value, dict) else None
        return DotDict(curr_value, defaults=curr_defaults)

    def __getattr__(self, path: str | Sequence[str]) -> DotDict:
        return self[path]

    def get(self) -> yaml_type:
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
            is_present = is_present and ((item in curr_value) if isinstance(curr_value, dict) else None)
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