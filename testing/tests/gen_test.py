import logging
import subprocess
from dataclasses import dataclass
from time import sleep
from typing import Any

import pytest
from _pytest.fixtures import SubRequest, FixtureRequest
from _pytest.outcomes import fail

from src.logic.blocks.node import N
from src.logic.constants import rdf_dev_log
from src.logic.db import GDM
from src.logic.lcm import LCM
from testing.consts import PREFIX, KEEP_GRAPH_FLAG, KEEP_GRAPH_OPT
from testing.core import TCG


@pytest.fixture(scope='session', autouse=True)  # function/class/module/session
def run_container():
    container = 'graphdb'
    kws = dict(capture_output=True, text=True, shell=True)
    is_running = subprocess.run("podman ps --filter name=" + container + " --format '{{.Names}}'", **kws).stdout.strip()
    if not is_running:
        logging.debug(f'Starting {container}')
        subprocess.run(f'podman start {container}', **kws)
        exists = False
        while not exists:
            sleep(0.1)
            exists = bool(subprocess.run('podman ps --filter name=' + container + ' --format {{.Names}}', **kws).stdout.strip())
    yield
    if not is_running:
        logging.debug(f'Stopping {container}')
        subprocess.run(f'podman stop {container}', **kws)


@pytest.fixture(scope='function', autouse=True)
def test_fixture(request: FixtureRequest):
    N.set_prefix(PREFIX)
    yield
    keep = request.config.getoption(KEEP_GRAPH_OPT)
    if not keep:
        GDM.curr().raw_query(f'''
            DELETE {{ ?s ?p ?o . }} WHERE {{
                ?s ?p ?o .
                FILTER(
                    STRSTARTS(STR(?s), "{PREFIX}") ||
                    STRSTARTS(STR(?p), "{PREFIX}") ||
                    STRSTARTS(STR(?o), "{PREFIX}")
                )
            }};
        ''')

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
                conf='''yaml
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
