from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from typing import Literal, TypeVar, Generic, Callable, Iterable, Tuple

import numpy as np

from morphemes.utils import get_name


Coord = int | tuple[int, ...]
Size = Coord
Step = str | tuple[str, ...]
Position = Literal[-1, 0, 1]
MU = TypeVar('MU')  # Morpheme Unit


# TODO THINK: D dir class from py2neo lib?
@dataclass(frozen=True)
class By:
    LETTERS = 'LETTERS'
    L = LETTERS
    CONSONANTS = 'CONSONANTS'
    C = CONSONANTS
    VOWELS = 'VOWELS'
    V = VOWELS
    SEMIVOWELS = 'SEMIVOWELS'
    SV = SEMIVOWELS


@dataclass(frozen=True)
class Side:
    BEFORE: Position = -1
    AFTER: Position = 1
    AT: Position = 0


class MetaLanguages(type):
    _languages: dict = {}
    _current: Language | None = None

    def __getitem__(cls, lang: str | Language) -> Language:
        return cls._languages[get_name(lang)]

    def __setitem__(cls, name: str, lang: Language):
        if isinstance(lang, Language):
            cls._languages[name] = lang
            cls._current = lang
        else:
            raise NotImplementedError

    def __contains__(self, name):
        return name in self._languages

    def keys(cls):
        return cls._languages.keys()

    def values(cls):
        return cls._languages.values()

    def items(cls):
        return cls._languages.items()

    @property
    def current(cls) -> Language | None:
        return cls._current

    @current.setter
    def current(cls, new_current: Language | str | None) -> None:  # TODO test setting ways
        name = get_name(new_current)
        if new_current is None or name in cls._languages:
            cls._current = cls._languages[name]
        else:
            raise NotImplementedError  # TODO test error

    def associate(cls, to_associate: Iterable | object) -> Language:  # TODO add annotation
        if cls._current is not None:
            return cls._current.associate(to_associate)


class languages(metaclass=MetaLanguages):  # TODO test access
    pass


class Language(Generic[MU]):

    def __init__(self):
        self.step_members = {
            By.LETTERS: 'abcdefghijklmnopqrstuvwxyz',
            By.CONSONANTS: 'bcdfghjklmnpqrstvwxz',
            By.VOWELS: 'aeioy',
            By.SEMIVOWELS: 'wj',
        }

    def get_step_members(self, by: Step) -> tuple[MU, ...]:
        return self.step_members[by]

    def associate(self, to_associate: Iterable | object) -> Language:  # TODO add annotation
        if not isinstance(to_associate, Iterable):
            return self._associate_single(to_associate)
        else:
            return reduce(lambda a, b: a, map(self.associate, to_associate))

    def _associate_single(self, to_associate) -> Language:  # TODO add annotation
        raise NotImplementedError
        return self


# TODO think: How to implement conditional src, pos: within the class, separately
class Morpheme(Generic[MU]):
    default: MU = ''
    first: Coord = 1
    last: Coord = -1
    before = Side.BEFORE
    after = Side.AFTER

    def __init__(self, form: MU = None, at: Coord = 0, by: Step = By.LETTERS, side: Position = Side.BEFORE):
        self.language = languages.associate(self)
        self.form: MU = form if form is not None else self._get_default()
        self.at: int = at
        self.by: str = by
        self.side: int = side

    def _inverse_problem(self, problem: Callable, word: MU):
        reverse_result = problem(~self, word[::-1])
        return reverse_result[::-1]

    @classmethod
    def _get_default(cls) -> MU:
        return cls.default

    def apply_to(self, word: MU, *args, **kwargs) -> Coord:
        if self.at < 0:
            return self._inverse_problem(self.apply_to, word)
        place, size = self._get_place_and_size(word)
        result = self._apply_at_place(word, place, size)
        return result

    def _apply_at_place(self, word: MU, place: Coord, size: Size = 1, side=None) -> MU:  # TODO think: Generalize to more dimensions rather than strings
        side = side if side is not None else self.side
        match side:
            case Side.BEFORE: return word[:place] + self.form + word[place:]
            case Side.AT: return word[:place] + self.form + word[place+size:]  # TODO think: or size?
            case Side.AFTER: return self._apply_at_place(word, place+size, Side.BEFORE)  # TODO think: or size?

    # TODO think: returning the size of the place
    def _get_place_and_size(self, word: MU) -> Tuple[Coord, Size]:
        step_members = self.language.step_members[self.by]
        place_sizes = [(i, 1) for i, unit in enumerate(word) if unit in step_members] if self.by != By.LETTERS else list(range(len(word)))  # TODO think: better size handling
        place, size = place_sizes[self.at]
        return place, size

    def __call__(self, word, *args, **kwargs):
        return self.apply_to(word, *args, **kwargs)

    def __invert__(self) -> Morpheme:
        return Morpheme(self.form[::-1], at=np.subtract(0, self.at), by=self.by, side=np.subtract(0, self.side))

    def __add__(self, other: Morpheme):
        if self.language != other.language:
            raise ArithmeticError
        return ComplexMorpheme(self, other)


class ComplexMorpheme(Morpheme):
    def __init__(self, *morphemes: Morpheme):
        super().__init__()
        self.morphemes: Tuple[Morpheme] = morphemes

    def apply_to(self, word: MU, *args, **kwargs) -> Coord:
        return reduce(lambda w, morph: morph(w), self.morphemes, word)

    def __invert__(self):
        return ComplexMorpheme(*tuple(map(Morpheme.__invert__, self.morphemes)))


class Prefix(Morpheme):
    def __init__(self, form: MU):
        super().__init__(form, at=self.first, by=By.LETTERS, side=self.before)


class Postfix(Morpheme):
    def __init__(self, form: MU):
        super().__init__(form, at=self.last, by=By.LETTERS, side=self.after)


class Suffix(Postfix):
    pass


class Circumfix(ComplexMorpheme):
    def __init__(self, pre: MU, post: MU):
        super().__init__(Prefix(pre), Postfix(post))
