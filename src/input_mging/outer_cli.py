import logging
import shlex
import sys
from argparse import ArgumentParser, Namespace, _SubParsersAction
from dataclasses import dataclass

import pydash as _
from pydash import chain as c

from src.input_mging.cli import CLI


@dataclass(frozen=True)
class Modes:
    start: str = 'start'
    query: str = 'query'
    load: str = 'load'


class OuterCLI(CLI):
    @property
    def parser(self) -> ArgumentParser:
        parser = ArgumentParser(
            prog='LangCode',
            description='Program for Coding Languages in',
            epilog=''
        )

        sub = parser.add_subparsers(dest='cmd', required=True)
        self._add_loop_subparser(sub)
        self._add_query_subparser(sub)
        self._add_load_subcmd(sub)
        return parser

    def _add_loop_subparser(self, sub: _SubParsersAction) -> _SubParsersAction:
        p_run = sub.add_parser(Modes.start, help='Enter main loop')
        return sub

    def _add_query_subparser(self, sub: _SubParsersAction) -> _SubParsersAction:
        p_rdf = sub.add_parser(Modes.query, help='Run an RDF query')
        p_rdf.add_argument(Modes.query, type=str, help='RDF query to execute')
        return sub

    def _add_load_subcmd(self, sub: _SubParsersAction) -> _SubParsersAction:
        p_load = sub.add_parser('load', help='Run an RDF query')
        p_load.add_argument('file', type=str, help='File to load')  # TODO: Lasu multajn bazojn
        return sub
