from __future__ import annotations

from unittest import SkipTest

import pydash as _
from parameterized import parameterized

from tests.lang_code_test import AbstractLangCodeTest, test_generator, Generator


# name_func=lambda method, param_num, params: f'{method.__name__}_{param_num}_' + get_lang_type(params[0][0])
def get_func_name(method, param_num, params):
    lang_name = params[0][0]
    func_name = f'{method.__name__}_{param_num}_normalization_of'
    normalization = AbstractLangCodeTest.all_test_properties[lang_name]['normalization']
    get = _.property_of(normalization)
    if get('morphemes'):
        func_name += '_morphemes'
    if get('morphemes.elems'):
        func_name += '_elems'
    elif get('morphemes.features'):
        func_name += '_features'
        if get('morphemes.features.as_list'):
            func_name += '_from_list'
            is_single = get('morphemes.features.as_list.single')
            is_multiple = get('morphemes.features.as_list.multiple')
            if is_single and is_multiple:
                func_name += '_with_single_and_multiple'
            elif is_single:
                func_name += '_with_single'
            elif is_multiple:
                func_name += '_with_multiple'
    return func_name


@test_generator
class DataNormalizerTestGenerator(Generator):
    props_paths_to_add = ('normalization',)
    lang_name_regexes = ''


class DataNormalizerTest(AbstractLangCodeTest):

    def setUp(self) -> None:
        raise SkipTest("Data normalizer does not exist anymore. It should probably be covered by the loading test")

    @parameterized.expand(
        DataNormalizerTestGenerator.generate_test_cases(),
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
                self.assertEqual(expected, actual)




