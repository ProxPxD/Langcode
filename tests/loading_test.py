from __future__ import annotations

from dataclasses import dataclass, field

from parameterized import parameterized

from src.exceptions import InvalidYamlException, InvalidPathException
from src.lang_factory import LangFactory
from tests.lang_code_test import AbstractLangCodeTest


def get_lang_type(lang_info: TestLangInfo):
    types = []
    if lang_info.single_morpheme:
        types.append('single_morpheme')
    if lang_info.compound_word:
        types.append('compound')
    if not lang_info.sound_change and not lang_info.ex_sound_change:
        types.append('regular_pronunciation')
    if lang_info.sound_change and not lang_info.ex_sound_change:
        types.append('regular_sound_change')
    if lang_info.sound_change and lang_info.ex_sound_change:
        types.append('irregular_sound_change')
    return 'none'


@dataclass
class TestLangInfo:
    name: str
    correct_config: bool = field(default=True)
    single_morpheme: bool = field(default=False)
    compound_word: bool = field(default=False)
    sound_change: bool = field(default=True)
    ex_sound_change: bool = field(default=True)


languages = [
    TestLangInfo('toki_pona', single_morpheme=True, sound_change=False, ex_sound_change=False),
    TestLangInfo('simplified_chinese', compound_word=True, sound_change=False, ex_sound_change=False),
    TestLangInfo('simple_sandhi_chinese', compound_word=True, ex_sound_change=False),
    TestLangInfo('chinese', compound_word=True),
]


class LoadingTest(AbstractLangCodeTest):

    @parameterized.expand(
        languages,
        name_func=lambda method, param_num, params: f'{method.__name__}_{param_num}_' + get_lang_type(params[0][0])
    )
    def test_lang_validation(self, lang_info: TestLangInfo):
        lf = LangFactory(self.TEST_LANGUAGES_PATH, lang_info.name)
        try:
            lang = lf.load()
            if not lang_info.correct_config:
                self.fail(f'Language {lang_info.name} should be invalid, but succeeds to load')
        except InvalidYamlException:
            if lang_info.correct_config:
                self.fail(f"Language {lang_info.name} should be valid, but it's not")
        except InvalidPathException:
            self.fail(f'Language {lang_info.name} does not exist in {self.TEST_LANGUAGES_PATH}')

