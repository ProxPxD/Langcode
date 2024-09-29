from __future__ import annotations

import re
from typing import Callable, Any

from src.constants import ST
from src.exceptions import NoConditionAppliesException
from src.lang_typing import YamlType


class Condition:
    @classmethod
    def from_conf(cls, source: YamlType) -> MultiCond | Cond:
        match source:
            case dict(): return Cond.from_conf(source)
            case list(): return MultiCond.from_conf(source)
            case _: raise ValueError(f'Condition: source {source} not supported')

    def __init__(self, source):
        self._cond = self.from_conf(source)

    def __call__(self, *args):
        return self._cond(*args)


class MultiCond:
    @classmethod
    def from_conf(cls, source: list):
        return cls(*list(map(Cond.from_conf, source)))

    def __init__(self, *conds: Cond):
        self.conds: list[conds] = list(conds)

    def __call__(self, *args) -> str:
        for cond in self.conds:
            try:
                return cond(*args)
            except NoConditionAppliesException:
                pass
        raise NoConditionAppliesException()


class Cond:
    @classmethod
    def from_conf(cls, source: dict) -> Cond:
        if ST.THEN in source:
            when_source, then_source = source.get('when'), source.get('then')
            when, then = When.from_conf(when_source), Then.from_conf(then_source)
            return cls(when, then)

    def __init__(self, when: When = None, then: Then = None):
        if not then:
            raise ValueError('Cond: then has to be set')
        self.when = when or When()
        self.then = then

    def __call__(self, *args):
        if self.when(*args):
            return self.then(*args)
        raise NoConditionAppliesException()


class When:
    @classmethod
    def from_conf(cls, source: YamlType):
        match source:
            case str(): return cls(re.compile(source).search)
            case _: raise NotImplementedError

    def __init__(self, source: Callable[..., bool | Any] = None):
        self._when: Callable[..., bool] = source or (lambda *args: True)

    def __call__(self, *args):
        return self._when(*args)


class Then:
    @classmethod
    def from_conf(cls, source: YamlType) -> Then:
        match source:
            case str(): return cls(source)
            case dict(): return Cond(source)

    def __init__(self, val: str | Cond):
        self._val = val

    def __call__(self, *args) -> str:
        match self._val:
            case Cond(): return self._val(*args)
            case _: return self._val
