from __future__ import annotations

from dataclasses import dataclass, field

from parameterized import parameterized

from src.exceptions import InvalidYamlException, InvalidPathException, Messages
from src.lang_factory import LangFactory
from tests.lang_code_test import AbstractLangCodeTest, Paths


from pyxdameraulevenshtein import damerau_levenshtein_distance


class LoadingTest(AbstractLangCodeTest):

    @parameterized.expand([
        ('toki_pona', ),
        ('simplified_chinese', ),
        ('form_and_compound_lang', Messages.FORMING_KEYS_TOGETHER),
        ('only_compound', Messages.NO_FORMING_KEY),
        ('sandhi_less_chinese', ),
        ('simple_sandhi_chinese', ),
        ('chinese', ),
        ],
        # name_func=lambda method, param_num, params: f'{method.__name__}_{param_num}_' + get_lang_type(params[0][0])
    )
    def test_lang_validation(self, lang_name: str, message=None):
        lf = LangFactory(Paths.LANGUAGES, lang_name)
        try:
            lang = lf.load()
            if message:
                self.fail(f'Language {lang_name} should be invalid, but succeeds to load. Expected message: {message}')
        except InvalidYamlException as iye:
            if message:
                dl = damerau_levenshtein_distance(iye.args[-1], message)
                self.assertGreater(dl, self.accepted_similarity, f'Wrong message! Got {iye.reason}, but expected {message}')
            else:
                self.fail(f"Language {lang_name} should be valid, but it's not, {iye.reason}")
        except InvalidPathException:
            self.fail(f'Language {lang_name} does not exist in {Paths.LANGUAGES}')




