from __future__ import annotations

import inspect
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Type, Iterable
import yaml

from src.morphemes import SimpleMorphemeND, Side, By, At, By, Side
from tests.abstractTest import AbstractTest


class OrthographyTest(AbstractTest):
    is_generated = False
    config_dir = Path(__file__).parent / 'configs'
    minimal_langs_path = config_dir / 'minimal_langs_path.yaml'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_generated:
            self.is_generated = True

    @classmethod
    def read_yaml(cls, path) -> dict:
        with open(path, 'r') as file:
            languages = yaml.safe_load(file)
        return languages

    def test_minimal_langs(self):
        pass