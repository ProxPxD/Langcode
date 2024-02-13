from __future__ import annotations

from parameterized import parameterized

from src.utils import to_list
from tests.lang_code_test import DotDict, AbstractLangCodeTest


# name_func=lambda method, param_num, params: f'{method.__name__}_{param_num}_' + get_lang_type(params[0][0])
def get_func_name(method, param_num, params):
    lang_name = params[0][0]
    func_name = f'{method.__name__}_if_{lang_name}_has_correct_test_properties'
    return func_name


class TestCorrectnessTest(AbstractLangCodeTest):
    @parameterized.expand(
        AbstractLangCodeTest.all_langs,
        name_func=get_func_name
    )
    def test(self, lang_name: str):
        expected_properties = DotDict(DotDict.orig_defaults).test_properties
        actual_properties = self.all_test_properties[lang_name]

        to_check = list(map(to_list, actual_properties.get().keys()))
        not_present = []
        while to_check:
            curr_path = to_check.pop()
            if curr_path in expected_properties:
                paths = map(lambda next_key: curr_path + [next_key], filter(bool, actual_properties[curr_path].keys()))
                to_check.extend(paths)
            else:
                not_present.append(curr_path)
        if not_present:
            printable_paths = map(lambda path: ' - ' + ('.'.join(path)), not_present)
            self.fail(f'Found incorrect properties in {lang_name}:\n' + '\n'.join(printable_paths))





