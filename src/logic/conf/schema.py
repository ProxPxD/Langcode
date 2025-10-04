import uuid
from collections import defaultdict
from distutils.core import setup_keywords
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, BeforeValidator, model_validator, RootModel
from keywords import *
import pydash as _

# Config Validation Schema

def ensure_dict_list(data: list | dict[str, Any]) -> list[dict]:
    match data:
        case list(): return data
        case dict(): return [{'id': key, **content} for key, content in data.items()]
        case None: return []
        case _: raise ValueError(f'No strategy for mapping: {data}')


Alphanumeric = Annotated[str, Field(pattern=r'^[a-zA-Z0-9_-]+$')]
ConfType = dict[str, Any]


class Source(RootModel[dict[str, ...]]):
    @model_validator(mode="before")
    def normalize_data(self, data: dict | list | str | int) -> ConfType:
        return self.normalize(data)

    @classmethod
    def normalize(cls, data: dict | list | str | int) -> ConfType:
        match data:
            case int() as n_args: return {str(i+1): {} for i in range(n_args)}
            case str() as feat: return cls.normalize([feat])
            case list(): ...
            case dict(): ...
            case _: raise ValueError('Incorrect data for structant source')

class Structant(BaseModel):
    uid: Alphanumeric = Field(alias=UID)
    source: Source = Field(alias=SOURCE)
    object: dict[str, Any] = Field(alias=OBJECT)
    target: dict[str, Any] = Field(alias=TARGET)
    define: None = Field(alias=DEFINE)

    @model_validator(mode="before")
    def normalize(self, data: ConfType) -> ConfType:
        structant = {kw: data.pop(kw, None) for kw in STRUCTANT_KWS}
        # structant: ConfType = _.map_values(structant, self.dictionarize_item)
        structant[UID] = str(uuid.uuid4())
        structant[SOURCE] = self._normalize_source(structant[SOURCE])
        structant = self.fulfill_object(structant, data)
        structant[OBJECT] = self._normalize_object(structant[OBJECT])
        if data:
            raise NotImplementedError(f'Some structant data is still not properly moved: {data}')
        return structant

    @classmethod
    def dictionarize_item(cls, content: Any) -> dict:
        match content:
            case None: return {}
            case dict(): return content
            case str(): return {content: True}
            case list(): return dict.fromkeys(content, True)
            case _: raise ValueError(f'Unsupported type for dictionarization: {type(content)}, content: {content}')

    @classmethod
    def _normalize_source(cls, source: dict | list | str | int) -> Optional[ConfType]:
        if not source:
            return None
        if isinstance(source, list):
            ...

    @classmethod
    def _normalize_object(cls, object: dict | list | str) -> Optional[ConfType]:
        return cls.dictionarize_item(object)

    @classmethod
    def fulfill_object(cls, structant: ConfType, data: ConfType) -> ConfType:
        if not (structant_id := data.pop(ID, NONE_ID_PREFIX)).startswith(NONE_ID_PREFIX):
            structant[OBJECT].setdefault(ALIASES, []).append(structant_id)
        return structant
    

class Config(BaseModel):
    general: dict[Alphanumeric, Any] = Field(alias=GENERAL)
    ingrains: dict[Alphanumeric, Any] = Field(alias=INGRAINS)
    structants: Annotated[
        list[Structant] | dict[Alphanumeric, Structant],
        BeforeValidator(ensure_dict_list)
    ] = Field(alias=STRUCTANTS)

