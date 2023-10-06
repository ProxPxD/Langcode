from types import NoneType
from typing import Callable, Any

from src.constants import LangData


class SchemaValidator:
    @classmethod
    def validate(cls, to_val: dict, kind: str = LangData.LANGUAGE) -> bool:
        return cls.get_validation(kind)(to_val)

    @classmethod
    def validate_dict(cls, to_val: dict, requireds=None, **kwargs) -> bool:
        if isinstance(to_val, (str, NoneType)):
            return True
        requireds = requireds or tuple()
        has_requireds = all((required in to_val for required in requireds))
        return has_requireds and all((isinstance(name, str) and cls.get_validation(name)(elem, **kwargs) for name, elem in to_val.items()))

    @classmethod
    def get_validation(cls, kind: str) -> Callable[[dict | str, Any, ...], bool]:
        try:
            func = getattr(cls, f'validate_{kind}')
        except Exception:
            func = cls.validate_dict
        return func

    @classmethod
    def validate_language(cls, to_val: dict, **kwargs) -> bool:
        return cls.validate_dict(to_val, requireds=(LangData.FEATURES, LangData.MORPHEMES, LangData.GRAPHEMES), **kwargs)
