from typing import Type, Tuple

from more_itertools import distribute
from neomodel import StructuredNode, StructuredRel, db

from src import utils
from src.lang_typing import YamlType, OrMore

import pydash as _
from pydash import chain as c


QueryNode = str | StructuredNode | Type[StructuredNode]
QueryRel = str | Type[StructuredRel]

AdvQueryRel = QueryRel | tuple[QueryRel, dict]
AdvQueryNode = QueryNode | tuple[QueryNode, dict]
AdvQueryComp = QueryRel | QueryNode


class Neo4jFormatter:
    @classmethod
    def format_property(cls, prop: YamlType) -> str:
        match prop:
            case None: return 'null'
            case bool() | int() | float(): return str(prop).lower()
            case str(): return f"'{prop}'"
            case list(): return '[' + (', '.join(_.map_(prop, cls.format_property))) + ']'
            case dict() if not prop: return ''
            case dict(): return '{' + (', '.join([f"{key}: {cls.format_property(val)}" for key, val in prop.items()])) + '}'

    @classmethod
    def format_labels(cls, labels: list[str]) -> str:
        return f":{':'.join(labels)}" if labels else ''

    @classmethod
    def format_to_node(cls, labels: list, props: dict, var_name: str = '', *, parenthesis='()') -> str:
        l, r = parenthesis
        return f'{l}{var_name}{cls.format_labels(labels)} {cls.format_property(props)}{r}'

    @classmethod
    def get_props_without_id(cls, node: StructuredNode) -> dict:
        props = {**node.__properties__}
        del props['element_id_property']
        return props

    @classmethod
    def format(cls, node: StructuredNode, format_spec: str) -> str:
        match format_spec:
            case 'id': return node.element_id
            case 'label' | 'l': return node.__class__.__name__
            case 'labels' | 'ls': return cls.format_labels(node.labels())
            case 'properties' | 'props' | 'p': return cls.format_property(cls.get_props_without_id(node))
            case 'node' | 'n': return cls.format_to_node([f'{node:l}'], cls.get_props_without_id(node))
            case 'full': return cls.format_to_node(node.labels(), cls.get_props_without_id(node))
            case _: raise ValueError(f'Format spec {format_spec} has not been defined')


class Neo4jQuerer:
    
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
            case StructuredNode(): return query_component.labels(), {}
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
        query = Neo4jFormatter.format_to_node(from_node[0], from_node[1], 'n0')
        for i, ((rel_labels, rel_props), (node_labels, node_props)) in enumerate(zip(*distribute(2, rel_to_nodes)), start=1):
            l = r = ''
            if arrow := next(filter('<>'.__contains__, rel_labels), None):
                rel_labels = rel_labels[::]
                rel_labels.remove(arrow)
                match arrow:
                    case '>': r = '>'
                    case '<': l = '<'

            node_str = Neo4jFormatter.format_to_node(node_labels, node_props, f'n{i}', parenthesis='()')
            rel_str  = Neo4jFormatter.format_to_node(rel_labels, rel_props, f'r{i}', parenthesis='[]')
            rel_str = rel_str.replace(':*', '*')  # Adjust for variable length
            query += f'{l}-{rel_str}-{r}{node_str}'
        return query

    @classmethod
    def query_by_rel(cls, from_node: AdvQueryNode, *rel_to_nodes: AdvQueryRel | AdvQueryNode):
        expression = cls.get_query_expression(from_node, *rel_to_nodes)
        query = f'MATCH {expression} RETURN *'
        return db.cypher_query(query)
    # TODO: replace get_one_own_by_rels_props with the something based on the above
