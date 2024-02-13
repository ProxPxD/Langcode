from __future__ import annotations

from parameterized import parameterized

from src.utils import to_list
from tests.lang_code_test import DotDict, AbstractLangCodeTest


# name_func=lambda method, param_num, params: f'{method.__name__}_{param_num}_' + get_lang_type(params[0][0])
def get_func_name(method, param_num, params):
    lang_name = params[0][0]
    func_name = f'{method.__name__}_if_{lang_name}_has_correct_test_properties'
    return func_name


class FeatureGenerationTest(AbstractLangCodeTest):
    @parameterized.expand(
        AbstractLangCodeTest.get_langs_where(lambda d: d.rules.features),
        name_func=get_func_name
    )
    def test(self, lang_name: str):
        self.fail(NotImplemented)




