from dataclasses import dataclass, field
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
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=False)
class EmeCase:
    short: str
    eme: dict
    checks: list[Check] = field(default_factory=list)  # Assumes uni_checks defined
    valid: bool = True
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=False)
class ConfCase:
    short: str
    conf: list[list | dict] | list | dict
    valid: bool = True
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=False)
class TC:
    short: str
    conf_cases: list[ConfCase]
    eme_cases: list[EmeCase]
    uni_checks: list[Check] = field(default_factory=list)
    tags: list = field(default_factory=list)
    preexistings: Preex = field(default_factory=Preex)
    skip: str | Exception | bool = False


@dataclass(frozen=False)
class tc:
    short: str
    conf: list | dict
    eme: dict  #?
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
            ConfCase(short=correlation,                         conf={'type': correlation, 'elems': list(features)}),
            ConfCase(short=f'{correlation} as elems',           conf={correlation: list(features)}),
            ConfCase(short=f'{correlation} as elems and types', conf={correlation: list(features), 'type': correlation}, valid=False),
        ]

    @classmethod
    def generate_tcs(cls):
        return [
        TC(
            short='base',
            conf_cases=[
                ConfCase(short='direct list',
                    conf=['noun', 'verb', 'modifier'],
                ),
                ConfCase(short='direct dict',
                    conf={'noun': None, 'verb': None, 'modifier': None},
                ),
                ConfCase(short='list elems',
                    conf={'elems': ['noun', 'verb', 'modifier']},
                ),
                ConfCase(short='dict elems',
                    conf={'elems': {'noun': None, 'verb': None, 'modifier': None}},
                ),
                ConfCase(short='list elems and type ambi',
                    conf={'elems': ['noun', 'verb', 'modifier'], 'type': 'ambi'},
                ),
                ConfCase(short='dict elems and type ambi',
                    conf={'elems': {'noun': None, 'verb': None, 'modifier': None}, 'type': 'ambi'},
                ),
                ConfCase(short='list elems and type ambi',
                    conf={'ambi': ['noun', 'verb', 'modifier'], 'type': 'ambi'},
                ),
                *cls.get_basic_correlated('ambi', ['noun', 'verb', 'modifier']),
            ],
            eme_cases=[
                EmeCase(short='just dict',
                    eme={},
                    checks=[
                        Check('adjective', NotImplemented),
                        Check('modifier', False),
                    ],
                ),
                EmeCase(short='set True',
                    eme={'noun': True},
                    checks=[
                        Check('noun', True),
                        Check('verb', False),
                    ],
                ),
                EmeCase(short='set False',
                    eme={'modifier': False},
                    checks=[
                        Check('modifier', False),
                    ],
                ),
                EmeCase(short='set many',
                    eme={'verb': True, 'modifier': True},
                    checks=[
                        Check('verb', True),
                        Check('modifier', True),
                        Check('noun', False),
                    ],
                ),
            ]
         ),
        TC(short='base',
            conf_cases=cls.get_basic_correlated('joint', ['singular', 'dual', 'plural']),
            eme_cases=[
                EmeCase(short='set with few',
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
                ),
            ]
        ),
        TC(short='',
           conf_cases=[ConfCase(short='', conf={
                'gender': {'type': 'disjoint', 'elems': [
                    'masculine',
                    'feminine',
                    'neuter',
                ]}
            })],
           eme_cases=[
                EmeCase(short='set style',  eme={'gender': 'feminine'}),
                EmeCase(short='leaf style', eme={'feminine': True}),
            ],
           uni_checks=[Check('feminine', True, short='is subfeature'), Check('gender', 'feminine', short='get subfeature')]
           )
    ]  # TODO: Extend for nested

    @classmethod
    def map_to_many(cls, big_tc: TC) -> Iterable[tc] | list[tc]:
        if big_tc.short:
            big_tc.short = big_tc.short.strip() + ' '
        for conf_case in big_tc.conf_cases:
            adjusted_eme_cases = big_tc.eme_cases if big_tc.eme_cases and conf_case.valid else [EmeCase('', {}, [])]
            for eme_case in adjusted_eme_cases:
                if not eme_case.valid and not eme_case.short:
                    eme_case.short = 'invalid'
                eme_skip = utils.init_tc_fields(eme_case, Unit, 'eme')
                adjusted_checks = eme_case.checks + big_tc.uni_checks
                if not adjusted_checks or not conf_case.valid or not eme_case.valid:
                    adjusted_checks = [None]
                eme_part = f'with eme {eme_case.short}'
                for check in adjusted_checks:
                    conf_part = f'{big_tc.short}conf of {conf_case.short}'
                    check_part = f'gets {cls.get_check_short(check)}' if conf_case.valid and eme_case.valid else ''
                    conf_supplement = f'{eme_part} {check_part}' if conf_case.valid else 'is invalid'

                    short = f'{conf_part} {conf_supplement}'.strip()
                    tags = big_tc.tags + (eme_case.tags if conf_case.valid else []) + (check.tags if conf_case.valid and eme_case.valid else [])
                    yield tc(short=short, conf=conf_case.conf, eme=eme_case.eme, check=check,
                             is_conf_valid=conf_case.valid, is_eme_valid=eme_case.valid,
                             tags=tags, preexistings=big_tc.preexistings, skip=big_tc.skip or eme_skip,
                    )

    @classmethod
    def get_check_short(cls, check: Check) -> str:
        match check.expect:
            case bool(): return str(check.expect)
            case _: return str(check.short or check.expect)

    @classmethod
    def gather_tag_before_mapping_to_many(cls, tc: TC) -> Iterable[str] | Sequence[str]:
        checks = tc.uni_checks[:]
        for eme_case in tc.eme_cases:
            if eme_case.eme:
                eme_case.tags = eme_case.tags  # TODO
            checks.extend(eme_case.checks)
        for check in filter(bool, checks):
            check.tags
        return []

    @classmethod
    def gather_tags(cls, tc: tc) -> Iterable[str] | Sequence[str]:
        yield 'feature'
        yield 'valid-conf' if tc.is_conf_valid else 'invalid-conf'
        if tc.is_conf_valid:
            yield 'valid-eme' if tc.is_eme_valid else 'invalid-eme'
        if tc.is_conf_valid and tc.is_eme_valid and tc.check:
            match tc.check.expect:
                case bool() | None: yield f'get-feature-{tc.check.expect}'.lower()
                case 'NotImplemented': yield 'invalid-get-feature'
                case _: pass #raise ValueError
        if tc.skip:
            yield 'xfail'
        yield from tc.tags


@FeatureTCG.parametrize('tc')
def test(tc: tc):
    raise NotImplementedError('Think whether to construct features here or a lang (prob. the former)')
