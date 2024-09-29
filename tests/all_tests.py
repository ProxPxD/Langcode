import importlib
import inspect
import re
import unittest
from itertools import chain
from pathlib import Path
from typing import Iterable
from unittest.case import SkipTest

from abstractTest import AbstractTest

all_tests = []


def get_files_at_nth_level(path: Path | str, branching_level: int, name_regex: str):
    path = Path(__file__).parent / path if isinstance(path, str) else path
    to_enter = list(path.iterdir())
    while branching_level > 1:
        curr_to_enter = to_enter[:]
        to_enter = []
        for directory in curr_to_enter:
            to_enter.extend(directory.iterdir())
        branching_level -= 1

    result = [file for file in to_enter if re.search(name_regex, file.name)]
    return result


def get_module_path_from_file(file: Path, branching_level: int = 0) -> str:
    module_path_parts = file.parts[-(branching_level+1):]
    module_path = '.'.join(module_path_parts).removesuffix('.py')
    return module_path


def load_module_from_path(path: str) -> Iterable[tuple[str, ...]]:
    try:
        module = importlib.import_module(path)
        return inspect.getmembers(module, inspect.isclass)
    except Exception as e:
        return [(path, e)]


def get_tests_from_dir(dir_name: str = None, name_pattern: str = None, *, branching_level=1):
    if not dir_name:
        return all_tests

    is_matching_pattern = re.compile(name_pattern).search if name_pattern else lambda x: True
    test_files = get_files_at_nth_level(dir_name, branching_level, r'[^__pycache__]')
    for file in test_files:
        module_path = get_module_path_from_file(file, branching_level)
        for name, test_class in load_module_from_path(module_path):
            if module_path == name:  # TODO: won't work with two words CamelCase
                is_matching_pattern = re.compile(name_pattern.lower()).search if name_pattern else lambda x: False
                if is_matching_pattern(name):
                    raise ValueError(f'Could not load {name}') from test_class

            elif name.endswith('Test') and is_matching_pattern(name):
                yield test_class


def run_tests(to_runs: Iterable):
    failure, errors, total, skipped = 0, 0, 0, 0
    for test_class in to_runs:
        test = test_class()
        unittest.main(module=test, exit=False)

        if test_class is not SkipTest:
            failure += test.failure
            errors += test.errors
            total += test.total
        else:
            skipped += 1  # test.skipped

    print()
    print('#' * (2 * AbstractTest.half_sep_length))
    print('Total test statistics:')
    AbstractTest.print_statistics(failure, errors, skipped, total)


if __name__ == '__main__':
    name_pattern = '[WT]hen'
    tests = chain(
        get_tests_from_dir('feature_tests', name_pattern, branching_level=2),
        # get_tests_from_dir('test_cases', name_pattern, branching_level=1),
    )
    run_tests(tests)
