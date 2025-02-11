from __future__ import annotations

from collections import namedtuple

from neomodel import StringProperty, BooleanProperty, ArrayProperty, StructuredNode

from src.neomodel_utitilities.neomixins import INeo4jFormattable
from tests.test_case_generator import TCG


class Animal(INeo4jFormattable):
    extincted = BooleanProperty(default=False)
    name = StringProperty(required=False)


class Human(Animal):
    pass


class Person(INeo4jFormattable):
    children = ArrayProperty(default=[])
    numbers = ArrayProperty(default=[])


class Neo4jFormattableTCG(TCG):
    map = tuple

    tc = namedtuple('tc', ['node', 'spec', 'expected'])
    tcs = [
        tc(Animal(extincted=True), 'l', 'Animal'),
        tc(Animal(extincted=True), 'ls', ':Animal'),
        tc(Animal(extincted=True, name='Bob'), 'props', "{extincted: true, name: 'Bob'}"),
        tc(Animal(extincted=False), 'node', "(:Animal {extincted: false, name: null})"),
        tc(Human(), 'ls', ':Animal:Human'),
        tc(Human(), 'full', "(:Animal:Human {extincted: false, name: null})"),
        tc(Person(children=['Aniela'], numbers=[21, 3.14]), 'p', "{children: ['Aniela'], numbers: [21, 3.14]}"),
    ]


@Neo4jFormattableTCG.parametrize(['node', 'spec', 'expected'])
def test(node: INeo4jFormattable, spec: str, expected: str):
    node.save()
    node.labels()
    actual = '{:{}}'.format(node, spec)
    assert actual == expected

