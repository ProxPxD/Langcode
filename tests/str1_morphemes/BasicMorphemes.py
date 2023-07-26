from typing import Type

from src.morphemes import SingleMorpheme, Position, Step, Coord, By, Side
from tests.abstractTest import AbstractTest


# TODO: write to parametrized/unittest to solve the issue with separately and both patch being set before the class and before the method
class BasicMorpheme(AbstractTest):
    is_generated = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_generated:
            self.gen_all_basic_morpheme_tests()
            self.is_generated = True

    '''
        (name: str, to_remove: str, to_insert: str, at: Coord, by: Step, side: Position, words: tuple[str], excepted: tuple[str | ExceptionType])
    '''
    single_morpheme_params = [
        # Inserts and Removes
        ('at_start', '', 'ver', 1, None, None, ('sprechen', ''), ('versprechen', 'ver')),
        ('at_end', None, '匠', -1, None, None, ('铁', '鞋', '修锁', ''), ('铁匠', '鞋匠', '修锁匠', '匠')),
        ('as_second_from_start', None, 'r', 2, None, None, ('atak', 'a', ''), ('artak', 'ar', ValueError)),
        ('as_second_from_end', '', 'e', -2, None, None, ('statk', ), ('statek', )),
        ('as_second_from_start_using_side', None, 'r', 1, None, Side.AFTER, ('atak', 'a', ''), ('artak', 'ar', ValueError)),
        ('as_second_from_end_using_side', None, 'e', -1, None, Side.BEFORE, ('statk', ), ('statek', )),
        ('from_start_by_vowels', '', 'j', 1, By.VOWELS, Side.AFTER, ('ana', 'maq'), ('ajna', 'majq')),
        ('from_end_by_vowels', '', 'r', 1, By.VOWELS, Side.BEFORE, ('hama', 'taj'), ('hamra', 'traj')),
        ('second_from_end_by_vowels', '', 'h', 2, By.VOWELS, Side.BEFORE, ('ami', 'larak'), ('ahmi', 'lahrak')),
        ('after_second_consonant_from_end', '', 'i', -2, By.CONSONANTS, Side.AFTER, ('rakta', 'trakt'), ('rakita', 'traktit')),

        # Removes' Exceptions:
        ('remove_first', 'e', '', 1, None, None, ('ava',), (ValueError, )),
        ('remove_last', 'r', '', -1, None, None, ('ama', ), (ValueError, )),
        ('remove_as_second_from_start', None, 'r', 2, None, None, ('', ), (ValueError, )),
        # Replaces:
    ]

    # TODO idea: assert that a certain method was called. Problem: Mock disables the invert function due to not knowing what happens in __init__
    @classmethod
    def gen_all_basic_morpheme_tests(cls):
        for (name, to_remove, to_insert, at, by, side, words, expecteds) in cls.single_morpheme_params:
            for i, word, expected in zip(range(len(words)), words, expecteds):
                adfix = cls.get_test_adfix(i, word, expected, words, expecteds)
                if isinstance(expected, str):
                    insert_test_name = f'test_insert_{name}_{adfix}'
                    remove_test_name = f'test_remove_{name}_{adfix}'
                    insert_test = cls.get_apply_morpheme_test(insert_test_name, to_remove, to_insert, at, by, side, word, expected)
                    remove_test = cls.get_apply_morpheme_test(remove_test_name, to_insert, to_remove, at, by, side, expected, word)
                    setattr(BasicMorpheme, insert_test_name, insert_test)
                    setattr(BasicMorpheme, remove_test_name, remove_test)
                elif isinstance(expected, type(Exception)):
                    exception_test_name = f'test_{adfix}_{name}'
                    test = cls.get_impossible_to_apply_morpheme_test(exception_test_name, to_remove, to_insert, at, by, side, word, expected)
                    setattr(BasicMorpheme, exception_test_name, test)
                else:
                    raise ValueError

    @classmethod
    def get_test_adfix(cls, i, word, expected, words, expecteds):
        if isinstance(expected, str) and len(words) > 1:
            if len(word) == 0:
                return f'{i}_empty'
            elif len(word) == 1:
                return f'{i}_to_single'
            elif len(words) == 2 and any((isinstance(e, type(Exception)) for e in expecteds)):
                return f'{i}_common'
        elif isinstance(expected, type(Exception)):
            return f'except'
        return ''

    @classmethod
    def get_apply_morpheme_test(cls, test_name: str, to_remove: str, to_insert: str, at: Coord, by: Step, side: Position, word: str, expected: str):
        def test(self):
            t = test_name
            self.assertIsNotNone(word)
            self.assertIsNotNone(expected)
            morpheme = SingleMorpheme[str](to_remove, to_insert, at=at, by=by, side=side)
            actual = morpheme(word)
            self.assertEqual(actual, expected)
        return test

    @classmethod
    def get_impossible_to_apply_morpheme_test(cls, test_name: str, to_remove: str, to_insert: str, at: Coord, by: Step, side: Position, word: str, expected: Type):
        def test(self):
            t = test_name
            self.assertIsNotNone(word)
            self.assertIsNotNone(expected)
            morpheme = SingleMorpheme[str](to_remove, to_insert, at=at, by=by, side=side)
            self.assertIsNotNone(morpheme)
            with self.assertRaises(expected):
                morpheme(word)
        return test

    # @patch('src.morphemes.SingleMorpheme', spec=True)
    # def test_basic_morphemes(self, name: str, to_remove: str, to_insert: str, at: Coord, by: Step, side: Position, words: Collection[str], expecteds: Collection[str | Exception], expected_method_to_be_called, mock_single_morpheme: MagicMock = None):
        # mock_single_morpheme.at = at
        # mock_single_morpheme.to_insert = to_remove if to_insert is not None else ''
        # mock_single_morpheme.at = at if at is not None else 1
        # mock_single_morpheme.by = by if by is not None else By.LETTERS
        # mock_single_morpheme.side = side if side is not None else Side.AFTER
