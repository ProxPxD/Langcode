from __future__ import annotations

import pydash as _
from parameterized import parameterized
from pydash import chain as c

from tests.lang_code_test import AbstractLangCodeTest


# name_func=lambda method, param_num, params: f'{method.__name__}_{param_num}_' + get_lang_type(params[0][0])
def get_func_name(method, param_num, params):
    lang_name = params[0][0]
    func_name = f'{method.__name__}_if_{lang_name}_has_correct_test_properties'
    return func_name


class TestPropertiesCorrectnessTest(AbstractLangCodeTest):
    @parameterized.expand(
        AbstractLangCodeTest.all_langs,
        name_func=get_func_name
    )
    def test(self, lang_name: str):
        expected_properties = self.defaults['test_properties']
        actual_properties = self.all_test_properties[lang_name]

        to_check = _.keys(actual_properties)
        not_present = []
        while to_check:
            curr_path = to_check.pop()
            if _.has(expected_properties, curr_path):
                paths = c(_.get(actual_properties, curr_path)).keys().map_(lambda next_key: f'{curr_path}.{next_key}').value()
                to_check.extend(paths)
            else:
                not_present.append(curr_path)
        if not_present:
            printable_paths = c(not_present).map_(lambda p: f' - {p}').join('\n').value()
            self.fail(f'Found incorrect properties in {lang_name}:\n{printable_paths}')





