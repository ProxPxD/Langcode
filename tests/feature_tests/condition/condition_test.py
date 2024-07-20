from pathlib import Path
from typing import Callable

from parameterized import parameterized

from src import utils
from src.exceptions import NoConditionAppliesException
from src.language_logic import Cond, Condition
from src.loaders import YamlLoader
from tests.lang_code_test import AbstractLangCodeTest


class ConditionTestGenerator:
    tc_dir_path = Path(__file__).parent / 'testcases'
    loader = YamlLoader()

    @classmethod
    def generate(cls) -> list[tuple[str, Callable]]:
        for path in cls.tc_dir_path.iterdir():
            tc = cls.loader.load(path)
            condition = Condition(tc['cond'])
            for expected_dict in tc['expecteds']:
                args = utils.to_tuple(expected_dict.get('for'))
                expected = expected_dict['expected']
                yield f'{path.name}_for_{args}_expecting_{expected if expected is not None else "exception"}', condition, args, expected


class ConditionTest(AbstractLangCodeTest):
    @parameterized.expand(list(ConditionTestGenerator.generate()))
    def test(self, name, cond: Condition, args: tuple, expected: str | None):
        try:
            actual = cond(*args)
            self.assertEqual(actual, expected)
        except NoConditionAppliesException:
            if expected is not None:
                raise Exception(f'{name}: {args} did match any when')




