from collections import ChainMap

from src.constants import basic_yaml_type, complex_yaml_type, yaml_type, SimpleTerms, ComplexTerms
from src.utils import is_list_of_dicts, is_list_of_basics


class DataNormalizer:
    def __init__(self):
        pass

    def yaml_type_to_dict(self, elems: complex_yaml_type) -> dict:
        match elems:
            case dict():
                return elems
            case list():
                return self.list_to_dict(elems)
            case int() | str() | bool() | None:
                raise NotImplementedError
            case _:
                raise AttributeError

    def list_to_dict(self, to_cast: list) -> dict:
        if is_list_of_dicts(to_cast):
            return self.dict_list_to_dict(to_cast)
        if is_list_of_basics(to_cast):
            return dict.fromkeys(to_cast)

    def dict_list_to_dict(self, to_cast: list[dict[str, str | list[str]]]) -> dict[str, list[str]]:
        casted = {}
        for subdict in to_cast:
            for key, value in subdict.items():
                for single_value in (value if isinstance(value, list) else (value,)):
                    casted.setdefault(key, []).append(single_value)
        return casted

    def normalize(self, config: dict) -> dict | None:
        for unit_type in ComplexTerms.UNTIS:
            if unit_type in config:
                self._normalize_unit(config[unit_type])
        return config

    def _normalize_unit(self, config: dict) -> None:
        for subkey in ComplexTerms.UNIT_SUBKEYS:
            if subkey in config:
                config[subkey] = self.yaml_type_to_dict(config[subkey])
