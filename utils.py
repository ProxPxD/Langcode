import operator as op
from typing import Iterable

from parsimonious.nodes import Node


def clean_empty(iterable: Iterable):
    return filter(lambda e: bool(e.text) if isinstance(e, Node) else op.truth(e), iterable)


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