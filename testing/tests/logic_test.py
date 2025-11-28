from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any, Collection, Iterable, Generator

import pytest
import yaml
from _pytest.outcomes import fail

from src.logic.blocks.node import N
from src.logic.conf.schema.top import Conf
from src.logic.consts.db import rdf_dev_log
from src.logic.consts.keywords import IS, STRUCTANT, SUB, EX
from src.logic.lcm import LCM
from testing.core import TCG
import pydash as _
from pydash import chain as c

from testing.core.utils import apply


SYSTEM_PATH = Path(__file__).parent
TMP_DIR = SYSTEM_PATH / 'tmp'
TEST_CONF = TMP_DIR / 'conf.yaml'


StrS = str | Collection[str]

def to_list(pos_str) -> list[str]:
    if isinstance(pos_str, str): return [pos_str]
    if isinstance(pos_str, (Collection, Iterable, Generator)): return list(pos_str)
    raise ValueError(f'Unhandled type: {type(pos_str)}')

@apply(list)
def gen_triples(s: StrS, v: StrS, o: StrS, *, reverse: str | bool = None) -> Generator[Collection[str], None, None]:
    svo = _.map_((s, v, o), to_list)
    for s_, v_, o_ in product(*svo):
        yield s_, v_, o_
    match reverse:
        case True: yield from gen_triples(o, v, s, reverse=False)
        case str(): yield from gen_triples(o, reverse, s, reverse=False)
        case _: pass

@dataclass
class TC:
    descr: str
    conf: Conf
    e_triples: Collection[Collection[str]]
    ie_triples: Collection[Collection[str]] = frozenset()
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
                conf=Conf(
                    structants=f'''
                        {(name := 'empty')}: 
                        '''
                ),
                e_triples=(
                    (name, IS, STRUCTANT),
                ),
            ),
            TC(
                descr='Substructant',
                tags={'sub/def', 'id'},
                conf=Conf(
                    structants=(binary_category := f'''
                    {(category := 'category')}:
                        {SUB}:
                            - {(choice1 := 'choice1')}
                            - {(choice2 := 'choice2')} 
                    ''')
                ),
                e_triples=(
                    *gen_triples([category, choice1, choice2], IS, STRUCTANT),
                    *gen_triples([choice1, choice2], IS, category, reverse=EX),
                ),
            ),
            TC(
                descr='Substructant Setting with Category',
                tags={'sub/def', 'sub/set/parent', 'id'},
                conf=Conf(
                    structants=f'''
                                {binary_category}
                                {(word := 'word')}:
                                    {category}: {choice1}
                                '''
                ),
                e_triples=(
                    (word, IS, STRUCTANT),
                    (word, IS, choice1)
                ),
                ie_triples=(  # TODO: It assumes for now nontransitive checks in e_triples
                    (word, IS, category),
                ),
            ),
            TC(
                descr='Substructant Setting without Category',
                tags={'sub/def', 'sub/set/direct', 'id'},
                conf=Conf(
                    structants=f'''
                    {binary_category}
                    {(word := 'word')}:
                        {choice1}: {True}
                    '''
                ),
                e_triples=(
                    (word, IS, STRUCTANT),
                    (word, IS, choice1)
                ),
                ie_triples=(  # TODO: It assumes for now nontransitive checks in e_triples
                    (word, IS, category),
                ),
            ),
        ]

    @classmethod
    def map(cls, tc):
        return tc

@LogicTCG.parametrize('tc')
def test(tc: Tc | TC):
    with open(TEST_CONF, 'w') as f:
        yaml.dump(tc.conf.model_dump(), f, default_flow_style=False, allow_unicode=True)

    lcm = LCM(log=rdf_dev_log)
    woman = N(name='woman')
    name = N(name='name')
    woman.name = name
    if woman.name[0] != name:
        fail('Wrong result')
    pytest.fail('Nefiniĝita')
