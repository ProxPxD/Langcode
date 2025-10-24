from _pytest.outcomes import fail

from src.logic.blocks.node import N
from src.logic.constants import log
from src.logic.db import GDM
from src.logic.lcm import LCM
from src.logic.main import lcm
from testing.core import TCG


class GenTCG(TCG):
    ...



def test():
    lcm = LCM(log=log)
    N.set_prefix('http://langcode/test/')

    woman = N(name='woman')
    name = N(name='name')
    woman.name = name
    if woman.name[0] != name:
        fail('Wrong result')