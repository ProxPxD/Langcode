from src.designing.logic.constants import USER, PASSWORD, URI, DB
from src.designing.logic.gdm import LoginData
from src.designing.logic.lcm import LCM

log = LoginData(uri=URI, user=USER, password=PASSWORD, database=DB)

lcm = LCM(log=log)
