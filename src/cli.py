import logging
import shlex
import sys
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass

import pydash as _
from pydash import chain as c


@dataclass(frozen=True)
class Modes:
    run: str = 'run'
    rdf: str = 'rdf'
    load: str = 'load'


class CLI:

    def __init__(self):
        ...

    def parse(self, args: list[str] | str = None) -> Namespace:
        args = _.apply_if(args, shlex.split, _.is_string) or sys.argv[1:]
        args = _.flat_map(args, c().split('\xa0'))
        if len(args) == 0: # TODO potentially edit for loop
            self.parser.print_help()
            exit(0)  # change
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

        sub = parser.add_subparsers(dest='cmd', required=True)
        sub = _.flow(self._add_rdf_subcmd, self._add_run_subcmd, self._add_load_subcmd)(sub)
        return parser

    def _add_run_subcmd(self, sub: ArgumentParser) -> ArgumentParser:
        p_run = sub.add_parser('run', help='Enter main loop')
        return sub

    def _add_rdf_subcmd(self, sub: ArgumentParser) -> ArgumentParser:
        p_rdf = sub.add_parser('rdf', help='Run an RDF query')
        p_rdf.add_argument('query', type=str, help='RDF query to execute')
        return sub

    def _add_load_subcmd(self, sub: ArgumentParser) -> ArgumentParser:
        p_load = sub.add_parser('load', help='Run an RDF query')
        p_load.add_argument('file', type=str, help='File to load')  # TODO: Lasu multajn bazojn
        return sub
