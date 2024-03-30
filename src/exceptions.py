from dataclasses import dataclass


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


class AmbiguousNameException(LangCodeException):
    def __init__(self, name, kind, *args, **kwargs):
        self.name = name
        self.kind = kind
        self.args = (f'There exist more than one {kind} {name} (Additional: {kwargs})', ) + args


class DoNotExistException(LangCodeException):
    def __init__(self, name, kind=None, *args, **kwargs):
        self.name = name
        self.kind = kind
        self.args = (f'{kind} {name} has not been found (Additional: {kwargs})', ) + args


class AmbiguousSubFeaturesException(LangCodeException):
    def __init__(self, feature, kind, *args):
        self.kind = kind
        self.args = (feature,) + args


@dataclass
class Messages:
    FORMING_KEYS_TOGETHER = '{SimpleTerms.FORMING_KEYS} cannot occur together'
    NO_FORMING_KEY = 'One of the following keys must appear: {SimpleTerms.FORMING_KEYS}'
    LACK_OF_REQUIRED_FIELD = '%s has no required %s field'
    NOT_DEFINED = '%s is not defined'
