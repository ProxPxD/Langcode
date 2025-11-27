import logging
import subprocess
from time import sleep

import pytest
from _pytest.fixtures import FixtureRequest

from src.logic.blocks.node import N
from src.logic.db import GDM
from testing.consts import KEEP_GRAPH_FLAG, URI_PREFIX, KEEP_GRAPH_OPT


def pytest_addoption(parser):
    parser.addoption(KEEP_GRAPH_FLAG, action='store_true', help='Ne forigu la grafon')


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
    N.set_prefix(URI_PREFIX)
    yield
    keep = request.config.getoption(KEEP_GRAPH_OPT)
    if not keep:
        GDM.curr().raw_query(f'''
            DELETE {{ ?s ?p ?o . }} WHERE {{
                ?s ?p ?o .
                FILTER(
                    STRSTARTS(STR(?s), "{URI_PREFIX}") ||
                    STRSTARTS(STR(?p), "{URI_PREFIX}") ||
                    STRSTARTS(STR(?o), "{URI_PREFIX}")
                )
            }};
        ''')
