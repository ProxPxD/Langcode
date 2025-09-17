from typing import Annotated, Any

from pydantic import BaseModel, Field, BeforeValidator

# Config Validation Schema

Alphanumeric = Annotated[str, Field(pattern=r'^[a-zA-Z0-9_-]+$')]


def ensure_dict_list(data: list | dict[str, Any]) -> list[dict]:
    match data:
        case list(): return data
        case dict(): return [{'id': key, **content} for key, content in data.items()]
        case None: return []
        case _: raise ValueError(f'No strategy for mapping: {data}')

class Structant(BaseModel):
    id: Alphanumeric = None
    source: None
    object: None
    target: None


class Config(BaseModel):
    general: dict[Alphanumeric, Any]
    ingrains: dict[Alphanumeric, Any]
    structives: Annotated[
        list[Structant] | dict[Alphanumeric, Structant],
        BeforeValidator(ensure_dict_list)
    ]

