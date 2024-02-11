from dataclasses import dataclass

from src.constants import LangData


class InvalidPathException(Exception):
    pass


class InvalidYamlException(Exception):
    def __init__(self, *args: str):
        self.args = args or tuple()

    @property
    def reason(self) -> str:
        return ''.join(self.args)


@dataclass
class Messages:
    FORMING_KEYS_TOGETHER = f'{LangData.FORMING_KEYS} cannot occur together'
    NO_FORMING_KEY = f'One of the following keys must appear: {LangData.FORMING_KEYS}'  # TODO: Rethink if needed
    LACK_OF_REQUIRED_FIELD = '%s has no required %s field'
    NOT_DEFINED = '%s is not defined'
