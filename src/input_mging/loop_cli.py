from argparse import ArgumentParser, SUPPRESS, _SubParsersAction

import keywords.run as run
from src.input_mging.cli import CLI


class LoopCLI(CLI):
    def parser(self) -> ArgumentParser:
        parser = ArgumentParser()
        cmd = parser.add_subparsers(dest=run.CMD)
        self._create_cmd_section(cmd)
        return parser

    def _create_cmd_section(self, cmd: _SubParsersAction):
        self._create_cmd_create_section(cmd)

    def _create_cmd_create_section(self, cmd: _SubParsersAction):
        create = cmd.add_parser(run.CREATE, aliases=run.create.ALIASES)
        create.add_argument(run.create.CAT)
        create.add_argument(run.create.ARGS, nargs='+', help=SUPPRESS)
        create.epilog = (
            f'Bare flags (order-independent):\n'
            f'  {run.create.coords.UNDER}    Specify one category the new one is under\n'
            f'  {run.create.coords.OVER}     Specify any number of categories the new one spreads over\n'
        )
