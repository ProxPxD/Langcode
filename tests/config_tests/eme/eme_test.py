import re
from collections import namedtuple
from typing import Optional, Iterable

from parameterized import parameterized

from src import utils
from src.exceptions import LangCodeException
from src.language_components import Unit
from src.utils import is_, is_not, is_any_instance_of_dict, is_any_instance_of_str, is_not_dict
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
    tc = namedtuple('tc', ['name', 'descr', 'defi', 'expected', 'tags', 'preexisting'], defaults=[[], preexisting()])

    tcs = [
        tc(
            name='direct_none',
            descr='A morpheme defined with an empty eme should copy the id',
            defi={'word': None},
            expected={'form': 'word'},
        ),
        tc(
            name='def_none',
            descr='A morpheme defined with an empty eme should copy the id',
            defi={'word': {'def': None}},
            expected={'form': 'word'},
        ),
        tc(
            name='def_string',
            descr='A morpheme defined with a string eme simply defines the form',
            defi={'woman': {'def': 'woman'}},
            expected={'form': 'woman'},
        ),
        tc(
            name='def_regex',
            descr='A morpheme defined with a regex eme creating a defining a morpheme',  # TODO: Rethinkg it being bound and consider: auf- und zumachen
            defi={'plural': {'def': '$s'}},
            expected={'eme': '$s'},
        ),
        tc(
            name='apply_multi',
            descr='A morpheme [lessness] defined as an application of many morphemes [less, ness]',
            preexisting=preexisting(morphemes=[{'less': {'at': -1}}, {'ness': {'at': -1}}]),
            defi={'lessness': {'apply': ['less', 'ness']}},
            expected={'apply': ['less', 'ness']}, #?
        ),
        tc(
            name='apply_various_types',
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
            name='apply_multi_to',
            descr='A morpheme [friendship] defined with as an application of one morpheme [shipness] to another [friend]',
            preexisting=preexisting(morphemes=['friend', {'shipness': '$ship'}]),
            defi={'friendship': {'apply': 'shipness', 'to': 'friend'}},
            expected={'form': 'friendship'},
        ),
        tc(
            name='explicit_features',
            tags=('explicit-features', ),
            descr='Morpheme defined explicitly with features',
            defi={'Welt': {'gender': 'feminine'}},
            expected={'form': 'Welt', 'gender': 'feminine'},
        ),
        tc(
            name='implicit_features',
            descr='Morpheme defined as another morpheme that sets features',
            tags=('implicit-features', 'apply-feature'),
            preexisting=preexisting(morphemes=[
                {'grammar': {'pos': 'noun'}},
                {'V': {'apply': {'pos': 'verb'}}}
            ]),
            defi={'to-grammar': {'to': 'grammar', 'apply': 'V'}},
            expected={'form': 'grammar', 'pos': 'verb'},
        ),
        tc(
            name='implicit_features_with_then',
            descr='Morpheme defined as another morpheme that sets features',
            tags=('implicit-features', 'apply-feature', 'apply-then'),
            preexisting=preexisting(morphemes=[
                {'Welt': {'pos': 'noun'}},
                {'lich': {
                    'apply': ['$lich', '^[A-Z] => [a-z]', {'then': {'pos': 'adjective'}}]
                }}
            ]),
            defi={'weltlich': {'to': 'Welt', 'apply': 'lich'}},
            expected={'form': 'weltlich', 'pos': 'adjective'},
        ),
    ]

    @classmethod
    def gather_tags(cls, tc) -> list:
        tags = []
        name, definition = list(tc.defi.items())[0]
        tags.extend(cls.gather_defi_tags(definition))
        tags.extend(cls.gather_feature_tags(definition))

        return tags

    @classmethod
    def gather_defi_tags(cls, definition) -> list:
        tags = []
        match definition:
            case _ if is_not(dict, definition):
                tags.append('direct')
                tags.extend(cls.gather_def_tags(definition))
            case dict():
                if 'def' in definition:
                    tags.append('def')
                    tags.extend(cls.gather_def_tags(definition['def']))
                if 'apply' in definition:
                    tags.append('apply')
                    content = definition['apply']
                    if is_any_instance_of_dict(content) and is_any_instance_of_str(content):
                        tags.append('various-types')
                if 'to' in definition:
                    tags.append('to')
        return tags

    @classmethod
    def gather_feature_tags(cls, defi) -> list:
        if is_not_dict(defi):
            return []
        features = ['gender', 'pos', 'number']  # TODO: think of test-wide approach
        if any(feature in defi for feature in features):
            return ['explicit-features']
        return []

    @classmethod
    def gather_def_tags(cls, definition) -> list:
        match definition:
            case None: return ['none']
            case str() if definition.isalpha(): return ['string']
            case str() if not definition.isalpha(): return ['regex']
        return []

    @classmethod
    def generate(cls) -> Iterable[tuple]:
        for tc in cls.tcs:
            preexistings, could_create_preexisting = cls.from_conf_and_is_skip(Unit, tc.preexisting.morphemes)
            tags = list(tc.tags or [])
            tags.extend(cls.gather_tags(tc))
            name = tc.name or '_'.join(tags)
            yield f'{name}', tc.descr, tags, preexistings, tc.defi, tc.expected, could_create_preexisting


class EmeTest(AbstractLangCodeTest):  # TODO: rethink testing approach
    @parameterized.expand(EmeTestGenerator.list())
    def test(self, name: str, descr: str, tags: list, preexistings: list, definition: dict, expected, skip: Optional[Exception|str]):
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

