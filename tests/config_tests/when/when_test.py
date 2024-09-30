import re
from collections import namedtuple
from itertools import chain, repeat
from typing import Iterable, Optional

from parameterized import parameterized

from src.lang_typing import YamlType
from src.language_components import Unit
from src.language_logic import When
from tests.lang_code_test import AbstractLangCodeTest, LangCodeTestGenerator


class WhenTestGenerator(LangCodeTestGenerator):
    preexisting = namedtuple('preexisting', ['morphemes', 'graphemes'], defaults=[[], []])
    tc = namedtuple('tc', ['name', 'descr', 'whenee', 'passings', 'failings', 'preexisting'], defaults=[preexisting()])
    case = namedtuple('case', ['conf', 'descr'], defaults=[{}, None])
    tcs = [
        tc(
            name='same_grapheme',
            descr='Plain text with no Regex symbols should pass for the exact same Morpheme and Grapheme,\n'
                  'but not for those containing it',
            whenee='eperanto',
            passings=[
                case({'esperanto': 'esperanto'}, 'with_same_id_same_form'),
                case({'esperantist': 'esperanto'}, 'with_different_id_same_form'),
            ],
            failings=[
                case({'malamo': 'malamo'}, 'with_different_id_different_form'),
                case({'esperanto': 'esperantist'},  'with_same_id_different_form'),
                case({'esperanto': 'malesperanto'},  'containing'),
            ],
        ),
        tc(
            name='grapheme_regex',
            descr='Plain text with Regex symbols should pass for Morphemes and Graphemes whose forms match it',
            whenee='i$',
            passings=[
                case({'canti': 'canti'}, 'with_matching_id_matching_form'),
                case({'to-sing': 'canti'}, 'with_wrong_id_matching_form'),
            ],
            failings=[
                case({'canto': 'canto'}, 'with_wrong_id_wrong_form'),
                case({'canti': 'canto'}, 'with_wrong_id_matching_form'),
                case({'mia': 'mia'}, 'with_containing_not_matching'),
            ],
        ),
        tc(
            name='grapheme_feature_regex',
            descr='Regex with alphabetical characters inside curly brackets should match against Graphemes and Morphemes,\n'
                  'whose forms have there a featuring grapheme',
            whenee='{V}$',
            passings=[
                case({'grande': 'grande'}, 'with_matching_id_matching_form'),
                case({'big': 'grande'}, 'with_wrong_id_matching_form'),
            ],
            failings=[
                case({'gran': 'gran'}, 'with_wrong_id_wrong_form'),
                case({'grande': 'gran'}, 'with_matching_id_wrong_form'),
                case({'grande': '{V}$'}, 'with_plain_regex'),  # TODO: Impossible to set, think of allowing it under custom options
            ],
        ),
        tc(  # TODO: invent a way to construct on generation, but skip if it fails
            name='morpheme_regex',
            descr='',
            whenee='[] plural',
            preexisting=preexisting(
                morphemes=['toe', {'plural': '$s'}]
            ),
            passings=[
                    case({'to': 'toe', 'apply': 'plural'}, 'with_applied_syntax'),
                    case({'def': ['toe', 'plural']}, 'with_concatenated_syntax'),
            ],
            failings=[
                    case({'toes'}, 'non_featuring'),
                    case({'toes': {'plural': True}}, 'featuring'),
                    case({'toes': {'plural': False}}, 'anti_featuring'),
            ],
        ),
        tc(
            name='morpheme_features_default',
            descr='',
            whenee='[] {plural}',
            preexisting=preexisting(
                morphemes=['toe', {'plural': '$s'}]
            ),
            passings=[
                    case({'feet': {'plural': True}}, 'featuring', ),
            ],
            failings=[
                    case('feet', 'non_featuring',),
                    case({'foot': {'plural': False}}, 'anti_featuring'),
                    case({'def': ['toe', 'plural']}, 'non_featuring_containing_morpheme'),
            ],
        ),
        tc(  # TODO: There shouldn't be such grapheme feature, test elsewhere
            name='morpheme_features_implied',
            descr='',
            whenee='{plural}$',
            preexisting=preexisting(
                morphemes=['toe', {'plural': '$s'}]
            ),
            passings=[
                    case({'feet': {'plural': True}}, 'featuring', ),
            ],
            failings=[
                    case('feet', 'non_featuring',),
                    case({'foot': {'plural': False}}, 'anti_featuring'),
                    case({'def': ['toe', 'plural']}, 'non_featuring_containing_morpheme'),
            ],
        ),
    ]  # TODO EXTEND: dict whens

    @classmethod
    def generate(cls) -> Iterable[tuple]:
        n_space = ' ' * len('description: ')
        for tc in cls.tcs:
            preexistings, could_not_create_preexisting = cls.from_conf_and_is_skip(Unit, tc.preexisting.morphemes)
            for case, expected in cls.gen_morph_dicts_and_states(tc):
                morph, could_not_create_morph = cls.from_conf_and_is_skip(Unit, case.conf)
                skip = could_not_create_preexisting or could_not_create_morph

                state = 'passing' if expected else 'failing'
                tc_name = f'when_{tc.name}_against_{state}_{case.descr}'.lower()
                tabbed_descr = re.sub(r'\n', fr'\n{n_space}', tc.descr)

                yield tc_name, tabbed_descr, tc.whenee, morph, expected, skip

    @classmethod
    def gen_morph_dicts_and_states(cls, tc: tc) -> Iterable[tuple[..., bool]]:
        passings = zip(tc.passings, repeat(True))
        failings = zip(tc.failings, repeat(False))
        return chain(passings, failings)


class WhenTest(AbstractLangCodeTest):
    @parameterized.expand(WhenTestGenerator.list())  # TODO form of testee
    def test(self, name: str, descr: str, whenee: YamlType, morph: Unit, expected: bool, skip: Optional[str]):
        print(f'Info: {whenee=}, {morph=}, {expected=}')
        if skip:
            self.skipTest(skip)
        print(f'Description: {descr}')

        try:
            when = When.from_conf(whenee)
            self.assertEqual(when(morph), expected)
        except Exception as e:
            self.fail(e)


