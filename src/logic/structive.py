from types import NoneType
from typing import Optional

from src.logic.gdm import GDM


class Structive:
    def __new__(cls, conf: dict = None, lcid: str = None, **kwargs):
        if not isinstance(lcid, (NoneType, str)):
            raise ValueError('LCID has to be string')

        gdm = GDM.curr()

        if lcid and (structive_eh := gdm.find(lcid=lcid, raises=False)):
            return structive_eh
        # TODO: logic!
        return super().__new__(cls)

    def __init__(self, conf: dict = None, lcid: str = None, **kwargs):
        super().__init__(**kwargs)
        self._gdm = GDM.curr()
        self._lcid: Optional[str] = lcid
        self._source = Structive(conf.get('source'))
        self._target = ...

    @property
    def lcid(self) -> Optional[str]:
        return self._lcid

