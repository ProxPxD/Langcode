from __future__ import annotations

from types import NoneType
from typing import Optional

from src.logic.conf.schema import ConfType
from src.logic.db import GDM


class Structive:
    def __new__(cls, conf: dict = None, lcid: str = None, **kwargs):
        if not isinstance(lcid, (NoneType, str)):
            raise ValueError('LCID has to be string or None')

        gdm = GDM.curr()

        if gdm and lcid and (pot_structive := gdm.find(lcid=lcid, raises=False)):
            return pot_structive
        # TODO: logic!
        return super().__new__(cls)

    def __init__(self, conf: dict = None, lcid: str = None, **kwargs):
        super().__init__(**kwargs)
        self._gdm: GDM = GDM.curr()
        self._lcid: Optional[str] = lcid
        self._source = Structive(conf.get('source'))
        self._target = ...

    @property
    def lcid(self) -> Optional[str]:
        return self._lcid


class Structive_:

    def __init__(self, conf: dict = None, **kwargs):
        ...

    @classmethod
    def from_conf(cls, conf: ConfType) -> Structive_:
        raise NotImplementedError
