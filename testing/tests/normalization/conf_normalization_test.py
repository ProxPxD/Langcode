from collections import namedtuple

from testing.core.TCG import TCG


class ConfTCG(TCG):
    tc = namedtuple('tc', ['name', 'descr', ''])
    tcs = [

    ]


ConfTCG.parametrize('name', 'tc')
def test(name, tc):
    raise NotImplementedError