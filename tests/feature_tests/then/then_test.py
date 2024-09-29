import re
from collections import namedtuple
from itertools import chain, repeat
from typing import Iterable, Optional

from parameterized import parameterized

from src.lang_typing import YamlType
from src.language_components import Unit
from src.language_logic import When, Then
from tests.lang_code_test import AbstractLangCodeTest, LangCodeTestGenerator


class ThenTestGenerator(LangCodeTestGenerator):
    preexisting = namedtuple('preexisting', ['morphemes', 'graphemes'], defaults=[[], []])
    tc = namedtuple('tc', ['name', 'descr', 'thenee', 'applyee', 'expected', 'preexisting'], defaults=[preexisting()])
    tcs = [
        tc(
            name='simple_grapheme_replace',
            descr='',
            thenee='a',
            applyee={'whatever': 'whatever'},  # TODO: test in condition joining with when
            expected={'form': 'a'},
        ),
        tc(
            name='add_grapheme_at_end',
            descr='',
            thenee='$eł',
            applyee={'pies': 'pies'},
            expected={'form': 'pieseł'},
        ),
        tc(
            name='add_grapheme_at_beginning',
            descr='',
            thenee='un',
            applyee={'alive': 'alive'},
            expected={'form': 'unalive'},
        ),
        tc(
            name='set_feature_to_morpheme',
            descr='',
            thenee={'gender': 'female'},
            applyee={'transwoman': {'def': 'transwoman'}},
            expected={'gender': 'female'},
        ),
        tc(
            name='replace_feature_to_morpheme',
            descr='',
            thenee={'gender': 'female'},
            applyee={'transwoman': {'def': 'transwoman', 'gender': 'male'}},
            expected={'gender': 'female'},
        ),
        tc(
            name='switch_grapheme_feature',
            descr='IS WRONGLY DEFINED, add preexisting features',
            thenee='{unvoiced}$',
            applyee={'bóg'},
            expected={'def': 'bók'},
        ),
    ]  # TODO Extend: morpheme unsetting,

    @classmethod
    def generate(cls) -> Iterable[tuple]:
        n_space = ' ' * len('description: ')
        for tc in cls.tcs:
            preexistings, could_not_create_preexisting = cls.from_conf_and_is_skip(Unit, tc.preexisting.morphemes)

            applyee, could_not_create_morph = cls.from_conf_and_is_skip(Unit, tc.applyee)
            skip = could_not_create_preexisting or could_not_create_morph

            tc_name = f'{tc.name}'.lower()
            tabbed_descr = re.sub(r'\n', fr'\n{n_space}', tc.descr)

            yield tc_name, tabbed_descr, tc.thenee, applyee, tc.expected, skip


class ThenTest(AbstractLangCodeTest):
    @parameterized.expand(ThenTestGenerator.list())  # TODO form of testee
    def test(self, name: str, descr: str, thenee: YamlType, applyee: Unit, expected: dict, skip: Optional[str]):
        print(f'Info: {thenee=}, {applyee=}, {expected=}')
        if skip:
            self.skipTest(skip)
        print(f'Description: {descr}')

        try:
            then = Then.from_conf(thenee)
            actual: Unit = then(applyee)
            for key, val in expected.items():
                self.assertTrue(actual.has_feature(key))  # TODO: verify method name
                self.assertEqual(actual.get_feature(key), val)  # TODO: or get_property? can be whatever? Should test separate them?
        except Exception as e:
            self.fail(e)


