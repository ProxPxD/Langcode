import inspect
import unittest
from pathlib import Path
from typing import Iterable
import importlib

from abstractTest import AbstractTest
from test_cases.loading_test import LoadingTest
from tests.test_cases.test_properties_correctness_test import TestPropertiesCorrectnessTest
from iteration_utilities import starfilter, flatten, nth

all_tests = [
    # TestPropertiesCorrectnessTest,
    # LoadingTest,
]


def get_tests_from_dir(dir_name: str = None):
    if not dir_name:
        return all_tests
    test_dir_path = Path(__file__).parent / dir_name
    for path in test_dir_path.iterdir():
        module = importlib.import_module(f'{dir_name}.{path.stem}')
        for name, test_class in inspect.getmembers(module, inspect.isclass):
            if name.endswith('Test'):
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
