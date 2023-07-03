from __future__ import annotations

from typing import Iterable

from collections import deque


def get_name(instance):
	return instance.name if 'name' in instance.__dir__ else instance if isinstance(instance, str) else None


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

	def associate(cls, to_associate: Iterable | object) -> None:  # TODO add annotation
		if cls._current is not None:
			cls._current.associate(to_associate)


class languages(metaclass=MetaLanguages):  # TODO test access
	pass


class Language:
	def __init__(self, name: str):
		languages[name] = self
		self._name: str = name
		self._morphemes: list = []

	@property
	def name(self) -> str:
		return self._name

	def __repr__(self):
		return f'{self.__class__.__name__}({str(self.__dict__)[1:-2]})'

	def associate(self, to_associate: Iterable | object) -> None:  # TODO add annotation
		if not isinstance(to_associate, Iterable):
			self._associate_single(to_associate)
		else:
			deque(map(self.associate, to_associate), 0)

	def _associate_single(self, to_associate) -> None:  # TODO add annotation
		pass


class Morpheme:

	def __init__(self, form: str | None = None):
		languages.associate(self)
		self._form: str = form  # TODO think of class

	def __call__(self, to_apply_to: str):
		raise NotImplementedError

	@property
	def form(self) -> str:
		return self._form

	def associate_to(self, lang: str| Language) -> Morpheme:
		languages[lang].associate(self)
		return self


# Affixes
# def Affix():
# 	pass


class Affix(Morpheme):
	pass


class Adfix(Affix):
	pass


class Prefix(Adfix):
	pass


class Postfix(Adfix):
	pass


class Infix(Affix):  # tmesis
	pass

class Interfix(Affix):
	pass


# ?? Simulfix 	mouse → mice == ?
# ?? Suprafix  pro'duce vs 'produce  ?= vocalic

# end affixes


class Reduplication(Morpheme):
	pass


class Suppletion(Morpheme):
	pass


class Conversion(Morpheme):
	pass


# Vocalics
class Vocalic(Morpheme):  # Stress, Tone, Tonality, pitch-accent, etc.
	pass

# end vocalics


class Truncation(Morpheme):
	pass


class Blend(Morpheme):
	pass


class Abbreviation(Morpheme):
	pass


class Compound(Morpheme):
	pass


class Incorporation(Morpheme):
	pass
