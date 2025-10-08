import uuid
from collections import defaultdict
from distutils.core import setup_keywords
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, BeforeValidator, model_validator, RootModel, field_validator
from pydash import curry

from keywords import *
import pydash as _

# Config Validation Schema

def ensure_dict_list(data: list | dict[str, Any]) -> list[dict]:
    match data:
        case list(): return data
        case dict(): return [{'id': key, **content} for key, content in data.items()]
        case None: return []
        case _: raise ValueError(f'No strategy for mapping: {data}')

@curry
def is_x_of_y(x_type, y_type, obj) -> bool:
    if not isinstance(obj, x_type): return False
    match obj:
        case list(): items = obj
        case dict(): items = obj.values()
        case _: raise ValueError(f'Unsupported type: {type(obj)}')
    for item in items:
        if not isinstance(item, y_type):
            return False
    return True

is_dict_of_dict = is_x_of_y(dict, dict)

Alphanumeric = Annotated[str, Field(pattern=r'^[a-zA-Z0-9_-]+$')]
ConfType = dict[str, Any]

class Source(RootModel[dict[str, dict[str, ...]]]):
    ...

class Object(RootModel[dict[str, Any]]):
    ...

class Target(RootModel[dict[str, Any]]):
    ...

class Define(RootModel[list[dict[str, ...]]]):
    ...

class Structant(BaseModel):
    uid: Alphanumeric = Field(validation_alias=UID_ALTS)
    source: Source = Field(validation_alias=SOURCE_ALTS)
    object: Object = Field(validation_alias=OBJECT_ALTS)
    target: Target = Field(validation_alias=TARGET_ALTS)
    define: Define = Field(validation_alias=DEFINE_ALTS)

    @classmethod
    @model_validator(mode="before")
    def normalize(cls, data: ConfType) -> ConfType:
        structant = {kw: data.pop(kw, None) for kw in STRUCTANT_KWS}
        # structant: ConfType = _.map_values(structant, self.dictionarize_item)
        structant[UID] = str(uuid.uuid4())
        structant[SOURCE] = cls._normalize_source(structant[SOURCE])
        structant = cls.fulfill_object(structant, data)
        structant[OBJECT] = cls._normalize_object(structant[OBJECT])
        structant[TARGET] = cls._normalize_target(structant[TARGET])
        structant[DEFINE] = cls._normalize_define(structant[DEFINE])
        if data:
            raise NotImplementedError(f'Some structant data is still not properly moved: {data}')
        return structant

    @classmethod
    def _normalize_source(cls, source: dict | list | str | int) -> dict[str, dict[str, ...]]:
        match source:
            case int() as n_args: return {str(i + 1): {} for i in range(n_args)}
            case str() as feat: return cls._normalize_source([feat])
            case list() as lst: return cls._normalize_source([dict.fromkeys(lst, True)])
            case dict() as dct: return dct  # TODO: finish
            case _: raise ValueError('Incorrect data for structant source')

    @classmethod
    def _normalize_object(cls, content: dict | list | str) -> dict:
        match content:
            case None: return {}
            case dict(): return content
            case str(): return {content: True}
            case list(): return dict.fromkeys(content, True)
            case _: raise ValueError(f'Unsupported type for dictionarization: {type(content)}, content: {content}')

    @classmethod
    def _normalize_define(cls, define) -> list[dict[str, ...]]:
        match define:
            case str(): raise NotImplementedError('"define: <str>" is not decided')
            case dict(): return cls.normalize([define])
            case list(): return define

    @classmethod
    def _normalize_target(cls, target) -> dict:
        return target

    @classmethod
    def fulfill_object(cls, structant: ConfType, data: ConfType) -> ConfType:
        if not (structant_id := data.pop(ID, NONE_ID_PREFIX)).startswith(NONE_ID_PREFIX):
            structant[OBJECT].setdefault(ALIASES, []).append(structant_id)
        return structant
    

class Config(BaseModel):
    general: dict[Alphanumeric, Any] = Field(alias=GENERAL)
    ingrains: dict[Alphanumeric, Any] = Field(alias=INGRAINS)
    structants: list[Structant] = Field(alias=STRUCTANTS)

    @classmethod
    @field_validator('structants', mode="before")
    def normalize_structants(cls, structants: ConfType | list[dict]) -> list[dict]:
        match structants:
            case list(): return structants
            case dict(): return [cls.merge_main_alias_with_content(key, content) for key, content in structants.items()]

    @classmethod
    def merge_main_alias_with_content(cls, main_alias: str, content: Any) -> dict:
        match content:
            case dict():
                content.setdefault(ID, main_alias)
                return content
            case _:
                return cls.merge_main_alias_with_content(main_alias, {DEFINE: content})
