from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, model_validator


uri_pattern: re.Pattern = re.compile(r'(?P<protocol>[^:]+)://(?P<host>[^:]+):(?P<port>\d{1,5})')


class LoginData(BaseModel):
    protocol: str = None
    host: str = None
    port: int = None
    user: str = None
    password: str = None
    database: str = None

    @property
    def auth(self) -> tuple[str, str]:
        return self.user, self.password

    @property
    def uri(self) -> str:
        return f'{self.protocol}://{self.host}:{self.port}'

    @model_validator(mode='before')
    @classmethod
    def validate(cls, data: dict[str, Any]) -> dict[str, Any]:
        data = cls._validate_auth(**data)
        data = cls._validate_uri(**data)
        data = cls._adjust_names(**data)
        return data

    @classmethod
    def _validate_auth(cls,
                       auth: tuple[str, str] | str = None,
                       user: str = None,
                       password: str = None,
                       **data
                       ) -> dict:
        if not (auth or user and password):
            raise ValueError(f'Logging requires "auth" or "user" and "password" in init')
        user, password = (user, password) if user and password else (auth.split(':') if isinstance(auth, str) else auth)
        data.update(user=user, password=password)
        return data

    @classmethod
    def _validate_uri(cls, uri: str = None, protocol: str = None, host: str = None, port: int | str = None, **data) -> dict:
        if not (uri or protocol and host and port):
            raise ValueError(f'Logging requires "uri" or "host" and "port" in init')
        protocol, host, port = (protocol, host, port) if protocol and host and port else uri_pattern.match(uri).groups()
        data.update(protocol=protocol, host=host, port=int(port))
        return data

    @classmethod
    def _adjust_names(cls, database: str = None, db: str = None, **data) -> dict:
        data.update(database=database or db)
        return data
