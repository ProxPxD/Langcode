from parameterized import parameterized

from src.morphemes import SingleMorpheme
from tests.abstractTest import AbstractTest


class BasicMorpheme(AbstractTest):

    @parameterized.expand([
        ('', )
    ])
    def test_basic_morphemes(self, form: str, at, step):
        SingleMorpheme[str]()
