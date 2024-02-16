from __future__ import annotations
from tests.lang_code_test import Paths

import traceback

from parameterized import parameterized
from pyxdameraulevenshtein import damerau_levenshtein_distance

from src.exceptions import InvalidYamlException, InvalidPathException, Messages
from src.lang_factory import LangFactory
from tests.lang_code_test import AbstractLangCodeTest


def get_func_name(method, param_num, params):
    lang_name = params[0][0]
    general = AbstractLangCodeTest.all_test_properties[lang_name]
    state = 'is_valid' if general.valid_schema and general.valid_restrictions else\
            'violates_restrictions' if general.valid_schema and not general.valid_restrictions else\
            'is_invalid' if not general.valid_schema else NotImplemented
    func_name = f'{method.__name__}_if_{lang_name}_{state}'
    return func_name


class LoadingTest(AbstractLangCodeTest):
    @parameterized.expand(
        AbstractLangCodeTest.all_langs,
        name_func=get_func_name
    )
    def test(self, lang_name: str, message=None):
        # TODO: consider spliting into many functions
        # TODO: add messages according to state
        lf = LangFactory(Paths.LANGUAGES, lang_name)
        try:
            lang = lf.load()
            if message:
                self.fail(f'Language {lang_name} should be invalid, but succeeds to load. Expected message: {message}')
        except NotImplementedError:
            self.fail(traceback.format_exc())
        except InvalidYamlException as iye:
            if message:
                dl = damerau_levenshtein_distance(iye.args[-1], message)
                self.assertGreater(dl, self.accepted_similarity, f'Wrong message! Got {iye.reason}, but expected {message}')
            else:
                self.fail(f"Language {lang_name} should be valid, but it's not, {iye.reason}")
        except InvalidPathException:
            self.fail(f'Language {lang_name} does not exist in {Paths.LANGUAGES}')





