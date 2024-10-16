from collections import namedtuple
from pathlib import Path
from typing import Callable, Optional

from parameterized import parameterized
from itertools import product

from src import utils
from src.exceptions import NoConditionAppliesException
from src.language_components import Unit
from src.language_logic import Cond, Condition
from src.loaders import YamlLoader
from src.utils import is_
from tests.lang_code_test import AbstractLangCodeTest, LangCodeTestGenerator


class CondTestGenerator(LangCodeTestGenerator):
    """
    aims to ensure the right functionality of "cond" key and its configuration's structure
    but not the separate functionalities of its sub keys
    """

    tc = namedtuple('tc', ['name', 'descr', 'defis', 'appls'])
    defi = namedtuple('defi', ['cond', 'name'], defaults=[None])
    appl = namedtuple('appl', ['condee', 'expected'])
    tcs = [
        tc(
            name='single_then',
            descr='',
            defis=[defi({'then': '$e'}, 'dict'), defi('=> $e', 'arrow'), defi('$e', 'right_side')],
            appls=[appl('mam', 'mame')],
        ),
        tc(
            name='basic_cond',
            descr='',
            defis=[defi({'when': 'a$', 'then': 'e'}), defi('a$ => e')],
            appls=[appl('mama', 'mame'), appl('mam', NotImplemented)],
        ),
        tc(
            name='basic_cond_without_replacement',
            descr='',
            defis=[defi({'when': 'a$', 'then': 'e^'}), defi('a$ => e^')],
            appls=[appl('mama', 'emama'), appl('mam', NotImplemented)],  #
        ),
        tc(
            name='wrong_just_when',
            descr='',
            defis=[defi({'when': '^s[pkt]'})],
            appls=[appl('spec', NotImplementedError)],  # Use expected exception?
        ),
        tc(
            name='removal',
            descr='',
            defis=[defi({'when': '^h', 'then': ''}), defi('^h =>')],
            appls=[appl('hola', 'ola'), appl('ola', NotImplemented)]
        )
    ]  # TODO: Extend with arrow syntax

    @classmethod
    def get_defi_name(cls, a_defi: defi) -> str:
        if a_defi.name:
            return a_defi.name
        match a_defi.cond:
            case dict(): return 'dict'
            case str() if '=>' in a_defi.cond: return 'arrow'
            case _: return 'right_side'

    @classmethod
    def generate(cls) -> list[tuple[str, Callable]]:
        for tc in cls.tcs:
            for a_defi, a_appl in product(tc.defis, tc.appls):
                cond, is_cond = cls.from_conf_and_is_skip(Cond, a_defi.cond)
                condee, is_condee = cls.from_conf_and_is_skip(Unit, a_appl.condee)
                if a_appl.expected is not NotImplemented:
                    expected, is_expected = cls.from_conf_and_is_skip(Unit, a_appl.expected)
                    condee_name = 'should_match'
                else:
                    expected, is_expected = a_appl.expected, None
                    condee_name = 'should_not_match'
                skip = is_cond or is_condee or is_expected

                case_name = cls.get_defi_name(a_defi)

                yield f'{case_name}_{tc.name}_{condee_name}', tc.descr, cond, condee, expected, skip


class CondTest(AbstractLangCodeTest):
    @parameterized.expand(list(CondTestGenerator.generate()))
    def test(self, name: str, descr: str, cond: Cond, condee: Unit, expected: Unit, skip: Optional[str]):
        print(f'Info: {cond=}, {condee=}, {expected=}')
        if skip:
            self.skipTest(skip)
        print(f'Description: {descr}')
        try:
            actual = cond(condee)
            self.assertEqual(actual, expected)
        except NoConditionAppliesException:
            if is_(Unit, expected):
                raise Exception(f'{name}: {condee} did match any "when" of {cond}')




