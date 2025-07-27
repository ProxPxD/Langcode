from src.logic.constants import USER, PASSWORD, URI, DB
from src.logic.gdm import LoginData
from src.logic.lcm import LCM

log = LoginData(uri=URI, user=USER, password=PASSWORD, database=DB)

lcm = LCM(log=log)
