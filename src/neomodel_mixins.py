from __future__ import annotations, annotations

from abc import abstractmethod
from dataclasses import dataclass
from types import NoneType
from typing import Sequence, Optional, Type, Tuple

import neomodel
import pydash as _
from more_itertools import distribute
from neomodel import StructuredNode, NeomodelPath, StructuredRel, db
from pydash import chain as c
from toolz import keyfilter

from src import utils
from src.exceptions import DoNotExistException, AmbiguousSubFeaturesException, IDynamicMessageException
from src.lang_typing import YamlType, OrMore
from src.utils import exceptions_to


class FeaturesNotHierarchied(IDynamicMessageException):
    _make_msg = lambda parent, properties: f'{parent:node} is not a parent of a node with those properties: {properties}'


class INeo4jFormattable(StructuredNode):
    __abstract_node__ = True


    # TODO: Suboptimal so separated. Move outside class?
    @classmethod
    def format_node(cls, labels: list, props: dict, var_name: str = '', *, parenthesis='()') -> str:
        l, r = parenthesis
        label_str = f":{':'.join(labels)}"
        inner = ', '.join([f"{key}: '{val}'" for key, val in (props or {}).items()])
        prop_str = f'{{{inner}}}' if inner else ''
        return f'{l}{var_name}{label_str} {prop_str}{r}'

    def __format__(self, format_spec) -> str:
        label = self.__class__.__name__
        props = {**self.__properties__}
        del props['element_id_property']
        match format_spec:
            case 'id': return self.element_id
            case 'label' | 'l': return label
            case 'labels' | 'ls': return f":{':'.join(self.labels())}"
            case 'properties' | 'props':
                inner = ', '.join([f"{key}: '{val}'" for key, val in (props or {}).items()])
                return f'{{{inner}}}' if inner else ''
            case 'node' | 'n': return f'(:{self:l} {self:props})'
            case 'full': return f'({self:ls} {self:props})'
            case _: raise ValueError(f'Format spec {format_spec} has not been defined')

    def __str__(self):
        return f'{self:node}'

    def __repr__(self):
        try:
            return f'{self:full}'
        except AttributeError:
            return str(self)


@dataclass(frozen=True)
class Orientation:
    UP = 'up'
    DOWN = 'down'


class INeo4jHierarchied(INeo4jFormattable):
    __abstract_node__ = True

    @classmethod
    @abstractmethod
    def _get_hierarchied_rel_name(cls) -> str:
        raise NotImplementedError

    @classmethod
    def get_hierarchied_relationship_expression_for(cls,
            orientation: str,
            __start: int = None,
            __end: int = None,
            __n: int = None,
            __rel_name: str = None,
            __connected_node: INeo4jFormattable = None,
            __connecting_rel: str = None,
            **properties: YamlType
        ) -> str:

        rel_name = __rel_name or cls._get_hierarchied_rel_name()
        label = cls.format_to_neo4j_style('label', **properties)
        node_repr = cls.format_to_neo4j_style('node', **properties)
        right, left = cls._get_right_and_left_parts(orientation)
        start, end = cls._get_start_and_end_parts(__start, __end, __n)
        connection_part = cls._get_connection_part(__connected_node, __connecting_rel)

        return f'{connection_part}{node_repr}{left}-[:{rel_name}*{start}..{end}]-{right}(:{label})'

    @classmethod
    def _get_right_and_left_parts(cls, orientation: str) -> tuple[str, str]:
        right = '>' if orientation == Orientation.DOWN else ''
        left  = '<' if orientation == Orientation.UP   else ''
        return right, left

    @classmethod
    def _get_start_and_end_parts(cls, start: int, end: int, n: int) -> tuple[str, str]:
        match (n, start, end):
            case (None, int(), int()): pass
            case (None, None, None): (start, end) = ('0', '')
            case (None, int(), None): end = ''
            case (None, None, int()): start = '0'
            case (int(), None, None): start = end = n
            case _: raise ValueError(f'Value "__n" cannot be set together with "__start" and "__end"')
        return str(start), str(end)

    @classmethod
    def _get_connection_part(cls, connected_node: INeo4jFormattable, connecting_rel) -> str:
        match (connected_node, connecting_rel):
            case (None, None): return ''
            case (None, _): raise ValueError('Cannot define "__connecting_rel" without "__connected_node"')
            case (str(), _):
                connected_node_repr = cls.format_to_neo4j_style('node', name=connected_node)
            case _:
                connected_node_repr = cls.format_to_neo4j_style('node', connected_node.label **connected_node.all_properties)
        rel_repr = f'[:{connecting_rel}]' if connecting_rel else ''
        return f'{connected_node_repr}-{rel_repr}-'

    @classmethod
    def get_paths_for_expression(cls, expression: str) -> Sequence[NeomodelPath]:
        query = cls.surround_with_path_query(expression)
        return neomodel.db.cypher_query(query)  # TODO: check if returns meta

    @classmethod
    def surround_with_path_query(cls, expression: str) -> str:
        return f'MATCH p = {expression} return p'

    @classmethod
    def get_paths_for(cls, orientation: str, **kwargs) -> Sequence[NeomodelPath]:
        hierarchied_relationship_expression = cls.get_hierarchied_relationship_expression_for(orientation, **kwargs)
        paths = cls.get_paths_for_expression(hierarchied_relationship_expression)
        if '__connected_node' in kwargs:
            paths = c(paths).map(_.drop).value()
        return paths

    def get_paths(self, orientation: str, **kwargs) -> Sequence[NeomodelPath]:
        return self.get_paths_for(orientation, **kwargs, **self.all_properties)

    @classmethod
    def get_paths_up_for(cls, **kwargs):
        return cls.get_paths_for(Orientation.UP, **kwargs)

    @classmethod
    def get_paths_down_for(cls, **kwargs):
        return cls.get_paths_for(Orientation.DOWN, **kwargs)

    def get_paths_up(self, **kwargs):
        return self.get_paths(Orientation.UP, **kwargs)

    def get_paths_down(self, **kwargs):
        return self.get_paths(Orientation.DOWN, **kwargs)

    @classmethod
    def get_all_nth_for(cls, orientation: str, n: int, **kwargs) -> Sequence[INeo4jHierarchied]:
        try:
            return [path.nodes[n] for path in cls.get_paths_for(orientation, n=n, **kwargs)]
        except IndexError:
            raise DoNotExistException

    @classmethod
    def get_all_nth_ancestors_for(cls, n: int, **kwargs) -> Sequence[INeo4jHierarchied]:
        return cls.get_all_nth_for(Orientation.UP, n, **kwargs)

    @classmethod
    def get_all_nth_descendants_for(cls, n: int, **kwargs) -> Sequence[INeo4jHierarchied]:
        return cls.get_all_nth_for(Orientation.DOWN, n, **kwargs)

    @classmethod
    def get_all_next_for(cls, orientation: str, **kwargs) -> Sequence[INeo4jHierarchied]:
        return cls.get_all_nth_for(orientation, n=1, **kwargs)

    def get_all_next(self, orientation: str, **kwargs):
        return self.get_all_next_for(orientation, **kwargs, **self.all_properties)

    @classmethod
    def get_all_next_up_for(cls, **kwargs) -> Sequence[INeo4jHierarchied]:
        return cls.get_all_next_for(Orientation.UP, **kwargs)

    @classmethod
    def get_all_next_down_for(cls, **kwargs) -> Sequence[INeo4jHierarchied]:
        return cls.get_all_next_for(Orientation.DOWN, **kwargs)

    def get_all_next_up(self, **kwargs) -> Sequence[INeo4jHierarchied]:
        return self.get_all_next_up_for(**kwargs, **self.all_properties)

    def get_all_next_down(self, **kwargs) -> Sequence[INeo4jHierarchied]:
        return self.get_all_next_down_for(**kwargs, **self.all_properties)

    @classmethod
    def get_one_nth_for(cls, orientation: str, n: int, **kwargs) -> INeo4jHierarchied:
        nth_nodes = cls.get_all_nth_for(orientation, n=n, **kwargs)
        match len(nth_nodes):
            case 1: return nth_nodes[0]
            case 0: raise DoNotExistException(cls.__name__, kwargs.get('kind', ''))
            case _: raise AmbiguousSubFeaturesException(cls.__name__, kwargs.get('kind', ''))

    @classmethod
    def get_one_nth_up_for(cls, n: int, **kwargs) -> INeo4jHierarchied:
        return cls.get_one_nth_for(Orientation.UP, n=n, **kwargs)

    @classmethod
    def get_one_nth_down_for(cls, n: int, **kwargs) -> INeo4jHierarchied:
        return cls.get_one_nth_for(Orientation.DOWN, n=n, **kwargs)

    @classmethod
    def get_one_next_for(cls, orientation: str, **kwargs) -> INeo4jHierarchied:
        return cls.get_one_nth_for(orientation, n=1, **kwargs)

    @classmethod
    def get_one_next_up_for(cls, **kwargs) -> INeo4jHierarchied:
        return cls.get_one_next_for(Orientation.UP, **kwargs)

    @classmethod
    def get_one_next_down_for(cls, **kwargs) -> INeo4jHierarchied:
        return cls.get_one_next_for(Orientation.DOWN, **kwargs)

    @classmethod
    @exceptions_to(flow_to_bool=True)
    def is_one_next_for(cls, orientation: str, **kwargs) -> bool:
        return cls.get_one_next_for(orientation, **kwargs)

    @classmethod
    @exceptions_to(flow_to_bool=True)
    def is_one_next_up_for(cls, **kwargs) -> bool:
        return cls.get_one_next_up_for(**kwargs)

    @classmethod
    @exceptions_to(flow_to_bool=True)
    def is_one_next_down_for(cls, **kwargs) -> bool:
        return cls.get_one_next_down_for(**kwargs)

    def get_one_next(self, **kwargs) -> INeo4jHierarchied:
        return self.get_one_next_for(**kwargs, **self.all_properties)

    def get_one_next_up(self, **kwargs) -> INeo4jHierarchied:
        return self.get_one_next_up_for(**kwargs, **self.all_properties)

    def get_one_next_down(self, **kwargs) -> INeo4jHierarchied:
        return self.get_one_next_down_for(**kwargs, **self.all_properties)

    def is_one_next(self, **kwargs) -> bool:
        return self.is_one_next_for(**kwargs, **self.all_properties)

    def is_one_next_up(self, **kwargs) -> bool:
        return self.is_one_next_up_for(**kwargs, **self.all_properties)

    def is_one_next_down(self, **kwargs) -> bool:
        return self.is_one_next_down_for(**kwargs, **self.all_properties)

    def get_from_hierarchy(self, orientation: str, __raises: bool = True, **kwargs) -> Optional[INeo4jHierarchied]:
        paths = self.get_paths(orientation, **kwargs)
        properties = keyfilter(lambda s: not s.startswith('__'), kwargs)
        has_all_props = lambda node: all((key, val) in node.__all_properties__ for key, val in properties.items())
        node: INeo4jHierarchied = next((node for path in paths for node in path.nodes if has_all_props(node)), None)
        if not node and __raises:
            raise FeaturesNotHierarchied(self, properties)
        return node

    def get_ancestor(self, **kwargs) -> INeo4jHierarchied:
        return self.get_from_hierarchy(Orientation.UP, **kwargs)

    def get_descendant(self, **kwargs) -> INeo4jHierarchied:
        return self.get_from_hierarchy(Orientation.DOWN, **kwargs)

    def get_ancestors(self, all_properties: Sequence[dict], **general) -> Sequence[INeo4jHierarchied]:
        return list((self.get_ancestor(**properties, **general) for properties in all_properties))

    def get_descendants(self, all_properties: Sequence[dict], **general) -> Sequence[INeo4jHierarchied]:
        return list((self.get_descendant(**properties, **general) for properties in all_properties))

    def is_in_hierarchy(self, other: INeo4jHierarchied, orientation: str, **kwargs) -> bool:
        paths = self.get_paths(orientation, __connected_node=other, **kwargs)
        return bool(paths)

    @exceptions_to(flow_to_bool=True)
    def is_ancestor(self, **kwargs) -> bool:
        return self.get_ancestor(**kwargs)

    @exceptions_to(flow_to_bool=True)
    def is_descendant(self, **kwargs) -> bool:
        return self.get_descendant(**kwargs)

    def has_ancestor(self, **kwargs) -> bool:
        return self.is_descendant(**kwargs)

    def has_descendant(self, **kwargs) -> bool:
        return self.is_ancestor(**kwargs)


# IRelationQuerable

QueryNode = str | INeo4jFormattable | Type[INeo4jFormattable]
SimplifiedQueryNode = str | StructuredNode | Type
QueryRel = Type[StructuredRel] | str
QueryDict = dict | str
FullQueryRel = QueryRel | OrMore[QueryNode] | QueryDict | Tuple[QueryRel, OrMore[QueryNode]] | Tuple[QueryRel, QueryDict] | Tuple[OrMore[QueryNode], QueryDict] | Tuple[QueryRel, OrMore[QueryNode], QueryDict]

AdvQueryRel = QueryRel | tuple[QueryRel, dict]
AdvQueryNode = QueryNode | tuple[QueryNode, dict]
AdvQueryComp = QueryRel | QueryNode


class IRelationQuerable:  # TODO: think of naming convention
    """
    Class that allows to query nodes in certain relation from the current one
    """
    __abstract_node__ = True
    # TODO: adjust node to mean label or at least allow many labels
    _main_property_name: str = 'name'

    @classmethod
    def _normalize_query_component(cls, query_component: AdvQueryComp) -> tuple[list, dict]:
        """
        :param query_component: AdvQueryNode | AdvQueryRel
        :return: (list of labels, properties)
        """
        match query_component:
            case None: return [], {}
            case dict(): return [], query_component
            case str(): return c(query_component).split(':').filter().value(), {}
            case INeo4jFormattable(): return query_component.labels(), {}
            case [_, dict() | None]:
                labels, _ = cls._normalize_query_component(query_component[0])
                _, props = cls._normalize_query_component(query_component[1])
                return labels, props
            case [*labels] if utils.is_all_instance_of_str(labels): return query_component, {}
            case _: raise ValueError(f'Cannot normalize query node: {query_component}')

    # TODO: Move to utils?
    @classmethod
    def get_query_expression(cls, from_node: AdvQueryNode, *rel_to_nodes: AdvQueryRel | AdvQueryNode) -> str:
        """
        AdvQueryNode:
            - StructuredNode
            - str
            - Type[StructuredNode]
            - prop_dict
            - (from_node, prop_dict)
        AdvQueryRel:
            - StructuredRel
            - str
            - Type[StructuredRel]
            - prop_dict
            - (rel, prop_dict)
        :return:
        """
        if len(rel_to_nodes) % 2 != 0:
            rel_to_nodes = [*rel_to_nodes, None]
        from_node = cls._normalize_query_component(from_node)
        rel_to_nodes = c(rel_to_nodes).map(cls._normalize_query_component).value()
        query = INeo4jFormattable.format_node(from_node[0], from_node[1], 'n0')
        for i, ((rel_labels, rel_props), (node_labels, node_props)) in enumerate(zip(*distribute(2, rel_to_nodes)), start=1):
            l = r = ''
            if arrow := next(filter('<>'.__contains__, rel_labels), None):
                rel_labels = rel_labels[::]
                rel_labels.remove(arrow)
                match arrow:
                    case '>': r = '>'
                    case '<': l = '<'

            node_str = INeo4jFormattable.format_node(node_labels, node_props, f'n{i}', parenthesis='()')
            rel_str  = INeo4jFormattable.format_node(rel_labels,  rel_props,  f'r{i}', parenthesis='[]')
            rel_str = rel_str.replace(':*', '*')  # Adjust for variable length
            query += f'{l}-{rel_str}-{r}{node_str}'
        return query

    @classmethod
    def query_by_rel(cls, from_node: AdvQueryNode, *rel_to_nodes: AdvQueryRel | AdvQueryNode):
        expression = cls.get_query_expression(from_node, *rel_to_nodes)
        query = f'MATCH {expression} RETURN *'
        return db.cypher_query(query)
    # TODO: replace get_one_own_by_rels_props with the something based on the above