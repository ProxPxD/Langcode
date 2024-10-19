from collections import namedtuple
from typing import Optional, Iterable

from parameterized import parameterized

from src.exceptions import LangCodeException
from src.language_components import Unit
from tests.lang_code_test import LangCodeTestGenerator, AbstractLangCodeTest


class EmeTestGenerator(LangCodeTestGenerator):
    """
    aims to ensure the right functionality of eme sub keys and its configuration's structure
    like:
      - def
      - apply
      - to
      - <FEATURE>
    """

    preexisting = namedtuple('preexisting', ['morphemes', 'graphemes'], defaults=[[], []])
    tc = namedtuple('tc', ['name', 'descr', 'defi', 'expected', 'preexisting'], defaults=[preexisting()])

    tcs = [
        tc(
            name='none',
            descr='A morpheme defined with an empty eme should copy the id',
            defi={'word': None},
            expected={'form': 'word'},
        ),
        tc(
            name='none_def',
            descr='A morpheme defined with an empty eme should copy the id',
            defi={'word': {'def': None}},
            expected={'form': 'word'},
        ),
        tc(
            name='string_def',
            descr='A morpheme defined with a string eme simply defines the form',
            defi={'woman': {'def': 'woman'}},
            expected={'form': 'woman'},
        ),
        tc(
            name='regex_def',
            descr='A morpheme defined with a regex eme creating a defining a morpheme',  # TODO: Rethinkg it being bound and consider: auf- und zumachen
            defi={'plural': {'def': '$s'}},
            expected={'eme': '$s'},
        ),
        tc(
            name='multi_apply',
            descr='A morpheme [lessness] defined as an application of many morphemes [less, ness]',
            preexisting=preexisting(morphemes=[{'less': {'at': -1}}, {'ness': {'at': -1}}]),
            defi={'lessness': {'apply': ['less', 'ness']}},
            expected={'apply': ['less', 'ness']}, #?
        ),
        tc(
            name='various_apply_types',
            descr='A morpheme [lich] defined as an application of many unnamed of different types',  # THINK: reword?
            defi={'lich': {
                'apply': ['$lich', '^[A-Z] => [a-z]', {'then': {'pos': 'adjective'}}]
            }},
            expected={
                'apply': ['$lich', '^[A-Z] => [a-z]', {'then': {'pos': 'adjective'}}]  #?
            },
        ),
        tc(
            name='apply_to',
            descr='A morpheme [friendship] defined as an application of one morpheme [shipness] to another [friend]',
            preexisting=preexisting(morphemes=['friend', {'shipness': '$ship'}]),
            defi={'friendship': {'apply': 'shipness', 'to': 'friend'}},
            expected={'form': 'friendship'},
        ),
        tc(
            name='multi_apply_to',
            descr='A morpheme [friendship] defined with as an application of one morpheme [shipness] to another [friend]',
            preexisting=preexisting(morphemes=['friend', {'shipness': '$ship'}]),
            defi={'friendship': {'apply': 'shipness', 'to': 'friend'}},
            expected={'form': 'friendship'},
        ),
        tc(
            name='explicit_features',
            descr='Morpheme defined explicitly with features',
            defi={'Welt': {'gender': 'feminine'}},
            expected={'form': 'Welt', 'gender': 'feminine'},
        ),
        tc(
            name='implicit_features',
            descr='Morpheme defined as another morpheme that sets features',
            preexisting=preexisting(morphemes=[
                {'Welt': {'pos': 'noun'}},
                {'lich': {
                    'apply': ['$lich', '^[A-Z] => [a-z]', {'then': {'pos': 'adjective'}}]  # todo: add multi apply to apply cases # todo add dict in list to apply cases
                }}
            ]),
            defi={'weltlich': {'to': 'Welt', 'apply': 'lich'}},
            expected={'form': 'weltlich', 'pos': 'adjective'},
        ),

    ]

    @classmethod
    def generate(cls) -> Iterable[tuple]:
        for tc in cls.tcs:
            preexistings, could_create_preexisting = cls.from_conf_and_is_skip(Unit, tc.preexisting.morphemes)
            yield f'{tc.name}', tc.descr, preexistings, tc.defi, tc.expected, could_create_preexisting


class EmeTest(AbstractLangCodeTest):  # TODO: rethink testing approach
    @parameterized.expand(EmeTestGenerator.list())
    def test(self, name: str, descr: str, preexistings: list, definition: dict, expected, skip: Optional[Exception|str]):
        #print(f'Info: {whenee=}, {morph=}, {expected=}')
        if skip:
            self.skipTest(skip)
        print(f'Description: {descr}')

        self._test_creation(definition, expected)

    def _test_creation(self, definition, expected):
        try:
            eme = Unit.from_conf(definition)
            self.assertEqual(eme, expected)  # TODO: think of how to change the expecteds
        except LangCodeException as e:
            self.fail(e)

