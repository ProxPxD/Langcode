from types import NoneType
from typing import Callable, Any

from src.constants import LangData
from src.exceptions import InvalidYamlException, Messages
from src.language import Language

from strictyaml import load, Map, Str, Int, Seq, YAMLError, MapPattern, MapCombined, Optional, Bool

general_schema = Map({

})

features_schema = Map({

})

morpheme_schema = MapCombined(
    {
        Optional('bound'): Bool()
    },
    Str(),
    Any()
)

graphemes_schema = Map({

})

morphemes_schema = MapPattern(Str(), morpheme_schema)


rules_schema = Map({

})


lang_schema = Map({
    'general': general_schema,
    'features': features_schema,  # TODO: think if should be inside graphemes and morphemes
    'graphemes': graphemes_schema,
    'morphemes': morphemes_schema,
    'rules': rules_schema,

})


class SchemaValidator:
    @classmethod
    def validate(cls, to_val: dict, kind: str = LangData.LANGUAGE) -> bool:
        return cls.get_validation(kind)(kind, to_val)

    @classmethod
    def validate_dict(cls, curr_kind: str, to_val: dict, requireds=None, next_kind: str = None, **kwargs) -> bool:
        if isinstance(to_val, (str, NoneType)):
            return True
        cls._validate_dict_required(curr_kind, to_val, requireds)
        return cls._validate_dict_subfields(curr_kind, to_val, next_kind, **kwargs)

    @classmethod
    def _validate_dict_required(cls, curr_kind: str, to_val: dict, requireds: tuple):
        if requireds:
            for req_to_val in requireds:
                if req_to_val not in to_val:
                    raise InvalidYamlException(Messages.LACK_OF_REQUIRED_FIELD % (curr_kind, req_to_val))
        return True

    @classmethod
    def _validate_dict_subfields(cls, curr_kind: str, to_val: dict, next_kind: str = None, **kwargs) -> bool:
        get_next_val = lambda name: cls.get_validation(next_kind) if next_kind else cls.get_validation(name)
        for name, elem in to_val.items():
            try:
                get_next_val(name)(name, elem, **kwargs)
            except InvalidYamlException as iye:
                raise InvalidYamlException(f'{curr_kind} > ', *iye.args)
        return True

    @classmethod
    def get_validation(cls, kind: str) -> Callable[[dict | str, Any, ...], bool]:
        return getattr(cls, f'validate_{kind}', cls.validate_dict)

    @classmethod
    def validate_language(cls, curr_kind: str, to_val: dict, **kwargs) -> bool:
        return cls.validate_dict(curr_kind, to_val, requireds=(LangData.MORPHEMES, ), **kwargs)

    @classmethod
    def validate_morphemes(cls, curr_kind, to_val, **kwargs) -> bool:
        return cls.validate_dict(curr_kind, to_val, next_kind=LangData.MORPHEMES, **kwargs)

    @classmethod
    def validate_morpheme(cls, curr_kind, to_val, **kwargs) -> bool:
        if to_val is None:
            raise InvalidYamlException(Messages.NOT_DEFINED % curr_kind)
        exclusives_with_form = (LangData.COMPOUND, )
        is_any_exclusives_with_form = any(map(to_val.__contains__, exclusives_with_form))
        is_form_in = LangData.FORM in to_val

        if is_form_in and is_any_exclusives_with_form:
            raise InvalidYamlException(Messages.FORMING_KEYS_TOGETHER)
        if not is_form_in and not is_any_exclusives_with_form:
            raise InvalidYamlException(Messages.NO_FORMING_KEY)
        return True

    @classmethod
    def validate_rules(cls, curr_kind, to_val, **kwargs) -> bool:
        return cls.validate_dict(curr_kind, to_val, next_kind=LangData.RULES, **kwargs)

    @classmethod
    def validate_rule(cls, curr_kind, to_val, **kwargs) -> bool:
        return False