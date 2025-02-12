from __future__ import annotations

import logging
from collections import namedtuple
from itertools import zip_longest
from typing import Callable, Sequence, Tuple

import pytest
from neo4j.graph import Node, Relationship
from neomodel import db

from src.neomodel_utitilities.neomixins import IRelationQuerable
from src.neomodel_utitilities.neoutils import Neo4jQuerer
from tests.test_case_generator import TCG


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

    tc = namedtuple('tc', ['name', 'method', 'query_args', 'expected'])
    tcs = [
        tc(
            name='Simple Query Directionless',
            method=Neo4jQuerer.query,
            query_args=(PERSON, IS_AUTHOR_OF, BOOK),
            expected=[
                [([PERSON], dict(name=MG_NAME)), ([BOOK], dict(name=WL_NAME)), ([IS_AUTHOR_OF], {})],
            ],
        ),
        tc(
            name='Exact Hop Query Directionless',
            method=Neo4jQuerer.query,
            query_args=(PERSON, [KNOWS, '*2'], PERSON),
            expected=[
                [([PERSON], dict(name=MG_NAME)), ([PERSON], dict(name=AZ_NAME)), [([KNOWS], {}), ([KNOWS], {})]],
                [([PERSON], dict(name=AZ_NAME)), ([PERSON], dict(name=MG_NAME)), [([KNOWS], {}), ([KNOWS], {})]],
            ],
        ),
        tc(
            name='Any Hop Query Directed',
            method=Neo4jQuerer.query,
            query_args=(PERSON, [KNOWS, '*', '>'], PERSON),
            expected=[
                [([PERSON], dict(name=MG_NAME)), ([PERSON], dict(name=JD_NAME)), [([KNOWS], {})]],
                [([PERSON], dict(name=MG_NAME)), ([PERSON], dict(name=AZ_NAME)), [([KNOWS], {}), ([KNOWS], {})]],
                [([PERSON], dict(name=JD_NAME)), ([PERSON], dict(name=AZ_NAME)), [([KNOWS], {})]],
            ],
        ),
        tc(
            name='Two Relations',
            method=Neo4jQuerer.query,
            query_args=(PERSON, KNOWS, PERSON, IS_AUTHOR_OF, BOOK),
            expected=[
                [([PERSON], dict(name=JD_NAME)), ([PERSON], dict(name=MG_NAME)), ([BOOK], dict(name=WL_NAME)), ([KNOWS], {}), ([IS_AUTHOR_OF], {})],
            ],
        ),
        tc(
            name='Single Node by Props',
            method=Neo4jQuerer.query,
            query_args=([PERSON, {'name': JD_NAME}],),
            expected=[
                [([PERSON], dict(name=JD_NAME),)],
            ],
        ),
        tc(
            name='Unnamed Relation',
            method=Neo4jQuerer.query,
            query_args=(PERSON, None, BOOK),
            expected=[
                [([PERSON], dict(name=MG_NAME)), ([BOOK], dict(name=WL_NAME)), ([IS_AUTHOR_OF], {})],
            ],
        ),
        tc(
            name='First Node',
            method=Neo4jQuerer.query_nth_node_s,
            query_args=(0, PERSON, IS_AUTHOR_OF, BOOK),
            expected=[
                [([PERSON], dict(name=MG_NAME))],
            ],
        ),
        tc(
            name='Second Node',
            method=Neo4jQuerer.query_nth_node_s,
            query_args=(1, PERSON, IS_AUTHOR_OF, BOOK),
            expected=[
                [([BOOK], dict(name=WL_NAME))],
            ],
        ),
        tc(
            name='Last Node',
            method=Neo4jQuerer.query_nth_node_s,
            query_args=(-1, PERSON, IS_AUTHOR_OF, BOOK),
            expected=[
                [([BOOK], dict(name=WL_NAME))],
            ],
        ),
        tc(
            name='Last Graphel',
            method=Neo4jQuerer.query_nth_s,
            query_args=dict(args=(PERSON, IS_AUTHOR_OF, BOOK), index=-1, kind='e'),
            expected=[
                [([BOOK], dict(name=WL_NAME))],
            ],
        ),
        tc(
            name='Last but one Graphel',
            method=Neo4jQuerer.query_nth_s,
            query_args=dict(args=(PERSON, IS_AUTHOR_OF, BOOK), index=-2, kind='e'),
            expected=[
                [([IS_AUTHOR_OF], {})],
            ],
        ),
        tc(
            name='Second Graphel',
            method=Neo4jQuerer.query_nth_s,
            query_args=dict(args=(PERSON, IS_AUTHOR_OF, BOOK), index=1, kind='e'),
            expected=[
                [([IS_AUTHOR_OF], {}),],
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


def normalize_query_args(query_args: Sequence | dict) -> Tuple[Sequence, dict]:
    if isinstance(query_args, Sequence):
        return query_args, {}
    else:
        args = query_args['args']
        kwargs = query_args
        del kwargs['args']
        return args, kwargs


@RelationQuerableTCG.parametrize(['name', 'method', 'query_args', 'expected'])
def test(name, method: Callable, query_args: tuple | dict, expected):
    args, kwargs = normalize_query_args(query_args)
    table, names = method(*args, **kwargs)
    logging.debug(f'Actual:')
    for i, row in enumerate(table):
        logging.debug(f'row_{i}:')
        for j, elem in enumerate(row):
            logging.debug(f'   - elem_{j}: {elem}')

    def is_row_same(a_row, e_row):
        for a_graphel, e_graphel in zip_longest(a_row, e_row):
            if hasattr(a_graphel, 'element_id'):
                e_labels, e_props = e_graphel
                if set(get_labels(a_graphel)) != set(e_labels) or dict(a_graphel.items()) != e_props:
                    return False
            elif not is_row_same(a_graphel, e_graphel):
                return False
        return True

    assert len(table) == len(expected)
    for e_row in expected:
        for a_row in table:
            if is_row_same(a_row, e_row):
                break
        else:
            pytest.fail(f'Did not found a mathing row for {e_row}')
