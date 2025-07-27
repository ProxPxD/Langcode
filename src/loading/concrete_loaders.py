import json

import yaml

from abstract_loaders import FileLoader, DirLoader

basic_file_loaders = [
    yaml_file_loader := FileLoader(yaml.safe_load, ('.yaml', '.yml')),
    json_file_loader := FileLoader(json.load, '.json'),
    # TODO: toml loader
]

basic_loaders = [
    yaml_loader := DirLoader(yaml_file_loader),
    json_loader := DirLoader(json_file_loader),
]
GenLoader = DirLoader(*basic_file_loaders)
