from __future__ import annotations

from typing import Iterable, Sequence, Optional, Any, Never, Type

from src.constants import yaml_type
from src.utils import to_list


class DotDictNone(object):
    def __bool__(self):
        return False


class DotDict:
    def __init__(self, d: Any = DotDictNone(), *, defaults: Optional[dict] = DotDictNone(), default_val: Any = DotDictNone()):
        self._curr: yaml_type | Any = d() if isinstance(d, DotDict) else d
        self._defaults = defaults
        self._default_val: Any = default_val

    def _get_default(self, item: str, curr_defaults: Optional[dict] = DotDictNone()) -> Any:
        curr_defaults = curr_defaults or self._defaults
        default = curr_defaults[item] if hasattr(curr_defaults, '__getitem__') else self._default_val
        return default

    def __getitem__(self, path: str | Sequence[str]) -> DotDict:
        path = to_list(path)
        curr_value, curr_defaults = self._curr, self._defaults
        while path:
            item = path.pop(0)
            curr_defaults = self._get_default(item, curr_defaults)
            curr_value = curr_value.get(item, curr_defaults) if isinstance(curr_value, dict) else self._default_val
        return DotDict(curr_value, defaults=curr_defaults)

    def __getattr__(self, path: str | Sequence[str]) -> DotDict:
        return self[path]

    def get(self, default: Any = DotDictNone()) -> Any:
        if isinstance(self._curr, DotDictNone):
            return None if isinstance(default, DotDictNone) else default
        return self._curr

    def __call__(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    def __bool__(self):
        curr = self.get()
        if not isinstance(curr, dict):
            return bool(curr)
        sub_dot_dicts = (DotDict(val, defaults=self._get_default(key), default_val=self._default_val) for key, val in curr.items())
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

    def keys(self) -> Iterable[str | None]:
        match self._curr:
            case dict(): return self._curr.keys()
            case DotDictNone(): return iter(())
            case _: return (None,)

    def values(self):
        match self._curr:
            case dict(): return (DotDict(val, defaults=self._get_default(key)) for key, val in self._curr.items())
            case DotDictNone(): return iter(())
            case _: (DotDict(self._curr), )

    def items(self):
        yield from zip(self.keys(), self.values())

    def __str__(self):
        return f'{self.__class__.__name__}({self._curr.__str__()})'

    def __repr__(self):
        return f'{self.__class__.__name__}({self._curr.__repr__()})'

    def is_(self, atype: Type | None) -> bool:
        if atype is None:
            return self._curr is None
        return isinstance(self._curr, atype)

    def is_dict(self) -> bool:
        return self.is_(dict)

    def is_none(self) -> bool:
        return self.is_(None)

    def is_list(self) -> bool:
        return self.is_(list)

    def is_int(self) -> bool:
        return self.is_(int)

    def is_bool(self) -> bool:
        return self.is_(bool)
