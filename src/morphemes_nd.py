from __future__ import annotations

from abc import abstractmethod
from dataclasses import asdict
from typing import TypeVar, Generic, Callable, Literal, Iterable, Optional

from src.utils import get_name

MU = TypeVar('MU')  # Morpheme Unit

At = int | tuple[int, ...]
Size = At
By = str | tuple[str, ...]
Side = Literal[-1, 0, 1] | tuple[Literal[-1, 0, 1], ...]


##########################
#        Language        #
##########################


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


class Characteristic:
    def __init__(self, name: str, characterizings: Iterable[Characteristic], characteristics: Iterable[Characteristic]):
        self.name: str = name
        self.characterizings: dict[str, Characteristic] = {characterizing.name: characterizing for characterizing in characterizings}  # noun, etc.
        self.characteristics: dict[str, Characteristic] = {characteristic.name: characteristic for characteristic in characteristics} # masculine, feminine

    def __getitem__(self, characteristic: str) -> Optional[Characteristic]:
        return self.characteristics.get(characteristic, None)

    def __contains__(self, characteristic):  # TODO: warning, it may not always be an expected behaviour
        return characteristic in self.characteristics or any((characteristic in characteristic_object for characteristic_object in self.characteristics.values()))


class Language(Generic[MU]):

    def __init__(self, name: str, featured: Iterable[Characteristic], features: Iterable[Characteristic]):
        languages[name] = self
        self.feature_description: Characteristic = Characteristic(name, featured, features)
        self.orthography = Orthography()  # TODO rethink creation args and method
        self.morphemes = {}

    def get(self, language_elem: str) -> dict:
        key = language_elem.lower()
        if key in asdict(LanguageElems()).values():
            return self.__dict__[key]
        raise ValueError

    def __getitem__(self, language_elem: str):
        return self.get(language_elem)

    def associate(self, to_associate: Iterable | Morpheme | Grapheme) -> Language:  # TODO add annotation
        if not isinstance(to_associate, Iterable):
            return self._associate_single(to_associate)
        else:
            return reduce(lambda a, b: a, map(self.associate, to_associate))

    def _associate_single(self, to_associate: Grapheme | Morpheme) -> Language:  # TODO add annotation
        match to_associate:
            case Grapheme() | Morpheme():
                language_elems = self.get(f'{type(to_associate).__name__}s'.lower())
                language_elems[to_associate.name] = to_associate
            case _:
                raise NotImplementedError
        return self

    def has_feature(self, feature: str) -> bool:
        return feature in self.feature_description


class LanguageElement:
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        if self.name is not None:
            self.language = languages.associate(self)


class Featured(LanguageElement):
    def __init__(self, name: str, **features):
        super().__init__(name)
        self._features: dict = features

    def is_(self, feature: str) -> Optional[bool]:
        if not self.language.has_feature(feature):
            raise ValueError

    def get(self, name: str) -> Optional[bool] | str:  # todo think of returning an array of features in case of multiple feature allowance
        if name in self.language.feature_description:
            return self._features.get(name, None)
        if name in self.language.feature_category:
            possibles = self.language.feature_category[name]
            return next((feature for feature in possibles if self.get(feature)), None)
        raise ValueError

    def __getitem__(self, name) -> Optional[bool] | str:
        return self.get(name)

    def __setitem__(self, name, value) -> None:
        if name in self.language.feature_category:
            possibles = self.language.feature_category[name]
            if value not in possibles:
                raise ValueError
            self[value] = True
        elif name in self.language.feature_description:
            self._features[name] = value
        else:
            raise ValueError


##########################
#        Grapheme        #
##########################


class Grapheme(Featured, LanguageElement):
    def __init__(self, name: str, **features):
        if not all(isinstance(feature, str) and isinstance(value, (bool, str, int, float)) for feature, value in features.items()):
            raise ValueError  # TODO handle
        super().__init__(name, **features)  # todo think if shouldn't be passed with another method

# todo add test for wether every sub-feature can be repeated in a different super-feature or rather they should be nor repeated


##########################
#        Morpheme        #
##########################


class IBound:
    def __init__(self, bounded: bool):
        self.bounded = bounded

    def is_bound(self) -> bool:
        return self.bounded

    def is_free(self) -> bool:
        return not self.bounded


class MorphemeND(Generic[MU], LanguageElement):
    def __init__(self, name: Optional[str], /, at: At = None, by: By = None, side: Side = None, bounded: bool = False, raises=True, *args, **kwargs):
        super().__init__(name, bounded=bounded, *args, **kwargs)
        self._at: At = at
        self._by: By = by
        self._side: Side = side  # if side is not None else Side.BEFORE if self.at > 0 else Side.AFTER
        self.raises: bool = raises

    @abstractmethod
    def __invert__(self) -> MorphemeND:
        return MorphemeND(None, self.to_remove[::-1], self.to_insert[::-1], at=np.subtract(0, self._at), by=self._by, side=np.subtract(0, self._side))

    def _inverse_problem(self, problem: Callable, word: MU):
        reverse_result = problem(~self, word[::-1])
        return reverse_result[::-1] if reverse_result is not None else None

    def set_settings(self, at: At = None, by: By = None, side: Side = None) -> None:
        kwargs = {'at': at, 'by': by, 'side': side}
        for key, value in kwargs.items():
            self.__dict__[f'_{key}'] = tuple(value) if (isinstance(value, Iterable) and not isinstance(value, str)) else (value, )

    def is_present(self, word: MU, /, at: At = None, by: By = None, side: Side = None) -> bool:
        self.set_settings(at=at, side=side, by=by)
        return False
        #raise NotImplementedError

    def is_applicable(self, word: MU, /, at: At = None, by: By = None, side: Side = None) -> bool:
        self.set_settings(at=at, side=side, by=by)
        return False

    def __call__(self, word: MU, /, at: At = None, by: By = None, side: Side = None):
        # TODO add decidingh whether remove or insert
        return self.apply(word, at=at, by=by, side=side)

    def apply(
            self, word: MU, /,
            insert: bool = None, remove: bool = None,
            at: At = None, by: By = None, side: Side = None) -> MU:
        if insert is True or remove is False:
            return self.insert(word)
        if remove is True or insert is False:
            return self.remove(word)
        # TODO think what about replace?
        if insert is None and remove is None:
            raise NotImplementedError

    def insert(self, word: MU, /, at: At = None, by: By = None, side: Side = None) -> MU:
        raise NotImplementedError

    def remove(self, word: MU, /, at: At = None, by: By = None, side: Side = None) -> MU:
        raise NotImplementedError