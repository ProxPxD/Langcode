from __future__ import annotations

from unittest import SkipTest

from tests.lang_code_test import Paths

import traceback

from parameterized import parameterized
from pyxdameraulevenshtein import damerau_levenshtein_distance

from src.exceptions import InvalidYamlException, InvalidPathException, Messages
from src.lang_factory import LangFactory
from tests.lang_code_test import AbstractLangCodeTest


def get_func_name(method, param_num, params):
    lang_name, valid_schema, should_load = params[0]
    general = AbstractLangCodeTest.all_test_properties[lang_name]
    state = 'is_valid' if valid_schema and general.valid_restrictions else\
            'violates_restrictions' if valid_schema and not general.valid_restrictions else\
            'is_invalid' if not valid_schema else NotImplemented
    func_name = f'{method.__name__}_if_{lang_name}_{state}'.lower()
    return func_name


def generate_test_cases():
    lang_names = AbstractLangCodeTest.all_langs
    for lang_name in lang_names:
        properties = AbstractLangCodeTest.all_test_properties[lang_name]
        yield lang_name, properties.valid_schema, properties.should_load


class LoadingTest(AbstractLangCodeTest):
    @parameterized.expand(
        generate_test_cases(),
        name_func=get_func_name
    )
    def test(self, lang_name: str, valid_schema, should_load, message=None):
        # TODO: consider spliting into many functions
        # TODO: add messages according to state
        try:
            lang = self.lang_factory.load(lang_name)
        except NotImplementedError:
            self.fail(traceback.format_exc())
        except InvalidYamlException as iye:
            if valid_schema:
                self.fail(f"Language {lang_name} should be valid, but it's not, {iye.reason}")
            if message:
                dl = damerau_levenshtein_distance(iye.args[-1], message)
                self.assertGreater(dl, self.accepted_similarity, f'Wrong message! Got {iye.reason}, but expected {message}')
        except InvalidPathException:
            self.fail(f'Language {lang_name} does not exist in {Paths.LANGUAGES}')
        else:
            if message:
                self.fail(f'Language {lang_name} should be invalid, but succeeds to load. Expected message: {message}')





