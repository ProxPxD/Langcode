from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, asdict
from functools import reduce
from typing import Literal, TypeVar, Generic, Callable, Iterable, Tuple, Any, List, Optional

import numpy as np

from src.morphemes_nd import MU
from src.utils import DictClass, get_name, word_to_basics, get_extreme_points

from morphemes_nd import At, Size, By, Side


# TODO THINK: D dir class from py2neo lib?
@dataclass(frozen=True)
class LanguageElems:
    GRAPHEMES = 'graphemes'
    MORPHEMES = 'morphemes'
    FEATURES = 'features'


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
    BEFORE: Side = -1
    AFTER: Side = 1
    AT: Side = 0


@dataclass(frozen=True)
class C:
    FORM = 'form'
    AT = 'at'
    BY = 'by'
    SIDE = 'side'


@dataclass(frozen=True)
class StrDefaults(DictClass):
    form: str = ''
    at: At = 0
    by: By = By.LETTERS

    side: Side = Side.BEFORE
    first: At = 1
    last: At = -1

    before: Side = Side.BEFORE
    after: Side = Side.AFTER


##########################
#       Orthography      #
##########################


class Orthography:
    def __init__(self, *graphemes: Grapheme):
        self.graphemes: dict[str, Grapheme] = {grapheme.name: graphemes for grapheme in graphemes}

    def get_realization(self, word: str | Morpheme) -> str:  # TODO think of return type and if a word should be a subclass of Morhpeme
        return get_name(word)  # TODO


##########################
#        Morpheme        #
##########################


class AbstractMorpheme(Generic[MU]):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.language = languages.associate(self)

    def _inverse_problem(self, problem: Callable, word: MU):
        reverse_result = problem(~self, word[::-1])
        return reverse_result[::-1] if reverse_result is not None else None

    @classmethod
    def _get_default(cls, name: str) -> MU | Any:
        return StrDefaults._dict()[name]

    @abstractmethod
    def _get_index_and_size(self, word: MU) -> Tuple[At, Size]:
        raise NotImplementedError

    @abstractmethod
    def _get_word_parts(self, word: MU, place: At, size: Size = 1, side=None) -> Tuple[MU, ...]:  # TODO think: Generalize to more dimensions rather than strings
        raise NotImplementedError

    @abstractmethod
    def is_bound(self) -> bool:
        raise NotImplementedError

    # TODO think: should "is_adding" be declared here?

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

    @abstractmethod
    def __call__(self, word: MU, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def __invert__(self) -> SimpleMorphemeND:
        raise NotImplementedError

    @abstractmethod
    def __add__(self, other: SimpleMorphemeND):
        raise NotImplementedError


# TODO think: How to implement conditional src, pos: within the class, separately
class SimpleMorphemeND(AbstractMorpheme, Generic[MU]):
    is_using_inversion = True

    # TODO: change tests to encopass the raises argument
    def __init__(self, form1: MU = None, form2: MU = None, *, at: At = None, by: By = None, side: Side = None, raises: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.to_remove: MU = form1 if form1 is not None else self._get_default(C.FORM)
        self.to_insert: MU = form2 if form2 is not None else self._get_default(C.FORM)
        self.at: At = at if at is not None else self._get_default(C.AT)
        self.by: By = by if by is not None else self._get_default(C.BY)
        self.side: Side = side if side is not None else Side.BEFORE if self.at > 0 else Side.AFTER
        self.raises: bool = raises

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
    def _get_index_and_size(self, word: MU) -> Tuple[At, Size]:
        all_step_members = self.language.step_members if self.language is not None else Language.general_step_members
        if self.by != By.LETTERS:
            step_members = all_step_members[self.by]
            index_parts = list(map(lambda e: tuple(reversed(e)), word_to_basics(word, step_members, yield_index=True, skip_missing=True)))
        else:
            index_parts = list(zip(range(0, len(word)), word))  # TODO think: better size handling
        adjusted_at = self.at - 1 if self.at > 0 else np.subtract(len(word), self.at)
        index, size = next(((index, len(part)) for (i, (index, part)) in enumerate(index_parts) if i == adjusted_at), tuple((len(word), 0)))  # TODO Generalize default empty
        if abs(self.at) > index + 1:
            raise ValueError  # TODO: more test to verify
        return index, size

    def _get_word_parts(self, word: MU, place: At, size: Size = 1, side=None) -> Tuple[MU, ...]:
        side = side if side is not None else self.side
        match side:
            case Side.BEFORE:
                return word[:place], word[place:]
            case Side.AT:
                return word[:place], word[place + size:]  # TODO think: or size?
            case Side.AFTER:
                return self._get_word_parts(word, place + size, size, Side.BEFORE)  # TODO think: or size?

    def is_applicable(self, word: MU, *args, **kwargs) -> bool:
        if self.is_using_inversion and self.at < 0:
            return self._inverse_problem(SimpleMorphemeND.insert, word)
        try:
            index, size = self._get_index_and_size(word)
        except ValueError:
            return False
        is_applicable = not self.to_remove or self._is_applicable_for_remove(word, index)
        is_applicable &= not self.to_insert or self._is_applicable_for_insert(word, index)
        return is_applicable

    def _is_applicable_for_insert(self, word: MU, index, *args, **kwargs) -> bool:
        return True  # TODO: implement

    def _is_applicable_for_remove(self, word: MU, index, *args, **kwargs) -> bool:
        # TODO move this to abstract after generalizing "len" (size_of) and "[]" (slice_of?)"
        remove_range = get_extreme_points(word, index, len(self.to_remove))
        return self.to_remove in remove_range

    def is_present(self, word: MU, *args, **kwargs) -> MU:
        if self.is_using_inversion and self.at < 0:
            return self._inverse_problem(SimpleMorphemeND.insert, word)
        try:
            index, size = self._get_index_and_size(word)
        except ValueError:
            return False
        # TODO move this to abstract after generalizing "[]"
        return word[index: index + size] == (self.to_remove if self.to_remove else self.to_insert)

    def insert(self, word: MU, *args, **kwargs) -> MU:
        # TODO move this to abstract after generalizing num of parts and it's concatanation with form
        if self.is_using_inversion and self.at < 0:
            return self._inverse_problem(SimpleMorphemeND.insert, word)
        try:
            index, size = self._get_index_and_size(word)
        except ValueError as e:
            if self.raises:
                raise e
            return word
        part1, part2 = self._get_word_parts(word, index)
        result = part1 + self.to_insert + part2
        return result

    # eme remove(self, word: MU, *args, **kwargs) -> MU:
    #     # TODO move this to abstract after generalizing num of parts and it's concatanation with form
    #     if self.is_using_inversion and self.at < 0:
    #         return self._inverse_problem(SingleMorpheme.remove, word)
    #     index, size = self._get_index_and_size(word)
    #     min_point, max_point = get_extreme_points(word, index, len(self.to_remove))
    #     middle = word[min_point:max_point]
    #     if self.to_remove not in middle:
    #         raise ValueError  # TODO specify
    #     result = word[:min_point] + middle.replace(self.to_remove, '') + word[max_point:]
    #     return result

    def replace(self, word: MU, *args, **kwargs) -> MU:
        # TODO move this to abstract after generalizing "negativity of at, inversing problem according to specific axis""
        if self.is_using_inversion and self.at < 0:
            return self._inverse_problem(SimpleMorphemeND.replace, word)
        try:
            index, size = self._get_index_and_size(word)
        except ValueError as e:
            if self.raises:
                raise e
            return word
        min_point, max_point = get_extreme_points(word, index, len(self.to_remove))
        middle = word[min_point:max_point]
        if self.to_remove not in middle:
            if self.raises:
                raise ValueError  # TODO specify
            return word
        # TODO: make more precise
        result = word[:min_point] + middle.replace(self.to_remove, self.to_insert) + word[max_point:]
        return result

    def __call__(self, word: MU, *args, **kwargs):
        if self.to_remove and self.to_insert:
            return self.replace(word)
        elif self.to_insert:
            return self.insert(word)
        elif self.to_remove:
            return self.replace(word)
        else:
            return word

    def __invert__(self) -> SimpleMorphemeND:
        return SimpleMorphemeND(self.to_remove[::-1], self.to_insert[::-1], at=np.subtract(0, self.at), by=self.by, side=np.subtract(0, self.side))

    def __add__(self, other: SimpleMorphemeND):
        if self.language != other.language:
            raise ArithmeticError
        return ComplexMorphemeND(self, other)

    def __repr__(self) -> str:
        return f"Morpheme(to_remove={self.to_remove if self.to_remove else ''}, to_insert={self.to_insert if self.insert else ''}, at={self.at}, by={self.by}, side={self.side}, lang={self.language})"


class ComplexMorphemeND(AbstractMorpheme):
    def __init__(self, *morphemes: AbstractMorpheme, **kwargs):
        super().__init__(**kwargs)
        self.morphemes: List[AbstractMorpheme] = [m for morph in morphemes for m in (morph.morphemes if isinstance(morph, ComplexMorphemeND) else [morph])]

    def insert(self, word: MU, *args, **kwargs) -> MU:
        return reduce(lambda w, morph: morph.insert, self.morphemes, word)

    def remove(self, word: MU, *args, **kwargs) -> MU:
        return reduce(lambda w, morph: morph.remove, self.morphemes, word)

    def replace(self, word: MU, *args, **kwargs) -> MU:
        return reduce(lambda w, morph: morph.replace, self.morphemes, word)

    def __invert__(self):
        return ComplexMorphemeND(*tuple(map(AbstractMorpheme.__invert__, self.morphemes)))


class ConditionalMorphemeND(AbstractMorpheme):
    def __init__(self, cond: Callable[[MU], bool] | SimpleMorphemeND, positive: ComplexMorphemeND | SimpleMorphemeND, negative: ComplexMorphemeND | SimpleMorphemeND | str = None, **kwargs):
        super().__init__(**kwargs)
        # TODO think: if cond should be callable or morpheme
        # if morpheme, then should it be specified if used existing or not existing?
        # if callable, then simply negate the cond?
        # Can be both?
        self.cond: SimpleMorphemeND | Callable[[MU], bool] = cond
        self.positive: ComplexMorphemeND | SimpleMorphemeND = positive
        self.negative: ComplexMorphemeND | SimpleMorphemeND = negative if isinstance(negative, (SimpleMorphemeND, ComplexMorphemeND)) else SimpleMorphemeND(
            negative if negative is not None else self.default, positive.at, positive.by, positive.side)

    def insert(self, word: MU, *args, **kwargs) -> MU:
        return self.positive(word) if self.cond(word) else self.negative(word)

    def __invert__(self):
        return Morpheme(~self.cond, ~self.positive, ~self.negative)


class Morpheme(SimpleMorphemeND, ComplexMorphemeND, ConditionalMorphemeND):
    def __init__(self, *form: Morpheme | MU, at: At = None, by: By = None, side: Side = None, cond: Callable[[MU], bool] | SimpleMorphemeND = None,
            positive: SimpleMorphemeND = None, negative: SimpleMorphemeND | str = None, **kwargs):
        single_form = form[0] if len(form) == 1 else None
        morphemes = tuple() if len(form) < 2 else tuple(map(lambda f: f if isinstance(f, Morpheme) else Morpheme(f, at=at, by=by, side=side), form))
        super(SimpleMorphemeND).__init__(single_form, at=at, by=by, side=side)
        super(ComplexMorphemeND).__init__(*morphemes)
        super(ConditionalMorphemeND).__init__(cond=cond, positive=positive, negative=negative)


#############
# Templates #
#############
# TODO: think of making them functions returning classes

class Prefix(SimpleMorphemeND):
    def __init__(self, form: MU):
        super().__init__(form, at=self.first, by=By.LETTERS, side=self.before)


class Postfix(SimpleMorphemeND):
    def __init__(self, form: MU):
        super().__init__(form, at=self.last, by=By.LETTERS, side=self.after)


class Suffix(Postfix):
    pass


class Circumfix(ComplexMorphemeND):
    def __init__(self, pre: MU, post: MU):
        super().__init__(Prefix(pre), Postfix(post))
