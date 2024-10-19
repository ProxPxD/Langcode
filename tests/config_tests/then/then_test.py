from dataclasses import dataclass, field
from typing import Iterable, Sequence

import pytest

import tests.lang_code_test_utils as utils
from src.lang_typing import YamlType
from src.language_components import Unit
from src.language_logic import Then
from tests.lang_code_test_utils import Preex, LangCodeTCG


class ThenTCG(LangCodeTCG):
    """
    aims to ensure the right functionality of applicative "then" key and its configuration's structure
    """

    @dataclass(frozen=False)
    class tc:
        name: str
        short: str
        thenee: YamlType
        applyee: YamlType
        expected: dict
        tags: list = field(default_factory=list)
        preexistings: Preex = field(default_factory=Preex)
        skip: str | Exception | bool = False

    tcs = [
        tc(
            name='',
            short='Replace grapheme',
            tags=['grapheme'],
            thenee='a',
            applyee={'whatever': 'whatever'},  # TODO: test in cond joining with when
            expected={'form': 'a'},
        ),
        tc(
            name='',
            short='Add grapheme suffix',
            tags=['grapheme'],
            thenee='$eł',
            applyee={'pies': 'pies'},
            expected={'form': 'pieseł'},
        ),
        tc(
            name='',
            short='Add grapheme prefix',
            tags=['grapheme'],
            thenee='un^',
            applyee={'alive': 'alive'},
            expected={'form': 'unalive'},
        ),
        tc(
            name='',
            short='Set feature to morpheme',
            thenee={'gender': 'female'},
            applyee={'transwoman': {'def': 'transwoman'}},
            expected={'gender': 'female'},
        ),
        tc(
            name='',
            short='Replace feature in morpheme',
            thenee={'gender': 'female'},
            applyee={'transwoman': {'def': 'transwoman', 'gender': 'male'}},
            expected={'gender': 'female'},
        ),
        tc(
            name='switch_grapheme_feature',
            short='IS WRONGLY DEFINED, add preexisting features',
            thenee='{unvoiced}$',
            applyee={'bóg'},
            expected={'def': 'bók'},
        ),
    ]  # TODO Extend: morpheme unsetting,

    @classmethod
    def map(cls, tc) -> tuple:
        tc.skip = utils.init_tc_fields(tc.preexistings, Unit, 'morphemes', tc, Unit, 'applyee')
        return tc

    @classmethod
    def gather_tags(cls, tc) -> Iterable[str] | Sequence[str]:
        yield 'then'
        yield from cls.gather_def_tags(tc.thenee)
        yield from cls.gather_feature_tags(tc.thenee)


@ThenTCG.parametrize('tc')
def test(tc):
    if tc.skip:
        pytest.xfail(tc.skip)

    try:
        then = Then.from_conf(tc.thenee)
        actual: Unit = then(tc.applyee)
        for key, val in tc.expected.items():
            assert actual.has_feature(key)  # TODO: verify method name
            assert actual.get_feature(key) == val  # TODO: or get_property? can be whatever? Should test separate them?
    except Exception as e:
        pytest.fail(e)


# class ThenTest(AbstractLangCodeTest):
#     @parameterized.expand(ThenTestGenerator.list())  # TODO form of testee
#     def test(self, name: str, short: str, thenee: YamlType, applyee: Unit, expected: dict, skip: Optional[str]):
#         print(f'Info: {thenee=}, {applyee=}, {expected=}')
#         if skip:
#             self.skipTest(skip)
#         print(f'shortiption: {short}')
#
#         try:
#             then = Then.from_conf(thenee)
#             actual: Unit = then(applyee)
#             for key, val in expected.items():
#                 self.assertTrue(actual.has_feature(key))  # TODO: verify method name
#                 self.assertEqual(actual.get_feature(key), val)  # TODO: or get_property? can be whatever? Should test separate them?
#         except Exception as e:
#             self.fail(e)


