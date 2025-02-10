from __future__ import annotations

from collections import namedtuple

from neo4j.graph import Node, Relationship
from neomodel import db

from src.neomodel_mixins import IRelationQuerable
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

    tc = namedtuple('tc', ['name', 'query_args', 'expected'])
    tcs = [
        tc(
            name='Simple Query Directionless',
            query_args=(PERSON, IS_AUTHOR_OF, BOOK),
            expected=[
                [([PERSON], dict(name=MG_NAME)), ([BOOK], dict(name=WL_NAME)), ([IS_AUTHOR_OF], {})],
            ],
        ),
        tc(
            name='Exact Hop Query Directionless',
            query_args=(PERSON, [KNOWS, '*2'], PERSON),
            expected=[
                [([PERSON], dict(name=MG_NAME)), ([PERSON], dict(name=AZ_NAME)), [([KNOWS], {}), ([KNOWS], {})]],
                [([PERSON], dict(name=AZ_NAME)), ([PERSON], dict(name=MG_NAME)), [([KNOWS], {}), ([KNOWS], {})]],
            ],
        ),
        tc(
            name='Any Hop Query Directed',
            query_args=(PERSON, [KNOWS, '*', '>'], PERSON),
            expected=[
                [([PERSON], dict(name=MG_NAME)), ([PERSON], dict(name=JD_NAME)), [([KNOWS], {})]],
                [([PERSON], dict(name=MG_NAME)), ([PERSON], dict(name=AZ_NAME)), [([KNOWS], {}), ([KNOWS], {})]],
                [([PERSON], dict(name=JD_NAME)), ([PERSON], dict(name=AZ_NAME)), [([KNOWS], {})]],
            ],
        ),
        tc(
            name='Two Relations',
            query_args=(PERSON, KNOWS, PERSON, IS_AUTHOR_OF, BOOK),
            expected=[
                [([PERSON], dict(name=JD_NAME)), ([PERSON], dict(name=MG_NAME)), ([BOOK], dict(name=WL_NAME)), ([KNOWS], {}), ([IS_AUTHOR_OF], {})],
            ],
        ),
         tc(
            name='Single Node by Props',
            query_args=([PERSON, {'name': JD_NAME}],),
            expected=[
                [([PERSON], dict(name=JD_NAME),)],
            ],
        ),
         tc(
            name='Unnamed Relation',
            query_args=(PERSON, None, BOOK),
            expected=[
                [([PERSON], dict(name=MG_NAME)), ([BOOK], dict(name=WL_NAME)), ([IS_AUTHOR_OF], {})],
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


@RelationQuerableTCG.parametrize(['name', 'query_args', 'expected'])
def test(name, query_args, expected):
    table, names = IRelationQuerable.query_by_rel(*query_args)
    assert len(table) == len(expected)
    for a_row, e_row in zip(table, expected):
        assert len(a_row) == len(e_row)
        for a_graphel, e_graphel in zip(a_row, e_row):
            if hasattr(a_graphel, 'element_id'):
                e_labels, e_props = e_graphel
                assert set(get_labels(a_graphel)) == set(e_labels)
                assert dict(a_graphel.items()) == e_props
            else:
                for a_sub_graphel, e_sub_graphel in zip(a_graphel, e_graphel):
                    e_labels, e_props = e_sub_graphel
                    assert set(get_labels(a_sub_graphel)) == set(e_labels)
                    assert dict(a_sub_graphel.items()) == e_props
