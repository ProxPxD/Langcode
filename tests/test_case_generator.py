
from typing import Iterable, Sequence, Callable

import pydash
import pytest
from _pytest.mark import MarkDecorator, ParameterSet
from pydash import chain as c

from src.utils import fjoin, is_not


class TCG:
    """
    TCG - Test Case Generator
    """
    tcs = []

    @classmethod
    def generate_tcs(cls) -> list:
        return cls.tcs

    @classmethod
    def map(cls, tc) -> tuple:
        return tc

    @classmethod
    def to_simpler_tcs(cls, tc) -> Iterable | list:
        return [tc]

    @classmethod
    def gather_tags(cls, tc) -> Iterable[str] | Sequence[str]:
        return []

    @classmethod
    def param_names(cls) -> list[str] | str:
        raise ValueError()  # TODO: replace exception

    ###############
    # Undefinable #
    ###############

    @classmethod
    def _generate_marks(cls, tags: Iterable[str] | Sequence[str]) -> list[MarkDecorator]:
        return [getattr(pytest.mark, tag) for tag in tags]

    @classmethod
    def _as_paramset(cls, tc) -> ParameterSet:
        tags = cls.gather_tags(tc)
        marks = cls._generate_marks(tags)
        tc = cls.map(tc)
        values = (tc, ) if hasattr(tc, '_asdict') or is_not(tuple, tc) else tc
        return pytest.param(*values, marks=marks)

    @classmethod
    def generate(cls) -> list[ParameterSet]:
        return (c(cls.generate_tcs())
                .map(cls.to_simpler_tcs)
                .flatten()
                .map(cls._as_paramset)
                .value())

    @classmethod
    def list(cls) -> list[tuple]:
        return list(cls.generate())

    @classmethod
    def parametrize(cls, param_names=None, name_from: str | int | Sequence[str|int] = None, ids=None, **kwargs):
        if ids is None:
            name_from = (name_from, ) if isinstance(name_from, (str | int)) else name_from or ('name', 'short', 'descr')
            ids = lambda tc: c().at(*name_from).filter(bool).concat(tc).head()(tc)
        param_names = param_names or cls.param_names()
        params = cls.list()
        return pytest.mark.parametrize(param_names, params, ids=ids, **kwargs)
