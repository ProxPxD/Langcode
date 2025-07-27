from __future__ import annotations

from typing import Union

import pydash as _
from numpy.random.mtrand import Sequence

# Remove string in python 3.14
Categorable = Union[str, 'Category']


class Category:
    def __init__(self, sources: Sequence[Categorable] = None, targets: Sequence[Categorable] = None, **kwargs):
        sources = sources or []
        targets = targets or []
        self._props = dict(kwargs)

    @classmethod
    def with_targets(cls, *targets: Category, sources: Sequence[Category] = None) -> Category:
        return Category(sources=sources, targets=targets)

    @classmethod
    def with_sources(cls, *sources: Category, targets: Sequence[Category] = None) -> Category:
        return Category(sources=sources, targets=targets)

    def is_(self, *sources: Categorable, targets: Sequence[Category], **kwargs) -> list[Category]:
        targets = _.concat([self], targets)
        self.with_targets(*targets)
        return ...

    def ex_(self, *targets: Categorable, sources: Sequence[Category], **kwargs) -> list[Category]:
        sources = _.concat([self], sources)
        return ...

    def __getattr__(self, item):
        if item in self._props:
            return self._props[item]
        return super().__getattribute__(item)


c = Category(a=1)
c.b = 2
print(c.a)
print(c.b)

