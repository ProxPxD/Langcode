from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from itertools import chain
from typing import Type, Optional, Iterable, Sequence

import pydash as _
from more_itertools import flatten
from pydash import chain as c
from toolz.curried import *

from src.exceptions import LangCodeException
from src.lang_typing import OrMore
from src.language_components import Unit
from src.utils import is_, is_not_dict, is_str
from tests.test_case_generator import TCG


@dataclass(frozen=False)
class Preex:  # Preexisting
    morphemes: list = field(default_factory=list)
    graphemes: list = field(default_factory=list)
    morpheme_features: list = field(default_factory=list)
    grapheme_features: list = field(default_factory=list)


def from_conf_and_is_skip(lang_code_class: Type, conf: OrMore[dict | str], *args, **kwargs):
    match conf:
        case _ if is_((list, tuple), conf): object_or_more = list(map(lambda conf: from_conf(lang_code_class, conf, *args, **kwargs), conf))
        case _: object_or_more = from_conf(lang_code_class, conf, *args, **kwargs)
    return object_or_more, is_skip(object_or_more)


def from_conf(lang_code_class: Type, conf: dict | str, kind=None) -> Unit | str:
    try:
        eme = lang_code_class.from_conf(conf)
        if kind:
            eme.kind = kind
    except NotImplementedError:
        eme = 'Not Implemented'
    except LangCodeException as e:
        eme = f'LangCodeException - Check test parameters or conf {conf}\n{traceback.format_exc()}'
    except Exception:
        eme = traceback.format_exc()
    return eme


def is_skip(creation: OrMore[Unit | str]) -> bool:
    match creation:
        case _ if not creation: return False
        case _ if is_((list, tuple), creation): any(filter(is_skip, creation))
        case _: return isinstance(creation, (str, Exception))


def choose_skip_reason(*args) -> Optional[str]:
    if len(args) % 2 != 0:
        raise ValueError('choose_skip_reason expects an even numbers (bool, result, ...)')
    get_msg_if_skip = lambda skip_msg: skip_msg[1] if skip_msg[0] else None
    return c(args).chunk(2).map(get_msg_if_skip).filter(bool).head().value()


def init_tc_fields(tc, lang_code_class: Type, fields: str | Sequence[str], *args) -> Optional[str]:
    args = (tc, lang_code_class, fields, *args)
    if len(args) % 3 != 0:
        raise ValueError('init_tc_fields expects an arg arity divisible by 3 (tc, class, fields...)')

    for tc, lang_code_class, fields in _.chunk(args, 3):
        fields = (fields, ) if isinstance(fields, str) else fields
        for field in fields:
            inited, skip = from_conf_and_is_skip(Unit, getattr(tc, field))
            if skip:
                return inited
            setattr(tc, field, inited)
    return None


class LangCodeTCG(TCG):
    @classmethod
    def gather_def_tags(cls, definition) -> Iterable[str]:
        match definition:
            case None: yield 'none'
            case str() if definition.isalpha(): yield 'string'
            case str() if not definition.isalpha(): yield 'regex'

    @classmethod
    def gather_feature_tags(cls, defi) -> Iterable[str]:
        # TODO: idea separate a feature extractor and compare some outside to decide if a feature has to change or be used, etc.
        if is_not_dict(defi):
            return

        feature_dict = {  # TODO: think of tree tagging
            'gender': ['masculine', 'feminine', 'neuter'],
            'pos': ['noun', 'verb', 'adjective', 'adverb'],
            'number': ['singular', 'plural'],
        }

        features = list(chain(feature_dict.keys(), flatten(feature_dict.values())))
        is_any = False
        for feature in features:  # TODO: think of test-wide approach
            if feature not in defi:
                continue
            is_any = True
            yield feature
            match val := defi[feature]:
                case str(): yield val
                case bool(): pass   # TODO: think of true/false dict tagging?
                case list(): yield from cls.gather_feature_tags(val)
                case dict(): yield from cls.gather_feature_tags(val)
                case _: raise ValueError(f'Did not expected {val} on tagging')
        if is_any:
            yield 'explicit-features'  # TODO: think
        return []

