from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any

from src.logic.gdm.login_data import LoginData


class GDM(ABC):
    """
    Graph Database Manager -- Interface for common queries
    """
    _gdm = None

    @classmethod
    def curr(cls) -> GDM:
        return cls._gdm

    def __init__(self, log: LoginData, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database: str = log.database
        self.driver = None
        self._session = None

    def __eq__(self, other: GDM | Any) -> bool:
        match other:
            case GDM(): return self.driver == other.driver
            case _: return False

    @contextmanager
    def session(self, database: str = None, *args, **kwargs):
        self._session = self.init_session(database=database or self.database, *args, **kwargs)
        self._gdm = self
        try:
            return self._session
        finally:
            self.exit_session()
            self._gdm = None

    @abstractmethod
    def init_session(self, database: str = None, *args, **kwargs):
        return ...

    def exit_session(self) -> None:
        ...

    @abstractmethod
    def raw_query(self, query: str, **kwargs) -> list[dict[str, Any]]:
        return ...





