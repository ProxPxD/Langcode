from dataclasses import field, dataclass
from pathlib import Path

from src.exceptions import Messages
from tests.abstractTest import AbstractTest


@dataclass
class TestLangInfo:
    name: str
    correct_config: bool = field(default=True)
    sound_change: bool = field(default=True)
    ex_sound_change: bool = field(default=True)
    single_morpheme: bool = field(default=False)
    compound_word: bool = field(default=False)
    with_bounded: bool = field(default=True)


class AbstractLangCodeTest(AbstractTest):
    TEST_LANGUAGES_PATH = Path(__file__).parent / "test_languages"

    accepted_similarity = .5

    all_languages = {
        'toki_pona': TestLangInfo('toki_pona',                           sound_change=False, ex_sound_change=False, single_morpheme=True, with_bounded=False),
        'simplified_chinese': TestLangInfo('simplified_chinese',         sound_change=False, ex_sound_change=False, compound_word=True, with_bounded=False),
        'form_and_compound_lang': TestLangInfo('form_and_compound_lang', sound_change=False, ex_sound_change=False, compound_word=True,                          correct_config=False),
        'no_forming_key_lang': TestLangInfo('no_forming_key_lang',       sound_change=False, ex_sound_change=False, compound_word=True,                          correct_config=False),
        'sandhi_less_chinese': TestLangInfo('sandhi_less_chinese',       sound_change=False, ex_sound_change=False, compound_word=True),
        'simple_sandhi_chinese': TestLangInfo('simple_sandhi_chinese',                       ex_sound_change=False, compound_word=True),
        'chinese': TestLangInfo('chinese',                               sound_change=True,  ex_sound_change=True,  compound_word=True),
    }
