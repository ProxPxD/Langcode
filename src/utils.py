from __future__ import annotations

import re
from copy import copy, deepcopy
from operator import *
from types import NoneType
from typing import Iterable, Callable, Any, AnyStr, Dict, Type, TypeVar, Sequence

import pydash as _
from pydash import flow, chain as c
from toolz.curried import *
from toolz.curried.operator import *

from src.lang_typing import BasicYamlType, YamlType

fjoin = compose = pipeline = compose_left
revarg = curry(lambda *args, **kwargs: lambda f: f(*args, **kwargs))


class Empty(object):
    pass


T = TypeVar('T')
K = TypeVar('K')
G = TypeVar('G')

vec_seq = Sequence[T] | T

is_ = curry(flip(isinstance))  # overrrides operator
is_not = curry(_.negate(is_))
is_empty = is_(Empty)
is_dict = is_(dict)
is_list = is_(list)
is_int = is_(int)
is_str = is_(str)
is_sequence = is_(Sequence)

is_many = curry(lambda reduc, type_, elems: reduc(map(is_(type_), elems)))
is_all = is_many(all)
is_any = is_many(any)

is_basic_yaml_type = is_((str, int, float))
is_complex_yaml_type = is_((dict, list))
is_yaml_type = is_((str, int, float, dict, list))
to_unary_func = lambda to_map: to_map if is_(Callable, to_map) else lambda whatever: to_map


class if_:
    '''
        # if_(elems).then_(any, all)
        # if_(elems).then(any).else_(all)
        # if_(func).then(func).elif_(elems).then_(any, all)
        # if_(func).elif_(elems).then_(any, all)
    '''

    class _IfNone(object):
        pass

    def __init__(self, arg: T, cond: Callable[[T], bool] | None = bool):
        self._arg = arg
        self._cond = cond if cond is not None else lambda x: x is None
        self.apply = self.then_apply

    def _meets(self):
        return self._cond(self._arg)

    def _proper_false(self, false: Any) -> T | Any:
        return self._arg if is_(if_._IfNone, false) else false

    def then_(self, true: K, false: G = _IfNone()) -> T | K | G:
        false = self._proper_false(false)
        return true if self._meets() else false

    def then(self, true: K) -> if_:
        return self.then_(if_(true, _.negate(self._cond)), self)

    def else_(self, false: G) -> T | G:
        return self.then_(self._arg, false)

    def raise_(self, to_raise: Exception) -> None:
        if self._meets():
            raise to_raise

    def then_apply(self, true: Callable[[T], K], false: Callable[[T], G] = _IfNone(), *, default: Any = _IfNone()) -> T | K | G:
        if flow(all, map(is_not(if_._IfNone))(false, default)):
            raise ValueError('false and default cannot be set together')

        false = self._proper_false(if_(default).is_not(if_._IfNone).then(false))
        transform = to_unary_func(self.then_(true, false))
        return transform(self._arg)

    def else_apply(self, false: Callable[[T], G]):
        return self.then_apply(self._arg, false)

    def is_(self, _type: Type) -> if_:
        self._cond = is_(_type)
        return self

    def is_not(self, _type: Type) -> if_:
        self._cond = is_not(_type)
        return self

    def elif_(self, arg: T, cond: Callable[[T], bool] = bool):
        return self.then_(if_(self._arg, cond=self._cond), if_(arg, cond=cond))


def adjust_str(old: str, new: str = ''):
    return lambda f: lambda *args, **kwargs: f(*args, **kwargs).replace(old, new)


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


class DictClass:  # TODO - base on already implemented probably
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
def map_nths(func: Callable, iterable: Iterable, n: int | tuple[int]):
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


def get_to_sequence(method, _type: T = None, is_type=None) -> Callable[[Any], T]:
    if _type and is_type:
        raise ValueError
    is_type = if_(is_type).elif_(_type).then(is_(_type)).else_(is_(method))

    def _map(to_map) -> T:
        match to_map:
            case _ if is_str(to_map): return method((to_map,))
            case _ if is_type(to_map): return to_map
            case _: return method(to_map)
    return _map


to_iter = get_to_sequence(tuple, Iterable)
to_list = get_to_sequence(list)
to_tuple = get_to_sequence(tuple)

is_all_instance_of = is_many(all)  # think of renaming to is_all
is_any_instance_of = is_many(any)
is_all_instance_of_none = is_all_instance_of(NoneType)


@curry
def is_cond_len(reduc: Callable[[Iterable], bool], cond: Callable[[int], bool], iterable: Iterable):
    return reduc(map(flow(len, cond), iterable))


is_all_cond_len = is_cond_len(all)
is_any_cond_len = is_cond_len(any)


@curry
def is_all_len_n(n: int, iterable: Iterable):
    return is_all_cond_len(eq(n), iterable)


is_len_n = curry(lambda n, iterable: eq(n, len(iterable)))
is_list_of_simple_dicts = _.conjoin(is_dict, is_len_n(1))

is_list_of_basics = is_many(BasicYamlType)


is_dict_of = curry(lambda reduct_func, _type, iterable: is_many(reduct_func, _type, iterable.values())) #map_arg(_3=dict.values)(is_instance_of)
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


compile_regexes = c().map_(re.compile)
compile_regexes_to_funcs = compile_regexes.pluck('search')
join_regexes_to_juxt = flow(compile_regexes_to_funcs, _.spread(_.juxtapose))
is_matching = curry(lambda reduc, regexes, elems: c().apply(join_regexes_to_juxt).flow(reduc)(regexes)(elems))
# is_matching = curry(c().apply(join_regexes_to_juxt).flow)  # Unfortunately, lambda is necessary to avoid calling all args separately

# compile_regexes_to_funcs = flow(compile_regexes, _.map(_.property_('search')))
# join_regexes_to_juxt = c().apply(compile_regexes_to_funcs).apply(_.spread(_.juxtapose))
# is_matching = curry(lambda reduc, regexes: flow(join_regexes_to_juxt(regexes), reduc))


def exceptions_to_bool(*, true: vec_seq = tuple(), false: vec_seq = tuple(), other: bool | None = Empty(), if_none: bool | None = Empty(), exceptions_to_false: bool = None, flow_to_bool: bool = None):
    switch_if_empty = lambda val, else_: else_ if is_empty(val) else val

    if exceptions_to_false is not None and flow_to_bool is not None:
        raise ValueError(f'"{exceptions_to_false.__name__}" and "{flow_to_bool.__name__}" cannot be set together')
    elif exceptions_to_false is not None:
        false = Exception
        if_none = None
        other = switch_if_empty(other, False)
    elif flow_to_bool is not None:
        false = Exception
        if_none = True
        other = switch_if_empty(other, False)
    elif not true and not false:
        false = Exception
        if_none = switch_if_empty(if_none, True)
        other = switch_if_empty(other, False)
    elif true and false:
        if_none = switch_if_empty(if_none, None)
        other = switch_if_empty(other, None)
    elif false:
        if_none = switch_if_empty(if_none, True)
        other = switch_if_empty(other, None)
    elif true:
        if_none = switch_if_empty(if_none, False)
        other = switch_if_empty(other, False)
    else:
        raise ValueError

    true, false = c().map_(to_tuple)((true, false))

    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
            except true:
                return True
            except false:
                return False
            except Exception:
                if other is None:
                    raise
                return other
            if if_none is None:
                return result
            return if_none
        return wrapper
    return decorator