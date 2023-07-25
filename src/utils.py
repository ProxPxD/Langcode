from dataclasses import asdict
from typing import Iterable, Callable, Any


def get_name(instance):
    return instance.name if 'name' in instance.__dir__ else instance if isinstance(instance, str) else None


def reapply(fn, arg, n=None, until=None, as_long=None):
    if sum([arg is None for arg in (n, until, as_long)]) < 2:
        raise ValueError
    cond = (lambda a: n > 0) if n is not None else (lambda a: not until(a)) if until is not None else as_long if as_long is not None else (lambda a: False)
    if isinstance(arg, Iterable) and not isinstance(arg, str):
        arg = list(arg)
    while cond(arg):
        arg = fn(arg)
    return arg


to_last_list = lambda elem: reapply(lambda c: c[0], elem, as_long=lambda c: isinstance(c, list) and len(c) == 1 and isinstance(c[0], list))


class DictClass:
    def __getitem__(self, item):
        return self.__dict__[item]

    def __setitem__(self, key, value):
        return self.__dict__.__setitem__(key, value)

    @classmethod
    def _dict(cls) -> dict:
        return asdict(cls())
    dict: Callable[[], dict] = lambda: DictClass._dict()
    values: Callable[[], Any] = lambda self: self.dict().values()
    keys: Callable[[], Any] = lambda self: self.dict().keys()
    items: Callable[[], Any] = lambda self: self.dict().items()

    @classmethod
    def map_to_contained_key(cls, k) -> str | None:
        return next(filter(k.__contains__, cls().keys()), None)