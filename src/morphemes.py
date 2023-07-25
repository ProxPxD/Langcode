from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from functools import reduce
from typing import Literal, TypeVar, Generic, Callable, Iterable, Tuple, Any, List

import numpy as np

from src.utils import DictClass, get_name

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


@dataclass(frozen=True)
class C:
    FORM = 'form'
    AT = 'at'
    BY = 'by'
    SIDE = 'side'


@dataclass(frozen=True)
class StrDefaults(DictClass):
    form: str = ''
    at = 0
    by = By.LETTERS
    side = Side.BEFORE

    first: Coord = 1
    last: Coord = -1

    before = Side.BEFORE
    after = Side.AFTER


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


class AbstractMorpheme(Generic[MU]):

    def __init__(self, **kwargs):
        self.language = languages.associate(self)
        super().__init__(**kwargs)

    def _inverse_problem(self, problem: Callable, word: MU):
        reverse_result = problem(~self, word[::-1])
        return reverse_result[::-1]

    @classmethod
    def _get_default(cls, name: str) -> MU | Any:
        return StrDefaults.dict()[name]

    @abstractmethod
    def _get_place_and_size(self, word: MU) -> Tuple[Coord, Size]:
        raise NotImplementedError

    @abstractmethod
    def _get_word_parts(self, word: MU, place: Coord, size: Size = 1, side=None) -> Tuple[MU, ...]:  # TODO think: Generalize to more dimensions rather than strings
        raise NotImplementedError

    @abstractmethod
    def is_present(self, word: MU, *args, **kwargs) -> MU:
        raise NotImplementedError

    @abstractmethod
    def is_applicable(self, word: MU, *args, **kwargs) -> MU:
        raise NotImplementedError

    @abstractmethod
    def insert(self, word: MU, *args, **kwargs) -> MU:
        raise NotImplementedError

    @abstractmethod
    def remove(self, word: MU, *args, **kwargs) -> MU:
        raise NotImplementedError

    @abstractmethod
    def replace(self, word: MU, *args, **kwargs) -> MU:
        raise NotImplementedError

    def __call__(self, word, *args, **kwargs):
        raise NotImplementedError
        # TODO switch between insert, remove, replace methods
        return self.insert(word, *args, **kwargs)

    @abstractmethod
    def __invert__(self) -> SingleMorpheme:
        raise NotImplementedError

    @abstractmethod
    def __add__(self, other: SingleMorpheme):
        raise NotImplementedError


# TODO think: How to implement conditional src, pos: within the class, separately
class SingleMorpheme(AbstractMorpheme):

    def __init__(self, form1: MU = None, form2: MU = None, *, at: Coord = None, by: Step = None, side: Position = None, **kwargs):
        super().__init__(**kwargs)
        # self.form: MU = form1 if form1 is not None else form2 if form2 is not None else self._get_default(C.FORM)
        self.to_remove: MU = form1 if form2 is not None else self._get_default(C.FORM)
        self.to_insert: MU = form2 if form2 is not None else self._get_default(C.FORM)
        self.at: Coord = at if at is not None else self._get_default(C.AT)
        self.by: Step = by if by is not None else self._get_default(C.BY)
        self.side: Position = side if side is not None else self._get_default(C.SIDE)

    @property
    def form(self) -> MU:
        is_to_remove = bool(self.to_remove)
        is_to_add = bool(self.to_insert)
        if is_to_remove and is_to_add:
            return f'{self.to_remove}>{self.to_insert}'
        elif is_to_add:
            return f'+{self.to_insert}+'
        elif is_to_remove:
            return f'-{self.to_insert}-'
        else:  # TODO think: how to represent no form
            return None

    # TODO think: returning the size of the place
    def _get_place_and_size(self, word: MU) -> Tuple[Coord, Size]:
        step_members = self.language.step_members[self.by]
        place_sizes = [(i, 1) for i, unit in enumerate(word) if unit in step_members] if self.by != By.LETTERS else list(range(len(word)))  # TODO think: better size handling
        place, size = place_sizes[self.at]
        return place, size

    def _get_word_parts(self, word: MU, place: Coord, size: Size = 1, side=None) -> Tuple[MU, ...]:
        side = side if side is not None else self.side
        match side:
            case Side.BEFORE: return word[:place], word[place:]
            case Side.AT: return word[:place], word[place+size:]  # TODO think: or size?
            case Side.AFTER: return self._get_word_parts(word, place + size, Side.BEFORE)  # TODO think: or size?

    def is_applicable(self, word: MU, *args, **kwargs) -> MU:
        if self.at < 0:
            return self._inverse_problem(self.insert, word)
        place, size = self._get_place_and_size(word)
        # TODO move this to abstract after generalizing "len" (size_of) and "[]" (slice_of?)"
        return len(word) < place + size and (not self.to_remove or word[place: place+size] == self.to_remove)

    def is_present(self, word: MU, *args, **kwargs) -> MU:
        if self.at < 0:
            return self._inverse_problem(self.insert, word)
        place, size = self._get_place_and_size(word)
        # TODO move this to abstract after generalizing "[]"
        return word[place: place+size] == (self.to_remove if self.to_remove else self.to_insert)

    def insert(self, word: MU, *args, **kwargs) -> MU:
        # TODO move this to abstract after generalizing num of parts and it's concatanation with form
        if self.at < 0:
            return self._inverse_problem(self.insert, word)
        place, size = self._get_place_and_size(word)
        part1, part2 = self._get_word_parts(word, place)
        result = part1 + self.to_insert + part2
        return result

    def remove(self, word: MU, *args, **kwargs) -> MU:
        # TODO move this to abstract after generalizing num of parts and it's concatanation with form
        if self.at < 0:
            return self._inverse_problem(self.insert, word)
        place, size = self._get_place_and_size(word)
        if not self.is_applicable(word):
            raise ValueError  # TODO specify
        part1, part2 = self._get_word_parts(word, place)
        return part1 + part2

    def replace(self, word: MU, *args, **kwargs) -> MU:
        # TODO move this to abstract after generalizing "negativity of at, inversing problem according to specific axis""
        if self.at < 0:
            return self._inverse_problem(self.insert, word)
        word = self.remove(word)
        word = self.insert(word)
        return word

    def __invert__(self) -> SingleMorpheme:
        return SingleMorpheme(self.form[::-1], at=np.subtract(0, self.at), by=self.by, side=np.subtract(0, self.side))

    def __add__(self, other: SingleMorpheme):
        if self.language != other.language:
            raise ArithmeticError
        return ComplexMorpheme(self, other)


class ComplexMorpheme(AbstractMorpheme):
    def __init__(self, *morphemes: AbstractMorpheme, **kwargs):
        super().__init__(**kwargs)
        self.morphemes: List[AbstractMorpheme] = [m for morph in morphemes for m in (morph.morphemes if isinstance(morph, ComplexMorpheme) else [morph])]

    def insert(self, word: MU, *args, **kwargs) -> MU:
        return reduce(lambda w, morph: morph.insert, self.morphemes, word)

    def remove(self, word: MU, *args, **kwargs) -> MU:
        return reduce(lambda w, morph: morph.remove, self.morphemes, word)

    def replace(self, word: MU, *args, **kwargs) -> MU:
        return reduce(lambda w, morph: morph.replace, self.morphemes, word)

    def __invert__(self):
        return ComplexMorpheme(*tuple(map(AbstractMorpheme.__invert__, self.morphemes)))


class ConditionalMorpheme(AbstractMorpheme):
    def __init__(self, cond: Callable[[MU], bool] | SingleMorpheme, positive: ComplexMorpheme | SingleMorpheme, negative: ComplexMorpheme | SingleMorpheme | str = None, **kwargs):
        super().__init__(**kwargs)
        # TODO think: if condition should be callable or morpheme
        # if morpheme, then should it be specified if used existing or not existing?
        # if callable, then simply negate the condition?
        # Can be both?
        self.cond: SingleMorpheme | Callable[[MU], bool] = cond
        self.positive: ComplexMorpheme | SingleMorpheme = positive
        self.negative: ComplexMorpheme | SingleMorpheme = negative if isinstance(negative, (SingleMorpheme, ComplexMorpheme)) else SingleMorpheme(negative if negative is not None else self.default, positive.at, positive.by, positive.side)

    def insert(self, word: MU, *args, **kwargs) -> MU:
        return self.positive(word) if self.cond(word) else self.negative(word)

    def __invert__(self):
        return Morpheme(~self.cond, ~self.positive, ~self.negative)


class Morpheme(SingleMorpheme, ComplexMorpheme, ConditionalMorpheme):
    def __init__(self,
            *form: Morpheme | MU,
            at: Coord = None, by: Step = None, side: Position = None,
            cond: Callable[[MU], bool] | SingleMorpheme = None, positive: SingleMorpheme = None, negative: SingleMorpheme | str = None,
            **kwargs):
        single_form = form[0] if len(form) == 1 else None
        morphemes = tuple() if len(form) < 2 else tuple(map(lambda f: f if isinstance(f, Morpheme) else Morpheme(f, at=at, by=by, side=side), form))
        super(SingleMorpheme).__init__(single_form, at=at, by=by, side=side)
        super(ComplexMorpheme).__init__(*morphemes)
        super(ConditionalMorpheme).__init__(cond=cond, positive=positive, negative=negative)

#############
# Templates #
#############
# TODO: think of making them functions returning classes

class Prefix(SingleMorpheme):
    def __init__(self, form: MU):
        super().__init__(form, at=self.first, by=By.LETTERS, side=self.before)


class Postfix(SingleMorpheme):
    def __init__(self, form: MU):
        super().__init__(form, at=self.last, by=By.LETTERS, side=self.after)


class Suffix(Postfix):
    pass


class Circumfix(ComplexMorpheme):
    def __init__(self, pre: MU, post: MU):
        super().__init__(Prefix(pre), Postfix(post))
