import unittest
from typing import Iterable

from abstractTest import AbstractTest
from test_cases.loading_test import LoadingTest
from tests.test_cases.test_correctness_test import TestCorrectnessTest

all_tests = [
    TestCorrectnessTest,
    LoadingTest,
    #BasicMorphemeTest,
]


def get_tests_from_dir(dir_name: str = None):
    if not dir_name:
        return all_tests
    raise NotImplementedError


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
    run_tests(get_tests_from_dir())
