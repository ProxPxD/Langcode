from pathlib import Path

from tests.abstractTest import AbstractTest


class AbstractLangCodeTest(AbstractTest):
    TEST_LANGUAGES_PATH = Path(__file__).parent / "test_languages"
