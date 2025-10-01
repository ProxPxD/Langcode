from types import NoneType

SimpleYamlType = bool | str | int | NoneType
ComplexYamlType = dict | list
YamlType = SimpleYamlType | ComplexYamlType