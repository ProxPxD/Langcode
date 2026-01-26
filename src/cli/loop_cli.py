from argparse import ArgumentParser, SUPPRESS, _SubParsersAction

from src.cli.cli import CLI
from src.cli.keywords import run


class LoopCLI(CLI):
    @property
    def parser(self) -> ArgumentParser:
        parser = ArgumentParser()
        cmd = parser.add_subparsers(dest=run.CMD)
        self._create_cmd_section(cmd)
        return parser

    def _create_cmd_section(self, cmd: _SubParsersAction) -> None:
        self._create_cmd_create_section(cmd)
        self._create_cmd_context_section(cmd)

    def _create_cmd_create_section(self, cmd: _SubParsersAction) -> None:
        create = cmd.add_parser(run.CREATE, aliases=run.create.ALIASES)
        create.add_argument(run.create.CAT)
        create.add_argument(run.create.ARGS, nargs='*', help=SUPPRESS)
        create.epilog = (
            f'Bare flags (order-independent):\n'
            f'  {run.create.coords.UNDER}    Specify one category the new one is under\n'
            f'  {run.create.coords.OVER}     Specify any number of categories the new one spreads over\n'
        )

    def _create_cmd_context_section(self, cmd: _SubParsersAction) -> None:
        context = cmd.add_parser(run.CONTEXT)
        context.add_argument(run.context.DIRECTION, choices=[])
        context.add_argument(*run.context.SET_ALIASES)
        context.add_argument(*run.context.OUT_ALIASES)
