from __future__ import annotations

from itertools import chain

from parameterized import parameterized

from src.utils import to_list
from tests.lang_code_test import DotDict, AbstractLangCodeTest, yaml_types


# name_func=lambda method, param_num, params: f'{method.__name__}_{param_num}_' + get_lang_type(params[0][0])
def get_func_name(method, param_num, params):
    lang_name, unit_kind, unit_name, feature_name, expected = params[0]
    general = AbstractLangCodeTest.all_test_properties[lang_name]
    # TODO: think of specifying how the features are generated.
    # TODO: do they use aliases, ands ors, what forms, etc.
    unit_features = general.rules.features[unit_kind]
    func_name = f'{method.__name__}_if_in_{lang_name}_{unit_kind[:-1]}_{unit_name}_has_generated_{feature_name}'
    return func_name


def generate_test_cases():
    lang_names = AbstractLangCodeTest.get_langs_where(lambda d: d.rules.features)
    for lang_name in lang_names:
        try:
            raw_data = AbstractLangCodeTest.data_loader.load(lang_name)
            data = AbstractLangCodeTest.data_normalizer.normalize(raw_data)
        except:
            continue

        morphemes = data.get('morphemes', {}).get('elems', {})
        # TODO: rn there's no test lang for graphemes but it should be adjust
        # TODO: once grapheme features are added
        graphemes = data.get('graphemes', {}).get('elems', {})
        all_units = {'morphemes': morphemes, 'graphemes': graphemes}
        for kind, units in all_units.items():
            for name, config in units.items():
                for feature_name, expected_value in config.get('expected', {}).items():
                    yield lang_name, kind, name, feature_name, expected_value


class FeatureGenerationTest(AbstractLangCodeTest):
    @parameterized.expand(
        list(generate_test_cases()),
        name_func=get_func_name,
        skip_on_empty=True,
    )
    def test(self, lang_name: str, unit_kind: str, unit_name: str, feature_name: str, expected: yaml_types):
        lang = self.lang_factory.load(lang_name)
        actual = lang.get_units(unit_kind).get(unit_name)[feature_name]
        self.assertEquals(expected, actual)




