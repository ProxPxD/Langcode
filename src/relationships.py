from typing import Type

import pydash as _
from neomodel import StructuredRel, RelationshipDefinition, StructuredNode, RelationshipTo, Relationship, RelationshipFrom, ZeroOrMore
from pydash import chain as c

from src.utils import if_


class IClassNameAsRelName:
    @classmethod
    def get_rel_name(cls) -> str:
        return c(cls.__name__).snake_case().upper_case().value()


class Features(IClassNameAsRelName, StructuredRel):
    """[Unit] has a feature [Feature]"""
    pass


class IsSuperOf(IClassNameAsRelName, StructuredRel):
    """[Feature] is a parent [Feature]"""
    pass


class Belongs(IClassNameAsRelName, StructuredRel):
    """[LangSpecificNode] is part of [Language]"""
    pass


class HasKind(IClassNameAsRelName, StructuredRel):
    """[X] is of unit kind of []"""
    pass


def create_rel(definition: Type[RelationshipTo | RelationshipFrom | Relationship], cls: Type[StructuredNode] | str, rel: Type[StructuredRel], cardinality=ZeroOrMore) -> RelationshipDefinition:
    return definition(
        cls_name=if_(cls).is_(Type).then_apply_(_.property_('__name__')),
        relation_type=rel.get_rel_name(),
        model=rel,
        cardinality=cardinality,
    )
