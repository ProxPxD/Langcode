from __future__ import annotations

import traceback

from parameterized import parameterized
from pyxdameraulevenshtein import damerau_levenshtein_distance

from src.exceptions import InvalidYamlException, InvalidPathException, ConflictingKeysException
from tests.lang_code_test import Paths, AbstractLangCodeTest, Generator, test_generator
import pydash as _
from pydash import chain


# @generator
# class LoadingTestGenerator(Generator):
#     test_1 = lambda x: x
#     # generate_test_case = lambda lang_name: Generator.generate_test_case(lang_name) + AbstractLangCodeTest.all_test_properties
#
#     @classmethod
#     def test_2(cls, x):
#         return x
#
#     def test_3(self, x):
#         return x

def get_func_name(method, param_num, params):
    lang_name, valid_schema, should_load = params[0]
    general = AbstractLangCodeTest.all_test_properties[lang_name]
    state = 'is_valid' if valid_schema and general['valid_restrictions'] else\
            'violates_restrictions' if valid_schema and not general['valid_restrictions'] else\
            'is_invalid' if not valid_schema else NotImplemented
    func_name = f'{method.__name__}_if_{lang_name}_{state}'.lower().replace('-', '_')
    return func_name


@test_generator
class LoadingTestGenerator(Generator):
    props_paths_to_add = ('valid_schema', 'should_load')
    lang_name_regexes = ''

    @classmethod
    def create_props_for_test_case(cls, params):
        lang = params[0]
        props = cls.test.all_test_properties[lang]
        return {
            'features': bool(props.get('features', False))
        }


class LoadingTest(AbstractLangCodeTest):
    """
        description: The test checks if the configurations load or fail accordingly to the configuration correctness
    """
    # @parameterized.expand(
    #     LoadingTestGenerator.generate_test_cases(),
    #     name_func=get_func_name
    # )
    @LoadingTestGenerator.parametrize(
        LoadingTestGenerator.generate_test_cases(),
        name_func=get_func_name,
    )
    def test(self, lang_name: str, valid_schema, should_load, message=None):
        # TODO: consider spliting into many functions
        # TODO: add messages according to state
        try:
            lang = self.lang_factory.load(lang_name)
        except NotImplementedError:
            self.fail(traceback.format_exc())
        except ConflictingKeysException:
            self.fail(f'Language {lang_name} has conflicting keys')
        except InvalidYamlException as iye:
            if valid_schema:
                self.fail(f"Language {lang_name} should be valid, but it's not, {iye.reason}")
            if message:
                dl = damerau_levenshtein_distance(iye.args[-1], message)
                self.assertGreater(dl, self.accepted_similarity, f'Wrong message! Got {iye.reason}, but expected {message}')
        except InvalidPathException:
            self.fail(f'Language {lang_name} does not exist in {Paths.LANGUAGES}')
        else:
            if message:
                self.fail(f'Language {lang_name} should be invalid, but succeeds to load. Expected message: {message}')





