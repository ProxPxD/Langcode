from __future__ import annotations

from collections import namedtuple
from typing import Callable, Sequence, Tuple

import pytest
from neo4j.graph import Node, Relationship
from neomodel import db

from old.neomodel_utitilities import Neo4jQuerer
from testing.core.test_case_generator import TCG

PERSON = 'Person'
BOOK = 'Book'
IS_AUTHOR_OF = 'IS_AUTHOR_OF'
KNOWS = 'KNOWS'
MG_NAME = 'Marcin Giełzak'
JD_NAME = 'Jakub Dymek'
AZ_NAME = 'Adrian Zandberg'
WL_NAME = 'Wieczna Lewica'


class RelationQuerableTCG(TCG):
    map = tuple
    init_query = f'''
    CREATE 
        (mg:{PERSON} {{name: '{MG_NAME}'}})-[:{IS_AUTHOR_OF}]->(wl: {BOOK} {{name: '{WL_NAME}'}}),
        (mg)-[:{KNOWS}]->(jd:{PERSON} {{name: '{JD_NAME}'}})-[:{KNOWS}]->(az:{PERSON} {{name: '{AZ_NAME}'}})
    '''

    tc = namedtuple('tc', ['name', 'method', 'query_params', 'expected'])
    tcs = [
        tc(
            name='Simple Query Directionless',
            method=Neo4jQuerer.query,
            query_params=(PERSON, IS_AUTHOR_OF, BOOK),
            expected=[
                [([PERSON], dict(name=MG_NAME)), ([IS_AUTHOR_OF], {}), ([BOOK], dict(name=WL_NAME))],
            ],
        ),
        tc(
            name='Exact Hop Query Directionless',
            method=Neo4jQuerer.query,
            query_params=(PERSON, [KNOWS, '*2'], PERSON),
            expected=[
                [([PERSON], dict(name=MG_NAME)), [([KNOWS], {}), ([KNOWS], {})], ([PERSON], dict(name=AZ_NAME))],
                [([PERSON], dict(name=AZ_NAME)), [([KNOWS], {}), ([KNOWS], {})], ([PERSON], dict(name=MG_NAME))],
            ],
        ),
        tc(
            name='Any Hop Query Directed',
            method=Neo4jQuerer.query,
            query_params=(PERSON, [KNOWS, '*', '>'], PERSON),
            expected=[
                [([PERSON], dict(name=MG_NAME)), [([KNOWS], {})], ([PERSON], dict(name=JD_NAME))],
                [([PERSON], dict(name=MG_NAME)), [([KNOWS], {}), ([KNOWS], {})], ([PERSON], dict(name=AZ_NAME))],
                [([PERSON], dict(name=JD_NAME)), [([KNOWS], {})], ([PERSON], dict(name=AZ_NAME))],
            ],
        ),
        tc(
            name='Two Relations',
            method=Neo4jQuerer.query,
            query_params=(PERSON, KNOWS, PERSON, IS_AUTHOR_OF, BOOK),
            expected=[
                [([PERSON], dict(name=JD_NAME)), ([KNOWS], {}), ([PERSON], dict(name=MG_NAME)), ([IS_AUTHOR_OF], {}), ([BOOK], dict(name=WL_NAME))],
            ],
        ),
        tc(
            name='Single Node by Props',
            method=Neo4jQuerer.query,
            query_params=([PERSON, {'name': JD_NAME}],),
            expected=[
                [([PERSON], dict(name=JD_NAME),)],
            ],
        ),
        tc(
            name='Unnamed Relation',
            method=Neo4jQuerer.query,
            query_params=(PERSON, None, BOOK),
            expected=[
                [([PERSON], dict(name=MG_NAME)), ([IS_AUTHOR_OF], {}), ([BOOK], dict(name=WL_NAME))],
            ],
        ),
        tc(
            name='First Node',
            method=Neo4jQuerer.query,
            query_params=dict(args=(PERSON, IS_AUTHOR_OF, BOOK), index=0, kind='n'),
            expected=[
                [([PERSON], dict(name=MG_NAME))],
            ],
        ),
        tc(
            name='Second Node',
            method=Neo4jQuerer.query,
            query_params=dict(args=(PERSON, IS_AUTHOR_OF, BOOK), index=1, kind='n'),
            expected=[
                [([BOOK], dict(name=WL_NAME))],
            ],
        ),
        tc(
            name='Last Node',
            method=Neo4jQuerer.query,
            query_params=dict(args=(PERSON, IS_AUTHOR_OF, BOOK), index=-1, kind='n'),
            expected=[
                [([BOOK], dict(name=WL_NAME))],
            ],
        ),
        tc(
            name='Last Graphel',
            method=Neo4jQuerer.query,
            query_params=dict(args=(PERSON, IS_AUTHOR_OF, BOOK), index=-1, kind='e'),
            expected=[
                [([BOOK], dict(name=WL_NAME))],
            ],
        ),
        tc(
            name='Last but one Graphel',
            method=Neo4jQuerer.query,
            query_params=dict(args=(PERSON, IS_AUTHOR_OF, BOOK), index=-2, kind='e'),
            expected=[
                [([IS_AUTHOR_OF], {})],
            ],
        ),
        tc(
            name='Second Graphel',
            method=Neo4jQuerer.query,
            query_params=dict(args=(PERSON, IS_AUTHOR_OF, BOOK), index=1, kind='e'),
            expected=[
                [([IS_AUTHOR_OF], {}),],
            ],
        ),
        tc(
            name='Exact Return',
            method=Neo4jQuerer.query,
            query_params=dict(args=(PERSON, IS_AUTHOR_OF, BOOK), kind='n', exact_return=True),
            expected=[([PERSON], dict(name=MG_NAME)), ([BOOK], dict(name=WL_NAME))],
        ),
        tc(
            name='Query Adv shorted names',
            method=Neo4jQuerer.query_adv,
            query_params=dict(
                args=[
                    [PERSON, IS_AUTHOR_OF, (BOOK, dict(name=WL_NAME))],
                    [PERSON, KNOWS, (PERSON, dict(name=JD_NAME))],
                ],
                names=[
                    ['author'],
                    ['author']
                ],
                to_return='author'
            ),
            expected=[
                [([PERSON], dict(name=MG_NAME))]
            ],
        ),
    ]

    @classmethod
    def generate_tcs(cls) -> list:
        db.cypher_query(cls.init_query)
        return cls.tcs


def get_labels(graphel: Node | Relationship) -> list[str]:
    try:
        return graphel.labels
    except AttributeError:
        return [graphel.type]


def normalize_query_params(query_params: Sequence | dict) -> Tuple[Sequence, dict]:
    if isinstance(query_params, Sequence):
        return query_params, {}
    else:
        args, kwargs = query_params['args'], query_params
        del kwargs['args']
        return args, kwargs


def is_graphel_same(a_graphel, e_graphel) -> bool:
    e_labels, e_props = e_graphel
    return set(get_labels(a_graphel)) == set(e_labels) and dict(a_graphel.items()) == e_props


def is_row_same(a_row, e_row):
    if hasattr(a_row, 'element_id'):
        return is_graphel_same(a_row, e_row)
    if len(a_row) != len(e_row):
        return False
    for a_graphel, e_graphel in zip(a_row, e_row):
        if hasattr(a_graphel, 'element_id'):
            if not is_graphel_same(a_graphel, e_graphel):
                return False
        elif not is_row_same(a_graphel, e_graphel):
            return False
    return True


@RelationQuerableTCG.parametrize(['name', 'method', 'query_params', 'expected'])
def test(name, method: Callable, query_params: tuple | dict, expected):
    args, kwargs = normalize_query_params(query_params)
    table, names = method(*args, **kwargs)

    assert len(table) == len(expected)
    for e_row in expected:
        for a_row in table:
            if is_row_same(a_row, e_row):
                break
        else:
            pytest.fail(f'Did not found a mathing row for {e_row}')
