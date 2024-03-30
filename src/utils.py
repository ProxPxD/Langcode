import operator as op
from typing import Iterable, Callable, Any, List, AnyStr, Dict, Type, TypeVar

from toolz.curried import *

from src.lang_typing import BasicYamlType

fjoin = compose = pipeline = compose_left
eq = curry(op.eq)
T = TypeVar('T')

is_ = flip(isinstance)
is_dict = is_(dict)
is_list = is_(list)
is_int = is_(int)
is_str = is_(str)


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

    def handle_dicts(args: list) -> list:
        '''
        Assumes "pos_funcs" in form: {_0=F1, _1=F2, __1, ...} (not necessarily in order)
        where _ means positive and __ means negative
        '''
        for _i, func in pos_funcs.items():
            sign = 2*int(not _i.startswith('__')) - 1
            i = sign * int(_i.removeprefix('_').removeprefix('_'))
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


is_dict_of = map_arg(__1=dict.values)(is_instance_of)
is_all_dict_of = is_dict_of(all)
is_any_dict_of = is_dict_of(any)
is_all_dict_of_none = is_all_dict_of(None)
is_any_dict_of_none = is_any_dict_of(None)


def map_conf_list_to_dict(to_map: List[AnyStr | Any] | Dict[AnyStr, Any]) -> Dict[AnyStr, Any]:
    match to_map:
        case d if is_dict(d) and is_all_instance_of(AnyStr, d.keys()):
            return to_map
        case l if is_list(l) and is_all_instance_of(AnyStr, l):
            return {elem: None for elem in to_map}
        case l if is_list(l) and is_all_instance_of(Dict, l):  # TODO: should form as default identifier be used?
            return {elem['form']: elem for elem in to_map}
        case _:
            raise NotImplementedError


def apply_to_tree(elems: list[T], apply_func: Callable, get_children: Callable[[T], Iterable[T]] = lambda curr: curr.children) -> None:
    to_applies = elems[:]
    while to_applies:
        curr: T = to_applies.pop()
        apply_func(curr)
        to_applies.extend(get_children(curr))
