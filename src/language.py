from typing import Any


class IName:
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self._name: str = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        raise NotImplementedError


class IKind:
    def __init__(self, kind: str, **kwargs):
        super().__init__(**kwargs)
        self._kind: str = kind

    @property
    def kind(self) -> str:
        return self._kind

    @kind.setter
    def kind(self, kind: str) -> None:
        raise NotImplementedError  # probably never allowed


class Langel(IName, IKind):
    def __init__(self, name: str, kind: str):
        super().__init__(name=name, kind=kind)

    def __getitem__(self, key) -> Any:
        raise NotImplementedError


class Language(IName):
    def __init__(self, name: str):
        super().__init__(name=name)

