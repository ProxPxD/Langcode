from src.logic.conf.fcn import FCN
from src.logic.db import GDM, LoginData
from src.logic.conf.ici import ICI
from src.logic.sci import SCI


class LCM:
    """
    Lang Code Manager
    """
    def __init__(self, *, log: LoginData):
        self.gdm: GDM = GDM(log)
        self.fcn = FCN()
        self.sci: SCI = SCI()

