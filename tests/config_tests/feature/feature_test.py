from dataclasses import dataclass, field
from itertools import product
from typing import Iterable, Sequence

import pytest

import tests.lang_code_test_utils as utils
from src.lang_typing import YamlType
from src.language_components import Unit
from tests.lang_code_test_utils import Preex, LangCodeTCG


@dataclass(frozen=False)
class Check:
    feature: str
    expect: YamlType = True
    short: str = ''


@dataclass(frozen=False)
class EmeCase:
    short: str
    eme: dict
    checks: list[Check]
    valid: bool = True


@dataclass(frozen=False)
class ConfCase:
    short: str
    conf: list[list | dict] | list | dict
    valid: bool = True


@dataclass(frozen=False)
class TC:
    short: str
    conf_cases: list[ConfCase]
    eme_cases: list[EmeCase]
    tags: list = field(default_factory=list)
    preexistings: Preex = field(default_factory=Preex)
    skip: str | Exception | bool = False


@dataclass(frozen=False)
class tc:
    short: str
    conf: list | dict
    eme: dict
    check: Check
    is_conf_valid: bool = True
    is_eme_valid: bool = True
    tags: list = field(default_factory=list)
    preexistings: Preex = field(default_factory=Preex)
    skip: str | Exception | bool = False


class FeatureTCG(LangCodeTCG):
    """
    aims to ensure the right functionality of features
    """
    # TODO: consider whether to use a bin- or a ternary logic, for now, a binary, maybe optional?

    @classmethod
    def get_basic_correlated(cls, correlation: str, features: dict | list) -> list[ConfCase]:
        return [
            ConfCase(
                short=correlation,
                conf={
                    'type': correlation,
                    'elems': list(features)
                }
            ),
            ConfCase(
                short=f'{correlation} as elems',
                conf={
                    'joint': list(features)
                }
            ),
            ConfCase(
                short=f'{correlation} as elems and types',
                valid=False,
                conf={
                    correlation: list(features)
                }
            ),
        ]

    @classmethod
    def generate_tcs(cls):
        return [
        TC(
            short='base',
            conf_cases=[
                ConfCase(
                    short='direct list',
                    conf=['noun', 'verb', 'modifier'],
                ),
                ConfCase(
                    short='direct dict',
                    conf={'noun': None, 'verb': None, 'modifier': None},
                ),
                ConfCase(
                    short='list elems',
                    conf={'elems': ['noun', 'verb', 'modifier']},
                ),
                ConfCase(
                    short='dict elems',
                    conf={'elems': {'noun': None, 'verb': None, 'modifier': None}},
                ),
                ConfCase(
                    short='list elems with type ambi',
                    conf={'elems': ['noun', 'verb', 'modifier'], 'type': 'ambi'},
                ),
                ConfCase(
                    short='dict elems with type ambi',
                    conf={'elems': {'noun': None, 'verb': None, 'modifier': None}, 'type': 'ambi'},
                ),
                ConfCase(
                    short='list elems with type ambi',
                    conf={'ambi': ['noun', 'verb', 'modifier'], 'type': 'ambi'},
                ),
                *cls.get_basic_correlated('ambi', ['noun', 'verb', 'modifier']),
            ],
            eme_cases=[
                EmeCase(
                    short='just dict',
                    eme={},
                    checks=[
                        Check('adjective', NotImplemented),
                        Check('modifier', False),
                    ],
                ),
                EmeCase(
                    short='set True',
                    eme={'noun': True},
                    checks=[
                        Check('noun', True),
                        Check('verb', False),
                    ],
                ),
                EmeCase(
                    short='set False',
                    eme={'modifier': False},
                    checks=[
                        Check('modifier', False),
                    ],
                ),
                EmeCase(
                    short='set many',
                    eme={'verb': True, 'modifier': True},
                    checks=[
                        Check('verb', True),
                        Check('modifier', True),
                        Check('noun', False),
                    ],
                ),
            ]
         ),
        TC(
            short='base',
            conf_cases=cls.get_basic_correlated('joint', ['singular', 'dual', 'plural']),
            eme_cases=[
                EmeCase(
                    short='set with few',
                    eme={'dual': True, 'plural': True},
                    checks=[Check('singular', False), Check('dual'), Check('plural')],
                )
            ]
        ),
        TC(
            short='base',
            conf_cases=cls.get_basic_correlated('disjoint', ['high', 'mid', 'low']),
            eme_cases=[
                EmeCase(
                    short='valid',
                    eme={'high': True},
                    checks=[Check('high', True)],
                ),
                EmeCase(
                    short='',
                    valid=False,
                    eme={'high': True, 'low': True},
                    checks=[],
                ),
            ]
        ),
    ]  # TODO: Extend for nested

    @classmethod
    def map_to_many(cls, big_tc: TC) -> Iterable[tc] | list[tc]:
        if big_tc.short:
            big_tc.short = big_tc.short.strip() + ' '
        for conf_case in big_tc.conf_cases:
            adjusted_eme_cases = big_tc.eme_cases if big_tc.eme_cases and conf_case.valid else [EmeCase('', {}, [None])]
            for eme_case in adjusted_eme_cases:
                if not eme_case.valid and not eme_case.short:
                    eme_case.short = 'invalid'
                eme_skip = utils.init_tc_fields(eme_case, Unit, 'eme')
                adjusted_checks = eme_case.checks if eme_case.checks and eme_case.valid else [None]
                eme_part = f'with eme {eme_case.short}'
                for check in adjusted_checks:
                    conf_part = f'{big_tc.short}conf of {conf_case.short}'
                    check_part = f'gets {cls.get_check_short(check)}' if eme_case.valid else ''
                    conf_suplement = f'{eme_part} {check_part}' if conf_case.valid else 'is invalid'

                    short = f'{conf_part} {conf_suplement}'.strip()
                    yield tc(short=short, conf=conf_case.conf, eme=eme_case.eme, check=check,
                             is_conf_valid=conf_case.valid, is_eme_valid=eme_case.valid,
                             tags=big_tc.tags, preexistings=big_tc.preexistings, skip=big_tc.skip or eme_skip,
                    )

    @classmethod
    def get_check_short(cls, check: Check) -> str:
        if not check:
            return ''
        match check.expect:
            case bool(): return str(check.expect)
            case _: return str(check.short or check.expect)

    @classmethod
    def gather_tags(cls, tc) -> Iterable[str] | Sequence[str]:
        yield 'feature'
        #yield from cls.gather_def_tags(tc.thenee)
        #yield from cls.gather_feature_tags(tc.thenee)


@FeatureTCG.parametrize('tc')
def test(tc):
    if tc.skip:
        pytest.xfail(tc.skip)

    raise NotImplementedError('Think whether to construct features here or a lang (prob. the former)')
