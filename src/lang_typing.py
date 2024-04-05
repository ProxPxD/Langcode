from __future__ import annotations

from typing import Dict, Any, Literal, AnyStr, List

BasicYamlType = str | int | bool | None
ComplexYamlType = dict | list
YamlType = BasicYamlType | ComplexYamlType

Config = Dict[str, Any]  # TODO: Check recurrent hinting  # TODO: verify name and/or make another
Kind = Literal['morpheme', 'grapheme']
Resolution = Literal['joint', 'disjoint']
Elems = Literal['elems']
UnitConf = Dict[AnyStr, Any] | List[AnyStr | Any]
