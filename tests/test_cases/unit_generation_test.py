from __future__ import annotations

from pathlib import Path

from parameterized import parameterized

from src.dot_dict import DotDict
from tests.lang_code_test import AbstractLangCodeTest, yaml_types


def get_func_name(method, param_num, params):
    lang_name, unit_kind, unit_name, expected = params[0]
    general = AbstractLangCodeTest.all_test_properties[lang_name]
    # TODO: think of specifying how the features are generated.
    # TODO: do they use aliases, ands ors, what forms, etc
    func_name = f'{method.__name__}_if_in_{lang_name}_{unit_kind}_generated_{unit_name}_correctly'
    return func_name


def generate_test_cases():
    lang_names = AbstractLangCodeTest.get_langs_where(lambda d: d.rules.features)
    for lang_name in lang_names:
        try:
            raw_data = AbstractLangCodeTest.data_loader.load(Path(lang_name) / '')
            dotdict = DotDict(data)
        except:
            continue

        unit_names = 'morphemes', 'graphemes'
        all_units = {unit_name: dotdict[unit_name].elems or DotDict() for unit_name in unit_names}
        for kind, units in all_units.items():
            expected_units = {key: val for key, val in units.expected.items() if key != 'skip'}
            for name, expected in expected_units.items():
                yield lang_name, kind, name, expected.get()


class UnitGenerationTest(AbstractLangCodeTest):
    @parameterized.expand(
        list(generate_test_cases()),
        name_func=get_func_name,
        skip_on_empty=True,
    )
    def test(self, lang_name: str, unit_kind: str, unit_name: str, expected: yaml_types):
        lang = self.load_lang(lang_name)
        units = lang.get_units(unit_kind)
        unit_label = f'{unit_kind[:-1].capitalize()} "{unit_name}"'
        self.assertIn(unit_name, units.keys(), f'{unit_label} has not been generated in "{lang_name}"')
        self.assertEqual(expected, units[unit_name], f'{unit_label} has not expected fields. \nFound: {units[unit_name]}\nExpected: {expected}')




