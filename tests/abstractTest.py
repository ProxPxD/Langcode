import abc
import unittest
from dataclasses import dataclass
from typing import Iterable

from colorama import Fore, Style


@dataclass(frozen=False)
class Stat:
    label: str
    status: str = ''
    color: str | int = ''
    n_tests: int = 0
    last_counted = None

    def lower(self) -> str:
        return self.label.lower()

    @property
    def colored_status(self) -> str:
        return f'{self.color}{self.status}{Style.RESET_ALL}'

    def count(self, test) -> None:
        if self.is_test(test):
            self.inc(test)
        else:
            self.last_counted = None

    def inc(self, test) -> None:
        self.n_tests += 1
        self.last_counted = test

    def is_test(self, test) -> bool:
        return any(test == it_test for it_test, text in getattr(test.get_test_result(), self.lower()))

    def in_percentage(self, total: int) -> float:
        return 100 * self.n_tests / total

    @property
    def first_letter(self) -> str:
        return self.label[0]

    def format(self, *, total: int = None, short: bool = False, percentage: bool = False) -> str:
        numerical = f'{self.in_percentage(total):.1f}%' if percentage else str(self.n_tests)
        formatted = f'{numerical}{self.first_letter}' if short else f'{self.label}: {numerical}'
        return formatted


@dataclass(frozen=False)
class Statistics:
    total = Stat('Total')
    failures = Stat('Failures', 'FAIL', Fore.MAGENTA)
    errors = Stat('Errors', 'ERROR', Fore.RED)
    skipped = Stat('Skipped', 'SKIP', Fore.LIGHTYELLOW_EX)
    _passed = None

    @property
    def failed(self) -> Stat:
        return Stat('Failed', 'FAIL', Fore.LIGHTGREEN_EX, self.failures.n_tests + self.errors.n_tests)

    @property
    def total_run(self) -> Stat:
        return Stat('Total Run', 'Total', '', self.total.n_tests - self.skipped.n_tests)

    @property
    def passed(self) -> Stat:
        if not self._passed:
            self._passed = Stat('Passed', 'PASS', Fore.LIGHTGREEN_EX, self.total_run.n_tests - self.failed.n_tests)
        return self._passed

    @property
    def stats(self) -> tuple[Stat, ...]:
        return self.passed, *self.checkable_stats

    @property
    def checkable_stats(self) -> tuple[Stat, ...]:
        return self.failures, self.errors, self.skipped

    @property
    def printable_stats(self) -> tuple[Stat, ...]:
        return self.failed, self.failures, self.errors, self.passed, self.skipped

    def count(self, test):
        self.total.n_tests += 1
        for stat in self.checkable_stats:
            stat.count(test)
        if is_passed := not any(stat.last_counted for stat in self.checkable_stats):
            self.passed.inc(test)

    def get_last_status(self, *, colored: bool = False) -> str:
        return next(
            (stat.status if not colored else stat.colored_status for stat in self.stats if stat.last_counted),
            'WRONG UNIT TEST OUTCOME CHECKING! Investigate (possible incompatible with a python newer than 3.10)'
        )

    def is_test_in_state(self, test, state):
        return any(test == self for test, text in getattr(test.get_test_result, state.lower()))

    def format(self, *, short: bool = False, percentage: bool = False) -> str:
        if self.total.n_tests == 0:
            return 'There are no tests'

        formatteds = {stat.label: stat.format(total=self.total_run.n_tests, short=short, percentage=percentage) for stat in self.printable_stats}
        failed = formatteds[self.failed.label]
        failures = formatteds[self.failures.label]
        errors = formatteds[self.errors.label]
        passed = formatteds[self.passed.label]
        skipped = formatteds[self.skipped.label]

        first_part = f'{failed} ({failures}, {errors}), {passed}' if not short else f'({failures}, {errors}, {passed})'
        total_part = ((', ' if not short else '/') + self.total_run.format(short=short)) if not percentage else ''
        skipped_part = f'   ({skipped})' if self.skipped.n_tests else ''
        statistics_str = f'{first_part}{total_part}{skipped_part}'

        return statistics_str


class TestGenerator:
    @classmethod
    def generate(cls) -> Iterable[tuple]:
        yield NotImplementedError

    @classmethod
    def list(cls) -> list[tuple]:
        return list(cls.generate())


class AbstractTest(unittest.TestCase, abc.ABC):
    half_sep_length = 50
    currentResult = None
    status_distance = int(0.75 * 2*half_sep_length)

    test_stats = Statistics()

    @classmethod
    def print_sep_with_text(cls, text: str, sep: str = '*') -> None:
        with_sep_lines = sep * cls.half_sep_length + f' {text} ' + sep * cls.half_sep_length
        over_length = len(with_sep_lines) - cls.half_sep_length*2
        to_print = with_sep_lines[over_length//2 : -over_length//2]
        print(to_print)

    @classmethod
    def setUpClass(cls) -> None:
        cls.print_sep_with_text(f'Starting {cls._get_test_name()} tests!')

    def setUp(self) -> None:
        if not self.get_method_name().startswith('test_'):
            return
        super().setUp()
        print('- ', self.get_method_name())
        self.print_test_props()

    def print_test_props(self) -> None:
        method = getattr(self, self._testMethodName)
        props = getattr(method, 'props', {})
        for name, val in props.items():
            print(f'\t\t - {name}' + f': {val}')

    def tearDown(self) -> None:
        if not self.get_method_name().startswith('test_'):
            return
        super().tearDown()

        self.test_stats.count(self)

        test_printing_length = len(self.get_method_name()) + 5
        padding = self.status_distance - test_printing_length
        status = self.test_stats.get_last_status(colored=True)
        print(f'\t\tstatus: {" "*padding}{status}')

    def get_test_result(self):
        if hasattr(self._outcome, 'errors'):
            result = self._get_legacy_test_results()
        else:  # Python 3.11+
            result = self._outcome.result
        return result

    def _get_legacy_test_results(self):
        ''' Python 3.4 - 3.10  (These two methods have no side effects) '''
        result = self.defaultTestResult()
        self._feedErrorsToResult(result, self._outcome.errors)
        for test, reason in self._outcome.skipped:
            self._addSkip(result, test, reason)
        return result

    @classmethod
    def tearDownClass(cls) -> None:
        cls.print_statistics(percentage=False)

    @classmethod
    def print_statistics(cls, failure=None, errors=None, skipped=None, total=None, *, short=False, percentage=True):
        stats = Statistics()
        stats.total.n_tests = total or cls.test_stats.total.n_tests
        stats.failures.n_tests = failure or cls.test_stats.failures.n_tests
        stats.errors.n_tests = errors or cls.test_stats.errors.n_tests
        stats.skipped.n_tests = skipped or cls.test_stats.skipped.n_tests

        print(statistics_str := stats.format(short=short, percentage=percentage))
        return statistics_str

    def run(self, result: unittest.result.TestResult | None = ...) -> unittest.result.TestResult | None:
        self.currentResult = result
        unittest.TestCase.run(self, result)

    def get_method_name(self) -> str:
        return self.id().split('.')[-1]

    @classmethod
    def _get_test_name(cls) -> str:
        return cls.__name__.removesuffix('Test')

    def get_parameterized_methods_of_current_test(self, *method_nums) -> Iterable:
        if not method_nums:
            return iter([])

        method_name = self.get_method_name()
        method_prefix = f'{method_name}_'
        child_methods = [name for name in dir(self) if name.startswith(method_prefix)]

        if method_nums[0] is None:
            method_nums = range(len(child_methods))
        number_marks = (name.removeprefix(method_prefix).split('_')[0] for name in child_methods)
        zero_count = len(next((num for num in number_marks if all((ch == '0' for ch in num))), ''))

        method_prefixes = (f'{method_prefix}{str(i).zfill(zero_count)}' for i in method_nums)
        methods = (getattr(self, actual_name) for expected_prefix in method_prefixes for actual_name in child_methods
                   if actual_name.startswith(expected_prefix))
        return methods

    def run_current_test_with_params(self, *method_nums):  # TODO: support custom names
        '''
        Run in a method declared after the desired parametrized method and named the same as it
        :param method_nums:
        :return:
        '''
        for method in self.get_parameterized_methods_of_current_test(*method_nums):
            method()
