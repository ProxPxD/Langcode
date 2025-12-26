import uuid
from typing import Any

from pydantic import RootModel, BaseModel, Field, AliasChoices
from pydantic import model_validator

from src.logic.conf.schema.utils import Alphanumeric, ConfType
from src.logic.consts.keywords import *


class Source(RootModel[dict[str, Any]]):
    ...

class Object(RootModel[dict[str, Any]]):
    ...

class Target(RootModel[dict[str, Any]]):
    ...

class Define(RootModel[list[dict[str, Any]]]):
    ...

class Structant(BaseModel):
    uid: Alphanumeric = Field(validation_alias=AliasChoices(*UID_ALTS))
    source: Source = Field(validation_alias=AliasChoices(*SOURCE_ALTS))
    object: Object = Field(validation_alias=AliasChoices(*OBJECT_ALTS))
    target: Target = Field(validation_alias=AliasChoices(*TARGET_ALTS))
    define: Define = Field(validation_alias=AliasChoices(*DEFINE_ALTS))


    @model_validator(mode="before")
    @classmethod
    def normalize(cls, data: ConfType) -> ConfType:
        structant = {kw: data.pop(kw, {}) or {} for kw in STRUCTANT_KWS}
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
            case None: return {}
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
            case None: return []
            case str(): raise NotImplementedError('"define: <str>" is not decided')
            case dict(): return cls._normalize_define([define])
            case list(): return define

    @classmethod
    def _normalize_target(cls, target) -> dict:
        return target or {}

    @classmethod
    def fulfill_object(cls, structant: ConfType, data: ConfType) -> ConfType:
        print(structant)
        if not (structant_id := data.pop(ID, NONE_ID_PREFIX)).startswith(NONE_ID_PREFIX):
            structant.setdefault(OBJECT, {}).setdefault(ALIASES, []).append(structant_id)
        return structant
