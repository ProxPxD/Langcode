import logging
import logging
import shlex
import sys
from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace

import pydash as _
from pydash import chain as c


class CLI(ABC):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
    @abstractmethod
    def parser(self) -> ArgumentParser:
        ...
