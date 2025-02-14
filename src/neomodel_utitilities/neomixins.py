from __future__ import annotations, annotations

from neomodel import StructuredNode

from src.neomodel_utitilities.neoutils import Neo4jFormatter


class INeo4jFormattable(StructuredNode):
    __abstract_node__ = True

    def __format__(self, format_spec) -> str:
        return Neo4jFormatter.format(self, format_spec)

    def __str__(self):
        return f'{self:node}'

    def __repr__(self):
        try:
            return f'{self:full}'
        except AttributeError:
            return str(self)

