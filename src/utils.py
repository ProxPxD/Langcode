import operator as op
from copy import copy
from types import NoneType
from typing import Iterable, Callable, Any, AnyStr, Dict, Type, TypeVar, Sequence

from toolz.curried import *

from src.lang_typing import BasicYamlType, YamlType

fjoin = compose = pipeline = compose_left
eq = curry(op.eq)
T = TypeVar('T')
K = TypeVar('K')

is_ = flip(isinstance)
is_dict = is_(dict)
is_list = is_(list)
is_int = is_(int)
is_str = is_(str)
is_sequence = is_(Sequence)

is_basic_yaml_type = is_((str, int, float))
is_complex_yaml_type = is_((dict, list))
is_yaml_type = is_((str, int, float, dict, list))


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


@curry
def map_n(func: Callable, iterable: Iterable, n: int | tuple[int]):
    to_change = to_iter(n)
    return (func(elem) if i in to_change else elem for i, elem in enumerate(iterable))


@curry
def map_nth(n: int, iterable: Iterable):
    return map(nth(n), iterable)


@curry
def mapif(map_func: Callable[[T], Any], cond: Callable[[T], bool], val: T, else_val: Any = NotImplemented) -> Any:
    return map_func(val) if cond(val) else (val if else_val is NotImplemented else else_val)

# TODO: mapifnot with map_args?


def map_arg(*funcs_or_num_funcs, **pos_funcs):
    def handle_positionals(args: list) -> list:
        '''
        Assumes "funcs_or_num_funcs" in form (1, F1, 3, F2, ...) or (F1, F2, None, F4, ...)
        '''
        prev_i = None
        for i, func in enumerate(funcs_or_num_funcs):
            i = prev_i or i
            prev_i = func if is_int(func) else None
            if not is_int(func):
                args[i] = func(args[i]) if func else args[i]
        return args

    def handle_dicts(args: list) -> list:  # TODO: does not work
        '''
        Assumes "pos_funcs" in form: {_0=F1, _1=F2, __1, ...} (not necessarily in order)
        where _ means positive and __ means negative
        '''
        for _i, func in pos_funcs.items():
            sign = 2*int(not _i.startswith('__')) - 1
            num = int(_i.removeprefix('_').removeprefix('_'))
            i = sign * num
            args[i] = func(args[i])
        return args

    def decorator(orig_func):
        def wrapper(*args, **kwargs):
            map_args = fjoin(list, handle_positionals, handle_dicts, tuple)
            new_args = map_args(args)
            return orig_func(*new_args, **kwargs)
        return wrapper
    return decorator


def to_iter(smth) -> Iterable:
    return smth if isinstance(smth, Iterable) and not isinstance(smth, str) else (smth, )


def to_list(smth) -> list:
    return [smth] if isinstance(smth, str | int | float | bool | None) else list(smth)


@curry
def is_instance_of(reduct_func: Callable, _type: Type, iterable: Iterable):
    return reduct_func(map(lambda elem: isinstance(elem, _type), iterable))


is_all_instance_of = is_instance_of(all)
is_any_instance_of = is_instance_of(any)
is_all_instance_of_none = is_all_instance_of(NoneType)


@curry
def is_all_cond_len(cond: Callable[[int], bool], iterable: Iterable):
    return all(map(fjoin(len, cond), iterable))


@curry
def is_all_len_n(n: int, iterable: Iterable):
    return is_all_cond_len(eq(n), iterable)


is_all_len_one = is_all_len_n(1)


def is_list_of_simple_dicts(to_check: list) -> bool:
    return is_all_instance_of(dict, to_check) and is_all_len_one(to_check)


def is_list_of_basics(to_check: list) -> bool:
    return is_all_instance_of(BasicYamlType, to_check)


is_dict_of = curry(lambda reduct_func, _type, iterable: is_instance_of(reduct_func, _type, iterable.values())) #map_arg(_3=dict.values)(is_instance_of)
is_all_dict_of = is_dict_of(all)
is_any_dict_of = is_dict_of(any)
is_all_dict_of_none = is_all_dict_of(NoneType)
is_any_dict_of_none = is_any_dict_of(NoneType)


def map_simple_dicts_to_dict(simple_dict_list: list[dict]) -> dict[str, YamlType]:
    proper_dict = {}
    for simple_dict in simple_dict_list:
        key, val = next(iter(itemmap(tuple, simple_dict).items()))
        if is_dict(val):
            proper_dict.setdefault(key, {}).update(val)
        else:
            proper_dict.setdefault(key, []).extend(to_list(val))
    return proper_dict


def map_conf_list_to_dict(to_map: Sequence[str | Any] | Dict[str, Any]) -> Dict[AnyStr, Any]:
    match to_map:
        case proper_dict if is_dict(proper_dict) and is_all_instance_of(str, proper_dict.keys()):
            return to_map
        case string_list if is_sequence(string_list) and is_all_instance_of(str, string_list):
            return {elem: None for elem in to_map}
        case simple_dict_list if is_sequence(simple_dict_list) and is_list_of_simple_dicts(simple_dict_list):
            return map_simple_dicts_to_dict(simple_dict_list)
        case complex_dict_list if is_sequence(complex_dict_list) and is_all_instance_of(dict, complex_dict_list):  # TODO: should form as default identifier be used?
            return {elem['form']: elem for elem in complex_dict_list}
        case None:
            return {}
        case _:
            raise ValueError


def apply_to_tree(
        elems: list[T],
        apply_func: Callable[[K], Any],
        get_children: Callable[[K], Iterable[T]] = lambda curr: curr.children,
        map_curr: Callable[[T], K] = lambda a: a,
    ) -> None:
    to_applies = list(copy(elems))
    while to_applies:
        curr: T = to_applies.pop()
        mapped = map_curr(curr)
        apply_func(mapped)
        to_applies.extend(get_children(mapped))


def merge_to_flat_dict(to_merge: dict) -> dict[str, list]:  # TODO: validate if the structure is as in features
    flattened = {}
    normalized = map_conf_list_to_dict(to_merge)
    for key, next_layer in normalized.items():
        preprocessed = preprocess_for_merge_to_flat_dict(next_layer)
        if is_all_dict_of_none(preprocessed):
            flattened.setdefault(key, []).extend(preprocessed.keys())
        else:
            for subkey, sublist in merge_to_flat_dict(preprocessed):
                flattened.setdefault(subkey, []).extend(sublist)
    return flattened


def preprocess_for_merge_to_flat_dict(to_preprocess: YamlType) -> dict[BasicYamlType, YamlType]:
    match to_preprocess:
        case dict(): return to_preprocess
        case list(): return map_conf_list_to_dict(to_preprocess)
        case basic if is_basic_yaml_type(basic): return {to_preprocess: None}
        case _: raise ValueError
