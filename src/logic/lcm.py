import logging
from argparse import Namespace

from src.cli import CLI, Modes
from src.logic.conf.fcn import FCN
from src.logic.db import GDM, LoginData
from src.logic.sci import SCI


class LCM:
    """
    Lang Code Manager
    """
    def __init__(self, *, log: LoginData):
        self.cli = CLI()
        self.gdm: GDM = GDM(log)
        self.fcn = FCN()
        self.sci: SCI = SCI()

    def run(self) -> None:
        parsed: Namespace = self.cli.parse()  # TODO: add a proper application context
        match parsed.cmd:
            case Modes.run: self.run_loop(parsed.run)
            case Modes.rdf: self.run_rdf(parsed.rdf)
            case _: raise ValueError(f'Unrecognized cmd: {parsed.cmd}')

    def run_loop(self, run_parsed) -> None:
        logging.debug('Run Loop')
        ...
        # while self.context.loop:
        #     self.run_single(shlex.split(input()))

    def run_rdf(self, rdf_parsed) -> None:
        logging.debug('Run RDF')
        res = self.gdm.raw_query(rdf_parsed.query)
        print(res)
