from pathlib import Path
from typing import Callable, Sequence, Optional, TextIO

import pydash as _


class IPathable:
    def __init__(self, path: str | Path, *args, **kwargs):
        self._path: Path = path
        super().__init__(*args, **kwargs)

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, path: str | Path):
        self._path = Path(path)


class FileLoader:
    def __init__(self,
            load: Callable[[str | Path | TextIO], dict],
            suffix: str | Sequence = None,
            is_loadable: Callable[[Path | str], bool] = _.constant(True),
    ):
        self._load = load
        self._suffixes = _.to_list(suffix, False)
        is_suffixed = lambda path: not self._suffixes or path.suffix in self._suffixes
        self.is_loadable = lambda path: is_suffixed(path) and is_loadable(path)

    def load(self, path: str | Path | TextIO) -> dict:
        try:
            if _.is_dict(result := self._load(path)):
                return result
        except Exception:
            pass
        with open(path) as f:
            return self._load(f)


class DirLoader(IPathable):
    def __init__(self, *file_loaders: FileLoader, **kwargs):
        self.file_loaders = file_loaders
        super().__init__(**kwargs)

    def load(self, path: str | Path = None) -> dict:
        self.path = path or self.path
        return self._load(self.path)

    def _load(self, path: Path) -> dict:
        if path.is_file() and (loader := self._pick_file_loader(path)):
            return loader.load(path)
        elif path.is_dir():
            return {
                subpath.stem: content
                for subpath in path.iterdir()
                if (content := self._load(subpath)) is not None
            }

    def _pick_file_loader(self, path: Path) -> Optional[FileLoader]:
        return next((file_loader for file_loader in self.file_loaders if file_loader.is_loadable(path)), None)


