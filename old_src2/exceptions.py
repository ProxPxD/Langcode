from dataclasses import dataclass
from typing import Callable
import pydash as _


class LangCodeException(Exception):
    pass


class InvalidPathException(LangCodeException):
    pass


class InvalidYamlException(LangCodeException):
    def __init__(self, *args: str):
        self.args = args or tuple()

    @property
    def reason(self) -> str:
        return ''.join(self.args)


class NoConditionAppliesException(LangCodeException):
    pass


class IDynamicMessageException(Exception):
    _make_msg: Callable[[...], str] = lambda *args, **kwargs: ''

    def __init__(self, *args, **kwargs):
        self.msg = self._make_msg(*args, **kwargs)
        super().__init__(*args, **kwargs)


class AmbiguousNodeException(LangCodeException):
    _make_msg = lambda *args, **kwargs: f'There exist more than one node ({args = }, {kwargs = })'


class DoNotExistException(LangCodeException):
    _make_msg = lambda *args, **kwargs: f'Node has not been found ({args = }, {kwargs = })'


class AmbiguousSubFeaturesException(LangCodeException):
    def __init__(self, feature, kind, *args):
        self.kind = kind
        self.args = (feature,) + args


class ConflictingKeysException(LangCodeException):
    pass


class CannotCreatePropertyException(LangCodeException, IDynamicMessageException):
    _make_msg = lambda prop_name: f'Property cannot be set named {prop_name}'


class PropertyNotFound(LangCodeException, IDynamicMessageException):
    _make_msg = lambda node, prop_name: f'{node:kind} {node:label} {node:name} has no property {prop_name}'



@dataclass
class Messages:
    FORMING_KEYS_TOGETHER = '{SimpleTerms.FORMING_KEYS} cannot occur together'
    NO_FORMING_KEY = 'One of the following keys must appear: {SimpleTerms.FORMING_KEYS}'
    LACK_OF_REQUIRED_FIELD = '%s has no required %s field'
    NOT_DEFINED = '%s is not defined'
