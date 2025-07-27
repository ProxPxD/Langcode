from __future__ import annotations

import operator as op
import re
from typing import Any, Callable, overload, Sequence

import pandas as pd
from box import Box
from pandas import Series

from old_src2.utils import to_list

c_: Series = Series(['c'])
h: Series = Series(['h'])
a: Series = Series(['a'])


ch_graphemes: Series = pd.Series.combine(c_, h, op.add)
ch_chars: Series = pd.concat([c_, h])

print(ch_graphemes)
print(ch_chars)
print('-'*42)

cha_graphemes: Series = pd.concat([ch_graphemes, a])
cha_chars_from_chars: Series = pd.concat([c_, h, a])
cha_chars_from_graphemes: Series = Series([g for gs in cha_graphemes for g in gs])


print(cha_graphemes)
print(cha_chars_from_chars)
print(cha_chars_from_graphemes)
print('-'*42)

vec_str = str | Sequence[str]
vec_coherence = 'Coherence' | Sequence['Coherence']


@overload
def ensure_coherence(coh: str | Coherence) -> Coherence: ...
@overload
def ensure_coherence(cohs: Sequence[str | Coherence]) -> list[Coherence]: ...
@overload
def ensure_coherence(*cohs: str | Coherence) -> list[Coherence]: ...

def ensure_coherence(coh: str | Coherence | Sequence[Coherence | str], *cohs: str | Coherence | Sequence[Coherence | str]) -> Coherence | list[Coherence]:
    match coh:
        case None: raise ValueError(f'Cannot map None to Coherence')
        case Coherence(): pass
        case str(): coh = Coherence(coh)
        case seq if isinstance(seq, Sequence): coh = list(map(ensure_coherence, coh))  # pydash fails
        case _: raise ValueError(f'Cannot map {type(coh)} to Coherence')
    return (coh, *ensure_coherence(cohs)) if cohs else coh


class Coherence:  # Coherence Object/Morphism
    _coherences = {}

    def __init__(self, content: Any, *,
            sources: vec_coherence = None,
            targets: vec_coherence = None,
            names: str | Sequence[str] = None,
            name: str | Sequence[str] = None,
            map: Callable[[Any], Any] = None,
            func: Callable[[...], Any] = None,
        ):
        self._map = map
        self.content: Any = self._map(content) if self._map else content
        self.names: list[str] = to_list(name or names or content)
        self.uid: str = self.names[0]  # TODO: work out
        self.sources: Box = Box({source.uid: source for source in to_list(sources or [])})
        self.targets: Box = Box({target.uid: target for target in to_list(targets or [])})
        self.func = func

        self._coherences[self.uid] = self
        # gato is[?root] gato0
        # gato is[?gender] M
        # M ex[gato0] gato
        # gato0 ex[M] gato

    def ex(self, *targets: Coherence, sources: Sequence[Coherence] = None) -> list[Coherence]:
        sources, targets = ensure_coherence(sources or [], targets)
        sources.insert(0, self)
        return [Coherence(target, sources=sources, map=self._map) for target in targets]

    def be(self, *sources: Coherence, targets: Sequence[Coherence] = None) -> list[Coherence]:
        sources, targets = ensure_coherence(sources, targets or [])
        targets.insert(0, self)
        return [Coherence(self._map(source), targets=targets, map=self._map) for source in sources]

    # pushback
    def __mul__(self, other) -> Coherence:
        """
        gato * pl == gatos
        :param other:
        :return:
        """
        ...

    # pullover
    def __add__(self, other) -> Coherence:
        """
        M + F == G
        :param other:
        :return:
        """
        ...

    # ?Remove a case out of collective
    # ?2 is_
    def __sub__(self, other):
        """
        G - N == M + F
        :param other:
        :return:
        """
        ...

    # last near to other
    def __matmul__(self, other):
        """
        gender @ szef == personal_masculine
        :param other:
        :return:
        """
        ...

    # Reapply morpheme
    def __xor__(self, other):
        """
        gatos ^ sg == gato
        same as: (gatos - pl) * sg == gato
        :param other:
        :return:
        """
        ...

    # Get subcoherence
    # Or last near to other
    def __getattr__(self, item):
        """
        gender.personal_masculine == personal_masculine
        szef.gender == personal_masculine
        :param item:
        :return:
        """
        return super().__getattribute__(item)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

Coh = Coherence
C = Coh

grapheme = C('grapheme', map=Series)
grapheme_concat = lambda *args: pd.concat(args)
sz, e, f = grapheme.ex('sz', 'e', 'f')

gender = C('gender')
m, f, n = gender.ex('masculine', 'feminine', 'neutral')
mp, ma, mi = m.ex('masculine_personal', 'masculine_animate', 'masculine_inanimate')


szef_grapheme = C('szef')
# szef_0 = C(source)
# szef = szef_bare * mp
cond = C(p := 'f$', func=re.compile(p).search)
print(cond(szef_grapheme.content))

assert m + f + n == gender
assert m + f != gender

assert szef.gender == mp
assert mp.gender == m
assert m.gender is True

# ???
assert gender.szef == szef  # ???
assert gender.mp == mp
assert gender.m == m


# concat = Arrow(when=True, then=lambda *args: args)
#
# concat = Arrow(lambda a, b: list(a) + list(b))  # Both lists and strings
