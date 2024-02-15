from typing import Iterable, Callable, Any, Collection, Tuple

from toolz import curry

from src.constants import basic_yaml_type


def get_name(instance):
    return instance.name if 'name' in instance.__dir__ else instance['name'] if '__contains__' in instance.__dir__ and 'name' in instance else instance if isinstance(instance, str) else None


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
    def dict(cls) -> dict:
        return {key: item for key, item in cls.__dict__.items() if not key.startswith('_') and not isinstance(item, Callable)}

    values: Callable[[], Any] = lambda self: self.dict().values()
    keys: Callable[[], Any] = lambda self: self.dict().keys()

    @classmethod
    def items(cls):
        return cls.dict().items()


def word_to_basics(word: str, basics: Collection[str], skip_missing=False, yield_index=False, start_from_one=False) -> Collection[str | Tuple[str, int] | None]:
    basics = sorted(basics, reverse=True)
    index = 1 if start_from_one else 0
    missing = ''
    while word:
        first = word[0]
        starting = next(filter(lambda b: b.startswith(first), basics), None)
        if starting is None:
            missing += first
            word = word[1:]
        else:
            if missing:
                if not skip_missing:
                    if yield_index:
                        yield missing, index
                    else:
                        yield missing
                index += len(missing)
                missing = ''
            if yield_index:
                yield starting, index
                index += len(starting)
            else:
                yield starting
            word = word[len(starting):]

    if missing and not skip_missing:
        if yield_index:
            yield missing, index
        else:
            yield missing


def get_extreme_points(col: list | str, midpoint: int, remove_range: int, right_remove_range: int = None) -> tuple[int, int]:
    left_range = remove_range
    right_range = right_remove_range if right_remove_range is not None else remove_range
    min_point = max(midpoint-left_range, 0)
    max_point = min(midpoint+right_range+1, len(col))
    return min_point, max_point


def to_list(smth) -> list:
    return [smth] if isinstance(smth, str) else list(smth)


@curry
def is_instance_of(reduct_func, atype, iterable: Iterable):
    return reduct_func(map(lambda elem: isinstance(elem, atype), iterable))


is_all_instance_of = is_instance_of(all)
is_any_instance_of = is_instance_of(any)


@curry
def is_all_len_n(n: int, iterable: Iterable):
    return all(map(lambda elem: len(elem) == n, iterable))


is_all_len_one = is_all_len_n(1)


def is_list_of_dicts(to_check: list) -> bool:
    return is_all_instance_of(dict, to_check) and is_all_len_one(to_check)


def is_list_of_basics(to_check: list) -> bool:
    return is_all_instance_of(basic_yaml_type, to_check)