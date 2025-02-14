import json

import yaml

from loaders import FileLoader

loader = [
    YamlLoader := FileLoader(yaml.safe_load, ('.yaml', '.yml')),
    JsonLoader := FileLoader(json.load, '.json'),
    # TODO: toml loader
]
