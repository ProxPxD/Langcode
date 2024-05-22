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


class IDynamicMessageException(Exception):
    _make_msg: Callable[[...], str] = lambda *args, **kwargs: ''

    def __init__(self, *args, **kwargs):
        self.msg = self._make_msg(*args, **kwargs)
        super().__init__(*args, **kwargs)


class INameKindException(IDynamicMessageException):
     def __init__(self, name, kind, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.kind = kind


class AmbiguousNameException(LangCodeException, INameKindException):
    _make_msg = lambda name, kind, *args, **kwargs: f'There exist more than one {kind} {name}' + (f' (Additional: {kwargs})' if kwargs else '')


class DoNotExistException(LangCodeException, INameKindException):
    _make_msg = lambda name, kind, *args, **kwargs: f'{kind} {name} has not been found' + (f' (Additional: {kwargs})' if kwargs else '')


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
