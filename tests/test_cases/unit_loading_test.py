from __future__ import annotations

import unittest
from unittest import SkipTest

from parameterized import parameterized

from src.constants import ComplexTerms
from tests.lang_code_test import AbstractLangCodeTest, test_generator, Generator


def get_func_name(method, param_num, params):
    lang_name = params[0][0]
    properties = AbstractLangCodeTest.all_test_properties[lang_name]
    func_name = f'{method.__name__}_{param_num}_if_{lang_name}_todo'.lower()
    return func_name


@test_generator
class UnitLoadingTestGenerator(Generator):
    props_paths_to_add = ('valid_schema', 'should_load')
    lang_name_regexes = ''


class UnitLoadingTest(AbstractLangCodeTest):
    def setUp(self) -> None:
        raise SkipTest("Correct the normalizing and Finish")

    @parameterized.expand(
        UnitLoadingTestGenerator.generate_test_cases(),
        name_func=get_func_name
    )
    def test_elems(self, lang_name: str):
        lang = self.lang_factory.load()
        expected_data = self.get_normalised_data(lang_name)
        for kind in ComplexTerms.UNTIS:
            expected_units = expected_data[kind].elems
            actual_units = lang.get_units(kind)
            for expected_name, expected_unit in expected_units.items():
                self.assertIn(expected_name, actual_units.keys())
                actual_unit = actual_units[expected_name]
                for feature_name, feature in expected_unit.items():
                    self.assertIn(feature_name, actual_unit.keys())
                    self.assertIn(feature, actual_unit.values())
        self.fail(NotImplemented)

    @parameterized.expand(
        UnitLoadingTestGenerator.generate_test_cases(),
        name_func=get_func_name
    )
    def test_features(self, lang_name: str):
        self.fail(NotImplemented)



