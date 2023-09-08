from __future__ import annotations

import inspect
from dataclasses import dataclass, asdict
from typing import Type, Iterable

from src.morphemes import SingleMorpheme, Position, Step, Coord, By, Side
from tests.abstractTest import AbstractTest

Record = tuple[str, str | None, str | None, Coord, Step, Position, tuple[str], tuple[str| Type[Exception | ValueError]]]


# TODO: write to parametrized/unittest to solve the issue with separately and both patch being set before the class and before the method
class BasicMorphemeTest(AbstractTest):
    is_generated = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_generated:
            self.gen_all_basic_morpheme_tests()
            self.is_generated = True
    # TODO think: of adding multiple ats, possibly working with many bys and sides (but not necessary)
    '''
        (name: str, to_remove: str, to_insert: str, at: Coord, by: Step, side: Position, words: tuple[str], excepted: tuple[str | ExceptionType])
    '''

    @dataclass
    class Params:
        inserts: Iterable[Record] = tuple()
        removes: Iterable[Record] = tuple()
        replaces: Iterable[Record] = tuple()
        multi: BasicMorphemeTest.Params = None

        dict = asdict

    all_params = Params(
        inserts=(
            ('at_start', '', 'ver', 1, None, None, ('sprechen', ''), ('versprechen', 'ver')),
            ('at_end', None, '匠', -1, None, None, ('铁', '鞋', '修锁', ''), ('铁匠', '鞋匠', '修锁匠', '匠')),
            ('as_second_from_start', None, 'r', 2, None, None, ('atak', 'a', ''), ('artak', 'ar', ValueError)),
            ('as_second_from_end', '', 'e', -2, None, None, ('statk', ), ('statek', )),
            ('as_second_from_start_using_side', None, 'r', 1, None, Side.AFTER, ('atak', 'a', ''), ('artak', 'ar', ValueError)),
            ('as_second_from_end_using_side', None, 'e', -1, None, Side.BEFORE, ('statk', ), ('statek', )),
            ('from_start_by_vowels', '', 'j', 1, By.VOWELS, Side.AFTER, ('ana', 'maq'), ('ajna', 'majq')),
            ('from_end_by_vowels', '', 'r', -1, By.VOWELS, Side.BEFORE, ('hama', 'taj'), ('hamra', 'traj')),
            ('second_from_end_by_vowels', '', 'h', -2, By.VOWELS, Side.AFTER, ('ami', 'larak'), ('ahmi', 'lahrak')),
            ('before_second_consonant_from_start', '', 'y', 2, By.CONSONANTS, Side.BEFORE, ('trocki', 'espana'), ('tyrocki', 'esypana')),
            ('after_second_consonant_from_end', '', 'i', -2, By.CONSONANTS, Side.AFTER, ('rakta', 'trakt'), ('rakita', 'trakit')),
        ),
        removes=(
            ('first', 'e', '', 1, None, None, ('ava',), (ValueError, )),
            ('last', 'r', '', -1, None, None, ('ama', ), (ValueError, )),
            ('as_second_from_start', None, 'r', 2, None, None, ('', ), (ValueError, )),
        ),
        replaces=(
            ('first_from_start', 'e', 'i', 1, None, None, ('est', 'ist'), ('ist', ValueError)),
            ('first_from_end', 'a', 'y', -1, None, None, ('mama', ), ('mamy', )),
            ('second_from_start', 'j', 'w', 2, None, None, ('ajka', ), ('awka', )),
            ('second_from_end', 'j', 'w', -2, None, None, ('fja', ), ('fwa', )),
            ('second_from_start_by_vowel_before', 'm', 'b', 2, By.VOWELS, Side.BEFORE, ('mama', ), ('maba', )),
            ('second_from_start_by_vowel_before', 't', 'b', 2, By.VOWELS, Side.AFTER, ('mamat', ), ('mamab', )),
            ('second_from_end_by_vowel_before',   'm', 'b', -2, By.VOWELS, Side.BEFORE, ('mama', ), ('bama', )),
            ('second_from_start_by_vowel_at', 'a', 'e', 2, By.VOWELS, Side.AT, ('dada', 'kirat', 'koko'), ('dade', 'kiret', ValueError)),
            ('second_from_end_by_vowel_at',   'a', 'e', -2, By.VOWELS, Side.AT, ('dada', 'karate', 'kakoka'), ('deda', 'karete', ValueError)),
            ('precise_at', 'o', 'ue', -2, By.VOWELS, Side.AT, ('soler',), ('sueler', )),
            ('precise_before', 'm', 'bj', -2, By.VOWELS, Side.BEFORE, ('mama',), ('bjama', )),
            ('precise_after', 'm', 'jb', -2, By.VOWELS, Side.AFTER, ('mama',), ('majba', )),
        ),
        multi=Params(
            # ('replace_at_two_places', 'i', 'u', (1, 2), By.VOWELS, Side.AT, ('anla', ), ('enle', )),
            # ('replace_at_two_sides', 't', 'd', -1, By.VOWELS, (Side.BEFORE, Side.AFTER), ('tato', ), ('dado', )),
            # ('replace_at_from_start_and_end', 'o', 'u', (1, -1), By.VOWELS, Side.AT, ('omamo', ), ('umamu', )),
        )
    )

    # TODO idea: assert that a certain method was called. Problem: Mock disables the invert function due to not knowing what happens in __init__
    @classmethod
    def gen_all_basic_morpheme_tests(cls):
        cls.create_test_types('insert', cls.all_params.inserts)
        cls.create_test_types('remove', cls.all_params.removes)
        cls.create_test_types('replace', cls.all_params.replaces)

    @classmethod
    def create_test_types(cls, test_type: str, all_type_params):
        for name, *rest in all_type_params:
            words = rest[-2]
            expecteds = rest[-1]
            params = rest[:-2]
            for i, word, expected in zip(range(len(words)), words, expecteds):
                print(expected)
                if inspect.isclass(expected) and issubclass(expected, Exception):
                    test_prefix = 'test_except_at'
                    test = cls.get_except_morpheme_test(name, *params, word, expected)
                else:
                    test_prefix = f'test'
                    test = cls.get_apply_morpheme_test(name, *params, word, expected)
                test_name = f'{test_prefix}_{test_type}_{name}_w{f"_{word}" if word else ""}'
                if len(word) > 1:
                    test_name += f'_{i}'
                setattr(BasicMorphemeTest, test_name, test)

    @classmethod
    def get_apply_morpheme_test(cls, test_name: str, to_remove: str, to_insert: str, at: Coord, by: Step, side: Position, word: str, expected: str):
        def test(self):
            t = test_name
            self.assertIsNotNone(word)
            self.assertIsNotNone(expected)
            morpheme = SingleMorpheme[str](to_remove, to_insert, at=at, by=by, side=side)
            if to_remove is not None:
                self.assertEqual(to_remove, morpheme.to_remove)
            if to_insert is not None:
                self.assertEqual(to_insert, morpheme.to_insert)
            actual = morpheme(word)
            self.assertEqual(actual, expected)
        return test

    @classmethod
    def get_except_morpheme_test(cls, test_name: str, to_remove: str, to_insert: str, at: Coord, by: Step, side: Position, word: str, expected: Type[Exception | ValueError]):
        def test(self):
            t = test_name
            self.assertIsNotNone(word)
            self.assertIsNotNone(expected)
            morpheme = SingleMorpheme[str](to_remove, to_insert, at=at, by=by, side=side)
            if to_remove is not None:
                self.assertEqual(to_remove, morpheme.to_remove)
            if to_insert is not None:
                self.assertEqual(to_insert, morpheme.to_insert)
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
