from __future__ import annotations

import functools
import inspect
from dataclasses import dataclass
from itertools import tee
from pathlib import Path
from typing import Callable, Iterable, Sequence

import pydash as _
import yaml
from pydash import chain as c
from toolz import valfilter
from toolz.curried import *

from src import utils
from src.constants import ST
from src.dot_dict import DotDict
from src.lang_factory import LangFactory
from src.language_components import Language
from src.loaders import LangDataLoader
from src.utils import if_, to_tuple
from tests.abstractTest import AbstractTest

val = _.method('value')

yaml_types = dict | bool | str | int | None


@dataclass
class Paths:
    LANGUAGES = Path(__file__).parent / 'languages'
    DEFAULTS = LANGUAGES / 'general_defaults.yaml'


class AbstractLangCodeTest(AbstractTest):
    accepted_similarity = .5

    defaults = yaml.safe_load(open(Paths.DEFAULTS, 'r'))
    data_loader = LangDataLoader(Paths.LANGUAGES)
    lang_factory = LangFactory(Paths.LANGUAGES)

    not_language_files = ('general_defaults', )
    all_paths: list[Path]
    all_langs: list[str]
    all_lang_data: dict[str, dict]
    all_test_properties: dict[str, dict]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loaded_langs = {}
        self.maxDiff = None

    def load_lang(self, name: str) -> Language:
        if name not in self._loaded_langs:
            self._loaded_langs[name] = self.lang_factory.load(name)
        return self._loaded_langs[name]

    @classmethod
    def init(cls):
        cls.all_paths = [path for path in Paths.LANGUAGES.iterdir() if path.stem not in cls.not_language_files]
        cls.all_langs = [path.stem for path in cls.all_paths]
        cls.all_lang_data = {lang: cls.data_loader.load(lang) for lang in cls.all_langs}
        cls.all_test_properties: dict[str, dict] = c(cls.all_lang_data).map_values(
            c().get(ST.GENERAL).apply(c(cls.defaults).merge).apply(val).get('test_properties')
        ).value()
        # cls.all_test_properties: dict[str, dict] = _.map_values(cls.all_lang_data, lambda data: _.merge(cls.defaults, data.get(ST.GENERAL, {})))
        # cls.all_test_properties: dict[str, dict] = {lang: DotDict(data.get('general'), defaults=cls.defaults).test_properties for lang, data in cls.all_data.items()}

    @classmethod
    def get_langs_where(cls, condition: Callable[[DotDict], bool] = lambda _: True) -> Iterable[str]:
        return valfilter(condition, cls.all_test_properties).keys()


def test_generator(orig_class):
    is_defined = c().ends_with('__').negate()

    parent = orig_class.__base__
    parent_dict = {name: getattr(parent, name) for name in filter(is_defined, dir(parent))}

    # child_dict = itemfilter(_.flow(all, _.over_args(_.to_list, is_defined, inspect.isfunction)), orig_class.__dict__)
    child_dict = keyfilter(is_defined, orig_class.__dict__)
    child_dict = valfilter(inspect.isfunction, child_dict)
    #child_dict = toolz.itemfilter(_.over_args(operator.and_, is_defined, inspect.isfunction), child_dict)
    for name, method in child_dict.items():
        args = inspect.getfullargspec(method).args
        new_method = method
        if args[0] == 'self':
            signature = inspect.signature(method)
            parameters = list(signature.parameters.values())
            new_param = inspect.Parameter('cls', inspect.Parameter.POSITIONAL_OR_KEYWORD)
            if args[0] == 'self':
                parameters = parameters[1:]
                # parameters.__setitem__(0, new_param)
            else:
                pass # parameters.insert(0, new_param)
            new_signature = signature.replace(parameters=parameters)
            method.__signature__ = new_signature
            # TODO: clean up
            # wraps prob. useless
            new_method = functools.wraps(method)(lambda *args, **kwargs: method(orig_class, *args, **kwargs))
        #@wraps
        setattr(orig_class, name, new_method)
    return orig_class


@test_generator
class Generator:
    test = AbstractLangCodeTest

    lang_name_regexes: Sequence[str] | str = tuple()
    lang_name_reduc: Callable[[Iterable], bool] = None

    props_paths_to_include: Sequence[str] = tuple()
    props_reduc: Callable[[Iterable], bool] = None

    props_paths_to_add: Sequence[str] = tuple()

    get_lang_parameters: Callable[[str], tuple] = lambda _: tuple()

    @classmethod
    def should_test_name(cls, lang_name: str) -> bool:
        match_name = cls._get_or_set('is_matching', get_is_matching, *to_tuple(cls.lang_name_regexes), reduc=cls.lang_name_reduc)
        return match_name(lang_name)

    @classmethod
    def should_test_props(cls, props: dict):
        reduc = if_(cls.props_reduc).else_(all)
        return reduc(_.properties(*cls.props_paths_to_include)(props))

    @classmethod
    def should_test(cls, lang_name):
        return cls.should_test_name(lang_name) and cls.should_test_props(AbstractLangCodeTest.all_test_properties[lang_name])

    @classmethod
    def generate_test_cases_for_lang(cls, lang_name) -> list[tuple]:
        return [
             (lang_name, ) + cls.get_props(lang_name) + to_tuple(cls.get_lang_parameters(lang_name)),
        ]

    @classmethod
    def generate_test_langs(cls) -> Iterable[str]:
        return filter(cls.should_test, AbstractLangCodeTest.all_lang_data)

    @classmethod
    def generate_test_cases(cls) -> Iterable[tuple]:
        return _.flat_map(cls.generate_test_langs(), cls.generate_test_cases_for_lang)

    @classmethod
    def _get_or_set(cls, name: str, factory, *args, **kwargs):
        if not (func := getattr(cls, name, None)):
            func = factory(*args, **kwargs)
            setattr(cls, name, func)
        return func

    # decorator
    @classmethod
    def add_props(cls, *paths: str):
        return lambda f: lambda lang_name: f(lang_name) + cls.get_props(lang_name, paths)

    @classmethod
    def get_props(cls, lang_name: str, paths: Sequence[str] = None) -> tuple[yaml_types]:
        props = cls.test.all_test_properties[lang_name]
        paths = to_tuple(paths or cls.props_paths_to_add)
        return tuple(_.properties(*paths)(props))


# func creator
def get_is_matching(*regexes: str, reduc=None):
    reduc = if_(reduc).elif_(regexes).then_(any, all)
    _is_matching = utils.is_matching(reduc, regexes)
    return _is_matching


def get_get_props(props, *paths):
    return _.properties(paths)(props)




# decorator
def add_cond(*conds):
    raise NotImplementedError




AbstractLangCodeTest.init()


# def matching():
#     def decorator(func):
#         def wrapper():
#             langs = AbstractLangCodeTest.get_langs_matching(*regexes, reduc=reduc)
#             return func(langs)
#         return wrapper
#     return decorator