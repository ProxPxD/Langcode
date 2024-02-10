from __future__ import annotations

from parameterized import parameterized
from pyxdameraulevenshtein import damerau_levenshtein_distance

from src.exceptions import InvalidYamlException, InvalidPathException, Messages
from src.lang_factory import LangFactory
from tests.lang_code_test import AbstractLangCodeTest


def get_lang_type(lang_name: str):
    lang_info = AbstractLangCodeTest.all_languages[lang_name]
    types = []
    if lang_info.single_morpheme:
        types.append('single_morpheme')
    if lang_info.compound_word:
        types.append('compound_words')
    if not lang_info.sound_change and not lang_info.ex_sound_change:
        types.append('regular_pronunciation')
    if lang_info.sound_change and not lang_info.ex_sound_change:
        types.append('regular_sound_change')
    if lang_info.sound_change and lang_info.ex_sound_change:
        types.append('irregular_sound_change')
    if not lang_info.with_bounded:
        types.append('free_morpheme')

    lang_type = ''
    if len(types) == 1:
        lang_type += types[0] + '_only'
    if len(types) > 1:
        lang_type += '_'.join(types)

    lang_type += '_on_' + lang_info.name

    return lang_type


class LoadingTest(AbstractLangCodeTest):

    @parameterized.expand([
        ('toki_pona', ),
        ('simplified_chinese', ),
        ('incompatible_chinese', Messages.FORMING_KEYS_TOGETHER),
        ('only_compound', Messages.NO_FORMING_KEY),
        ('sandhi_less_chinese', ),
        ('simple_sandhi_chinese', ),
        ('chinese', ),
        ],
        name_func=lambda method, param_num, params: f'{method.__name__}_{param_num}_' + get_lang_type(params[0][0])
    )
    def test_lang_validation(self, lang_name: str, message=None):
        lang_info = self.all_languages[lang_name]
        lf = LangFactory(self.LANGUAGES_PATH, lang_info.name)
        try:
            lang = lf.load()
            if message:
                self.fail(f'Language {lang_info.name} should be invalid, but succeeds to load. Expected message: {message}')
        except InvalidYamlException as iye:
            if message:
                dl = damerau_levenshtein_distance(iye.args[-1], message)
                self.assertGreater(dl, self.accepted_similarity, f'Wrong message! Got {iye.reason}, but expected {message}')
            else:
                self.fail(f"Language {lang_info.name} should be valid, but it's not, {iye.reason}")
        except InvalidPathException:
            self.fail(f'Language {lang_info.name} does not exist in {self.LANGUAGES_PATH}')




