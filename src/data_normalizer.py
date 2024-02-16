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
            case basic_yaml_type():
                raise NotImplementedError
            case _:
                raise AttributeError

    def list_to_dict(self, to_cast: list) -> dict:
        if is_list_of_dicts(to_cast):
            return dict(ChainMap(*to_cast))
        if is_list_of_basics(to_cast):
            return dict.fromkeys(to_cast)

    def normalize(self, config: dict) -> dict | None:
        for unit_type in ComplexTerms.UNTIS:
            if unit_type in config:
                self._normalize_unit(config[unit_type])
        return config

    def _normalize_unit(self, config: dict) -> None:
        if SimpleTerms.ELEMS in config:
            config[SimpleTerms.ELEMS] = self.yaml_type_to_dict(config[SimpleTerms.ELEMS])
