from src.designing.logic.gdm import GDM, Neo4jGDM, LoginData
from src.designing.logic.ict import ICT
from src.designing.logic.sci import SCI


class LCM:
    """
    Lang Code Manager
    """
    def __init__(self, *, log: LoginData):
        self.gdm: GDM = Neo4jGDM(log)
        self.ict: ICT = ICT()
        self.sci: SCI = SCI()

