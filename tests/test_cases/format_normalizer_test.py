from __future__ import annotations

from parameterized import parameterized

from src.data_normalizer import DataNormalizer
from src.utils import to_list
from tests.lang_code_test import DotDict, AbstractLangCodeTest, yaml_types


# name_func=lambda method, param_num, params: f'{method.__name__}_{param_num}_' + get_lang_type(params[0][0])
def get_func_name(method, param_num, params):
    lang_name = params[0][0]
    func_name = f'{method.__name__}_{param_num}_normalization_of'
    normalization = AbstractLangCodeTest.all_test_properties[lang_name].normalization
    if normalization.morphemes:
        func_name += '_morphemes'
        if normalization.morphemes.elems:
            func_name += '_elems'
        elif normalization.morphemes.features:
            func_name += '_features'
            if normalization.morphemes.features.as_list:
                func_name += '_from_list'
                if normalization.morphemes.features.as_list.single:
                    func_name += '_with_single'

    return func_name


def generate_test_cases():
    raise NotImplementedError


class FeatureGenerationTest(AbstractLangCodeTest):
    @parameterized.expand(
        AbstractLangCodeTest.get_langs_where(lambda d: d.normalization),
        name_func=get_func_name,
        skip_on_empty=True,
    )
    def test(self, lang_name: str):
        # TODO: How to handle expected file when schema will work?
        normalization = self.all_test_properties[lang_name].normalization
        original = self.data_loader.load(lang_name)
        normalized = self.data_normalizer.normalize(original)

        for filename, config in normalization.items():
            if config:
                expected = original[f'expected_{filename}']
                actual = normalized[filename]
                self.assertEquals(expected, actual)




