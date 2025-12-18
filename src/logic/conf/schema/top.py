import uuid
from typing import Annotated, Any, Optional

import yaml
from pydantic import BaseModel, Field, model_validator, RootModel, field_validator
from pydash import curry

from src.logic.conf.schema.general import General
from src.logic.conf.schema.structant import Structant
from src.logic.conf.schema.utils import Alphanumeric, ConfType
from src.logic.consts.keywords import *


# # Config Validation Schema
#
# def ensure_dict_list(data: list | dict[str, Any]) -> list[dict]:
#     match data:
#         case list(): return data
#         case dict(): return [{'id': key, **content} for key, content in data.items()]
#         case None: return []
#         case _: raise ValueError(f'No strategy for mapping: {data}')
#
# @curry
# def is_x_of_y(x_type, y_type, obj) -> bool:
#     if not isinstance(obj, x_type): return False
#     match obj:
#         case list(): items = obj
#         case dict(): items = obj.values()
#         case _: raise ValueError(f'Unsupported type: {type(obj)}')
#     for item in items:
#         if not isinstance(item, y_type):
#             return False
#     return True
#
# is_dict_of_dict = is_x_of_y(dict, dict)


class Conf(BaseModel):
    general: General = Field(alias=GENERAL, default=None)
    ingrains: dict[Alphanumeric, Any] = Field(alias=INGRAINS, default=None)
    structants: list[Optional[Structant]] | dict[str, Optional[Structant]] | str  = Field(alias=STRUCTANTS)


    @field_validator('structants', mode='before')
    @classmethod
    def normalize_structants(cls, structants: ConfType | list[dict] | str) -> list[Structant]:
        match structants:
            case str(): return cls.normalize_structants(yaml.safe_load(structants))
            case list(): return list(map(lambda s: cls.merge_main_alias_with_content(None, s), structants))
            case dict(): return [cls.merge_main_alias_with_content(key, content) for key, content in structants.items()]

    @classmethod
    def merge_main_alias_with_content(cls, main_alias: Optional[str], content: Any) -> Structant:
        match content:
            case dict():
                if main_alias:
                    content.setdefault(ID, main_alias)
                return Structant(**(content or {}))
            case _:
                return cls.merge_main_alias_with_content(main_alias, {DEFINE: content})
