from __future__ import annotations

import functools
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence, Type

import pydash as _
import yaml
from parameterized import parameterized
from pydash import chain as c
from toolz import valfilter
from toolz.curried import *
from typing_extensions import deprecated

from src import utils
from src.constants import ST
from src.exceptions import LangCodeException
from src.lang_factory import LangFactory
from src.lang_typing import OrMore
from src.language_components import Language, Unit
from src.loaders import LangDataLoader
from src.utils import if_, to_tuple, is_
from tests.abstractTest import AbstractTest, TestGenerator

val = _.method('value')

yaml_types = dict | bool | str | int | None


@dataclass
class Paths:
    LANGUAGES = Path(__file__).parent / 'languages'
    DEFAULTS = LANGUAGES / 'general_defaults.yaml'


class LangCodeTestGenerator(TestGenerator):
    @classmethod
    def from_conf_and_is_skip(cls, lang_code_class: Type, conf: OrMore[dict | str], *args, **kwargs):
        match conf:
            case _ if is_((list, tuple), conf): object_or_more = list(map(lambda conf: cls.from_conf(lang_code_class, conf, *args, **kwargs), conf))
            case _: object_or_more = cls.from_conf(lang_code_class, conf, *args, **kwargs)
        return object_or_more, cls.is_skip(object_or_more)

    @classmethod
    def from_conf(cls, lang_code_class: Type, conf: dict | str, kind=None) -> Unit | str:
        try:
            eme = lang_code_class.from_conf(conf)
            if kind:
                eme.kind = kind
        except NotImplementedError:
            eme = 'Not Implemented'
        except LangCodeException as e:
            eme = f'LangCodeException - Check test parameters or conf {conf}\n{e}'
        except Exception as e:
            eme = e
        return eme

    @classmethod
    def is_skip(cls, creation: OrMore[Unit | str]) -> bool:
        match creation:
            case _ if is_((list, tuple), creation): return creation and any(filter(cls.is_skip, creation))
            case _: return isinstance(creation, (str, Exception))


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
    @deprecated('Think if implement or remove')
    def get_langs_where(cls, condition: Callable[[dict], bool] = lambda _: True) -> Iterable[str]:
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
    def generate_test_cases_parameters_for_lang(cls, lang_name) -> list[tuple]:
        params = (lang_name, ) + cls.get_props(lang_name) + to_tuple(cls.get_lang_parameters(lang_name))
        return [params]

    @classmethod
    def generate_test_langs(cls) -> Iterable[str]:
        return filter(cls.should_test, AbstractLangCodeTest.all_lang_data)

    @classmethod
    def generate_test_cases(cls) -> Iterable[tuple]:
        return _.flat_map(cls.generate_test_langs(), cls.generate_test_cases_parameters_for_lang)

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

    @classmethod
    def create_props_for_test_case(cls, params):
        return {}

    @classmethod
    def parametrize(cls,
            input,
            name_func: Callable[..., str] = None,
            **expand_kwargs
        ):
        frame = inspect.currentframe().f_back.f_locals

        def wrapper(f, *args, **kwargs):
            parameterized.expand(input, namespace=frame, name_func=name_func, **expand_kwargs)(f)

            all_params = parameterized.input_as_callable(input)()
            digits = len(str(len(all_params) - 1))
            for num, params in enumerate(all_params):
                name = name_func(f, f'{num:0>{digits}}', params)
                setattr(frame[name], 'props', cls.create_props_for_test_case(params.args))

        return wrapper


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


# eme matching():
#     eme decorator(func):
#         eme wrapper():
#             langs = AbstractLangCodeTest.get_langs_matching(*regexes, reduc=reduc)
#             return func(langs)
#         return wrapper
#     return decorator