from dataclasses import dataclass
from typing import Any, Collection

from _pytest.outcomes import fail

from src.logic.blocks.node import N
from src.logic.consts.keywords import IS, STRUCTANT
from testing.core import TCG


@dataclass
class TC:
    descr: str
    conf: Any
    e_triples: dict[str, tuple[str, str, str]]
    tags: Collection[str] = frozenset()

@dataclass
class Tc:
    ...


class LogicTCG(TCG):
    @classmethod
    def generate_tcs(cls) -> list:
        return [
            TC(
                descr='Empty Structant',
                tags={'empty', 'id'},
                conf=f'''
                {(name:='empty')}: 
                ''',
                e_triples={
                  'exist': (name, IS, STRUCTANT),
                },
            ),
        ]


@LogicTCG.parametrize('tc')
def test(tc: Tc | TC):
    woman = N(name='woman')
    name = N(name='name')
    woman.name = name
    if woman.name[0] != name:
        fail('Wrong result')
