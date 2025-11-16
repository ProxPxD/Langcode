import logging
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass

import pydash as _
from pydash import chain as c


@dataclass(frozen=True)
class Modes:
    run: str = 'run'
    rdf: str = 'rdf'


class CLI:

    def __init__(self):
        ...

    def parse(self, args: list[str] | str = None) -> Namespace:
        if len(args) == 0: # TODO potentially edit for loop
            self.parser.print_help()
            exit(0)  # change
        args = [a for arg in args for a in arg.split('\xa0')]
        parsed = self.parser.parse_args(args)
        # parsed, remaining = self.parser.parse_known_args(args)
        # parsed.args += remaining

        logging.debug(f'Parsed: {parsed}')
        return parsed

    @property
    def parser(self) -> ArgumentParser:
        parser = ArgumentParser(
            prog='LangCode',
            description='Program for Coding Languages in',
            epilog=''
        )

        # parser = _.flow()(parser)
        sub = parser.add_subparsers(dest='cmd', required=True)
        sub = _.flow(self._add_rdf_subcmd, self._add_run_subcmd)(sub)
        return parser

    def _add_run_subcmd(self, sub: ArgumentParser) -> ArgumentParser:
        p_run = sub.add_parser('run', help='Enter main loop')
        return sub

    def _add_rdf_subcmd(self, sub: ArgumentParser) -> ArgumentParser:
        p_rdf = sub.add_parser('rdf', help='Run an RDF query')
        p_rdf.add_argument('query', type=str, help='RDF query to execute')
        return sub
