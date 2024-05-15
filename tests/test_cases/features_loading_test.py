from __future__ import annotations

import unittest
from unittest import SkipTest

import nutree
from parameterized import parameterized

from src.langtree import LangTree
from tests.lang_code_test import AbstractLangCodeTest, Generator, test_generator


def get_func_name(method, param_num, params):
    lang_name, kind, *rest = params[0]
    properties = AbstractLangCodeTest.all_test_properties[lang_name]

    func_name = f'{method.__name__}_{kind}_features_of_{lang_name}'
    return func_name


def generate_test_cases():
    for lang_name in feature_lang_names:
        yield lang_name, None, None
        continue
        all_features = AbstractLangCodeTest.get_normalised_data(lang_name).features
        for kind, units in all_features.items():
            yield lang_name, kind[:-1], LangTree.from_str_dict(units)


@test_generator
class FeaturesLoadingTestGenerator(Generator):
    props_paths_to_add = ('valid_schema', 'should_load', 'features',)
    lang_name_regexes = ''
    get_lang_parameters = lambda _: (None, None)


class FeaturesLoadingTest(AbstractLangCodeTest):
    def setUp(self) -> None:
        raise SkipTest('Test should have a better way to gather the features')

    @parameterized.expand(
        FeaturesLoadingTestGenerator.generate_test_cases(),
        name_func=get_func_name
    )
    def test(self, lang_name: str, kind: str, expected_features: LangTree):
        lang = self.lang_factory.load()
        tree_iter = expected_features.iterator(nutree.IterMethod.LEVEL_ORDER)
        for node in tree_iter:
            try:
                lang.get_feature(node.data, kind)
            except ValueError:  # TODO change to custom
                self.fail(f'{lang_name} has no feature {node.data}')

        # TODO: think of checking the structure and not only existence



