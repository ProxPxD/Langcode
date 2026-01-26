import logging
from dataclasses import dataclass
from typing import Any

import pytest
from _pytest.outcomes import fail

from src.logic.blocks.node import N
from src.logic.consts.db import rdf_dev_log
from src.lcm import LCM
from testing.core import TCG


@pytest.fixture(scope='module', autouse=True)
def module_fixture():
    logs = logging.getLogger('#TODO')
    lcm = LCM(log=rdf_dev_log)
    yield lcm


@pytest.fixture(scope='function', autouse=True)
def _():
    logging.debug("Setup")
    yield
    logging.debug("Teardown")


@dataclass
class TC:
    conf: Any

@dataclass
class Tc:
    ...


class GenTCG(TCG):
    @classmethod
    def generate_tcs(cls) -> list:
        return [
            TC(
                conf='''
                test: sa
                ''',
            ),
        ]


@GenTCG.parametrize('tc')
def test(tc: Tc | TC):
    woman = N(name='woman')
    name = N(name='name')
    woman.name = name
    if woman.name[0] != name:
        fail('Wrong result')
