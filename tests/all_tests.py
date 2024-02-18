import importlib
import inspect
import re
import unittest
from pathlib import Path
from typing import Iterable, Optional

from abstractTest import AbstractTest

all_tests = []


def get_tests_from_dir(dir_name: str = None, name_pattern: str = None):
    if not dir_name:
        return all_tests
    test_dir_path = Path(__file__).parent / dir_name
    for path in test_dir_path.iterdir():
        module = importlib.import_module(f'{dir_name}.{path.stem}')
        for name, test_class in inspect.getmembers(module, inspect.isclass):
            if name.endswith('Test'):
                if name_pattern is None or re.match(name_pattern, name):
                    yield test_class


def run_tests(to_runs: Iterable):
    failure, errors, total, skipped = 0, 0, 0, 0
    for test_class in to_runs:
        test = test_class()
        unittest.main(module=test, exit=False)

        failure += test.failure
        errors += test.errors
        total += test.total
        skipped += test.skipped

    print()
    print('#' * (2 * AbstractTest.half_sep_length))
    print('Total test statistics:')
    AbstractTest.print_statistics(failure, errors, skipped, total)


if __name__ == '__main__':
    run_tests(get_tests_from_dir('test_cases'))
