from __future__ import annotations

import nutree
from parameterized import parameterized

from src.langtree import LangTree
from tests.lang_code_test import AbstractLangCodeTest


def get_func_name(method, param_num, params):
    lang_name, kind, *rest = params[0]
    properties = AbstractLangCodeTest.all_test_properties[lang_name]

    func_name = f'{method.__name__}_{kind}_features_of_{lang_name}'
    return func_name


def generate_test_cases():
    feature_lang_names = AbstractLangCodeTest.get_langs_where(lambda p: p.valid_schema and p.should_load and p.features)
    for lang_name in feature_lang_names:
        all_features = AbstractLangCodeTest.get_normalised_data(lang_name).features
        for kind, units in all_features.items():
            yield lang_name, kind[:-1], LangTree.from_str_dict(units)


class FeaturesLoadingTest(AbstractLangCodeTest):
    @parameterized.expand(
        list(generate_test_cases()),
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



