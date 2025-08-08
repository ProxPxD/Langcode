from typing import Optional, Any

from pydantic import BaseModel, model_validator


class LoginData(BaseModel):
    port: int = None
    host: str = None
    user: str = None
    password: str = None
    database: Optional[str] = None

    @property
    def auth(self) -> tuple[str, str]:
        return self.user, self.password

    @property
    def uri(self) -> str:
        return f'{self.host}:{self.port}'

    @model_validator(mode='before')
    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        data = self.validate_auth(**data)
        data = self.validate_uri(**data)
        data = self.adjust_names(**data)
        return data

    @classmethod
    def validate_auth(cls,
            auth: tuple[str, str] | tuple[str] = None,
            user: str = None,
            password: str = None,
            **data
        ) -> dict:
        if not (auth or user and password):
            raise ValueError(f'Logging requires "auth" or "user" and "password" in init')
        data.update(
            user=user or auth[0],
            password=password or auth[-1],
        )
        return data

    @classmethod
    def validate_uri(cls, uri: str, host: str, port: int | str, **data) -> dict:
        if not (uri or host and port):
            raise ValueError(f'Logging requires "uri" or "host" and "port" in init')
        host, port = (host, port) if host and port else uri.split(':')
        data.update(host=host, port=int(port))
        return data

    @classmethod
    def adjust_names(cls, database: str = None, db: str = None, **data) -> dict:
        data.update(database=database or db)
        return data
