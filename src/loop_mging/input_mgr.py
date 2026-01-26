from typing import Any

from src.loop_mging.input_processing import InputProcessor
from src.cli.loop_cli import LoopCLI


class InputMgr:
    def __init__(self):
        self.loop_cli = LoopCLI()
        self.input_processor = InputProcessor()

    def parse(self) -> Any:  # context
        parsed = self.loop_cli.parse(input())
        _ = self.input_processor.process(parsed)
        return _
