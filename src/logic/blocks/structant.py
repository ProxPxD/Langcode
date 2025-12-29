from __future__ import annotations

from src.logic.blocks.node import N
from src.logic.conf.schema.structant import Structant as StructantConf
from src.logic.db import GDM


class Structant:
    structants: dict[str, Structant] = {}

    def __new__(cls, uid: str = None, *args, **kwargs):
        obj = super().__new__(cls)
        return obj

    def __init__(self, *,
            uid: str = None,
            # src,
        ):
        self.self = N(uid=uid)

    @property
    def gdm(self) -> GDM:
        return self.self.gdm

    @property
    def uid(self) -> str:
        return self.self.uid

    @property
    def uri(self) -> str:
        return self.self.uri

    @classmethod
    def fromconf(cls, conf: StructantConf) -> Structant:
        ...

S = Structant

