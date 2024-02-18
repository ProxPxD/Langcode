from __future__ import annotations

from parameterized import parameterized

from src.dot_dict import DotDict
from tests.lang_code_test import AbstractLangCodeTest, yaml_types


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
            dotdict = AbstractLangCodeTest.get_normalised_data(lang_name)
        except:
            continue

        # TODO: rn there's no test lang for graphemes but it should be adjust
        # TODO: once grapheme features are added
        unit_names = 'morphemes', 'graphemes'
        all_units = {unit_name: dotdict[unit_name].elems or {} for unit_name in unit_names}
        for kind, units in all_units.items():
            for name, config in units.items():
                for feature_name, expected_value in config.expected.items():
                    yield lang_name, kind, name, feature_name, expected_value


class FeatureGenerationTest(AbstractLangCodeTest):
    @parameterized.expand(
        list(generate_test_cases()),
        name_func=get_func_name,
        skip_on_empty=True,
    )
    def test(self, lang_name: str, unit_kind: str, unit_name: str, feature_name: str, expected: yaml_types):
        lang = self.load_lang(lang_name)
        actual = lang.get_units(unit_kind).get(unit_name)[feature_name]
        self.assertEqual(expected, actual)




