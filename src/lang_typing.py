from __future__ import annotations

from typing import Dict, Any, Literal, AnyStr, List, TypeVar, Union, Sequence

BasicYamlType = str | int | bool | None
ComplexYamlType = dict | list
YamlType = BasicYamlType | ComplexYamlType

Config = Dict[str, Any]  # TODO: Check recurrent hinting  # TODO: verify name and/or make another
Kind = Literal['morpheme', 'grapheme']
Resolution = Literal['joint', 'disjoint']
Elems = Literal['elems']
ElemsConf = Dict[AnyStr, Any] | List[AnyStr | Any]
FeatureConf = Dict[AnyStr, List[AnyStr] | None]

T = TypeVar('T')
OneOrMore = T | Sequence[T]
