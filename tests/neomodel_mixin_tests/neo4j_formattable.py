from __future__ import annotations

from collections import namedtuple

from neomodel import StringProperty, BooleanProperty

from src import db
from src.neomodel_mixins import INeo4jFormattable
from tests.test_case_generator import TCG

db.config_db()


class Animal(INeo4jFormattable):
    extincted = BooleanProperty(default=False)
    name = StringProperty(required=False)


class Human(Animal):
    pass


class Neo4jFormattableTCG(TCG):
    map = tuple

    tc = namedtuple('tc', ['node', 'format', 'expected'])
    tcs = [
        tc(Animal(extincted=True), 'l', 'Animal'),
        tc(Animal(extincted=True), 'ls', ':Animal'),
        tc(Animal(extincted=True, name='Bob'), 'props', str(dict(extincted=True, name='Bob'))),
        tc(Animal(extincted=True), 'node', "(:Animal {'extincted': True, 'name': None})"),
        tc(Human(), 'ls', ':Animal:Human'),
        tc(Human(), 'full', "(:Animal:Human {'extincted': False, 'name': None})"),
    ]


@Neo4jFormattableTCG.parametrize(['node', 'spec', 'expected'])
def test(node: INeo4jFormattable, spec: str, expected: str):
    node.save()
    node.labels()
    actual = '{:{}}'.format(node, spec)
    assert actual == expected

