import uuid
from typing import Annotated, Any

from pydantic import BaseModel, Field, BeforeValidator, model_validator
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


class Structant(BaseModel):
    uid: Alphanumeric = Field(alias=UID)
    source: dict[str, Any] = Field(alias=SOURCE)
    object: dict[str, Any] = Field(alias=OBJECT)
    target: dict[str, Any] = Field(alias=TARGET)
    define: None = Field(alias=DEFINE)

    @model_validator(mode="before")
    def normalize(self, data: ConfType) -> ConfType:
        structant = {kw: data.pop(kw, None) for kw in STRUCTANT_KWS}
        structant: ConfType = _.map_values(structant, self.dictionarize_item)
        structant[UID] = str(uuid.uuid4())
        structant = self.fulfill_object(structant, data)
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

