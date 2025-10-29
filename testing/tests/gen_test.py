import logging
import subprocess
from time import sleep

import pytest
from _pytest.outcomes import fail

from src.logic.blocks.node import N
from src.logic.constants import rdf_dev_log
from src.logic.lcm import LCM
from testing.core import TCG


class GenTCG(TCG):
    ...


@pytest.fixture(scope='session', autouse=True)  # function/class/module/session
def run_container():
    container = 'graphdb'
    kws = dict(capture_output=True, text=True, shell=True)
    is_running = subprocess.run("podman ps --filter name=" + container + " --format '{{.Names}}'", **kws).stdout.strip()
    if not is_running:
        logging.info(f'Starting {container}')
        subprocess.run(f'podman start {container}', **kws)
        exists = False
        while not exists:
            sleep(1)
            exists = bool(subprocess.run('podman ps --filter name=' + container + ' --format {{.Names}}', **kws).stdout.strip())
    yield
    if not is_running:
        logging.info(f'Stopping {container}')
        subprocess.run(f'podman stop {container}', **kws)

@pytest.fixture(scope='function', autouse=True)
def _():
    logging.info("Setup")
    yield
    logging.info("Teardown")


def test():
    logs = logging.getLogger('#TODO')
    lcm = LCM(log=rdf_dev_log)
    N.set_prefix('http://langcode/test/')

    woman = N(name='woman')
    name = N(name='name')
    woman.name = name
    if woman.name[0] != name:
        fail('Wrong result')