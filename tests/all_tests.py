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


def get_files_at_nth_level(dir: Path, branching_level):
    to_enter = list(dir.iterdir())
    while branching_level > 1:
        curr_to_enter = to_enter[:]
        to_enter = []
        for dir in curr_to_enter:
            to_enter.extend(dir.iterdir())
        branching_level -= 1
    return to_enter


def get_tests_from_dir(dir_name: str = None, name_pattern: str = None, *, branching_level=1):
    if not dir_name:
        return all_tests

    test_dir_path = Path(__file__).parent / dir_name
    test_files = get_files_at_nth_level(test_dir_path, branching_level)
    test_files = [file for file in test_files if '__pycache__' not in file.name]
    for file in test_files:
        module_path_parts = file.parts[-(branching_level+1):]
        module_path = '.'.join(module_path_parts).removesuffix('.py')
        module = importlib.import_module(module_path)
        is_matching_pattern = re.compile(name_pattern).match

        for name, test_class in inspect.getmembers(module, inspect.isclass):
            if name.endswith('Test'):
                if name_pattern is None or is_matching_pattern(name):
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
    name_pattern = 'Condition'
    tests = chain(
        get_tests_from_dir('feature_tests', name_pattern, branching_level=2),
        get_tests_from_dir('test_cases', name_pattern, branching_level=1),
    )
    run_tests(tests)
