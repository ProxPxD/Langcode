from __future__ import annotations

from neomodel import RelationshipTo
from neomodel.contrib.sync_.semi_structured import SemiStructuredNode

from src.neomodel_utitilities import INeo4jFormattable


class StructiveOGM(INeo4jFormattable, SemiStructuredNode):
    is_ = RelationshipTo('StructiveOGM', 'is')
