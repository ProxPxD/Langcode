from __future__ import annotations

import pydash as _
from numpy.random.mtrand import Sequence

# Remove string in python 3.14
Categorable = 'Category' | str


class Category:
    def __init__(self, sources: Sequence[Categorable] = None, targets: Sequence[Categorable] = None, **kwargs):
        sources = sources or []
        targets = targets or []

    @classmethod
    def with_targets(cls, *targets: Category, sources: Sequence[Category] = None) -> Category:
        return Category(sources=sources, targets=targets)

    @classmethod
    def with_sources(cls, *sources: Category, targets: Sequence[Category] = None) -> Category:
        return Category(sources=sources, targets=targets)

    def is_(self, *sources: Categorable, targets: Sequence[Category], **kwargs) -> list[Category]:
        targets = _.concat([self], targets)
        self.with_targets(*targets)

    def ex_(self, *targets: Categorable, sources: Sequence[Category], **kwargs) -> list[Category]:
        sources = _.concat([self], sources)
        ...
