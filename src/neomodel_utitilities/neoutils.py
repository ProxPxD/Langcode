from itertools import cycle
from itertools import cycle
from typing import Type, Sequence

import pydash as _
from more_itertools import distribute, take
from neomodel import StructuredNode, StructuredRel, db
from pydash import chain as c

from src import utils
from src.lang_typing import YamlType

QueryNode = str | StructuredNode | Type[StructuredNode]
QueryRel = str | Type[StructuredRel]

AdvQueryRel = QueryRel | tuple[QueryRel, dict]
AdvQueryNode = QueryNode | tuple[QueryNode, dict]
AdvQueryComp = QueryRel | QueryNode


def take_out_arrows(labels) -> tuple[list, str, str]:
    if not (arrow := next(filter('<>'.__contains__, labels), None)):
        return labels, '', ''
    labels.remove(arrow)
    match arrow:
        case '>': return labels, '', arrow
        case '<': return labels, arrow, ''


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
    # TODO: replace get_one_own_by_rels_props with the something based on the below
    
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

    @classmethod
    def get_query_expression(cls, from_node: AdvQueryNode, *rel_to_nodes: AdvQueryRel | AdvQueryNode,  names: Sequence[str] = None) -> str:
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
        names = names or ['n0'] + take(len(rel_to_nodes), (f'{name}{i//2 + 1}' for i, name in enumerate(cycle('rn'))))
        if len(names) != len(rel_to_nodes) + 1:
            raise ValueError('Graphel names should be as many as graphels')
        from_node = cls._normalize_query_component(from_node)
        rel_to_nodes = c(rel_to_nodes).map(cls._normalize_query_component).value()
        query = Neo4jFormatter.format_to_node(from_node[0], from_node[1], names[0])
        for rel_name, node_name, (rel_labels, rel_props), (node_labels, node_props) \
                in zip(*distribute(2, names[1:]), *distribute(2, rel_to_nodes)):
            rel_labels, l, r = take_out_arrows(rel_labels)
            rel_str = Neo4jFormatter.format_to_node(rel_labels, rel_props, rel_name, parenthesis='[]').replace(':*', '*')  # Adjust for variable length
            node_str = Neo4jFormatter.format_to_node(node_labels, node_props, node_name, parenthesis='()')
            query += f'{l}-{rel_str}-{r}{node_str}'
        return query

    @classmethod
    def query(cls, from_node: AdvQueryNode, *rel_to_nodes: AdvQueryRel | AdvQueryNode, names: Sequence[str] = None, to_return: str | Sequence = '*'):
        expression = cls.get_query_expression(from_node, *rel_to_nodes, names=names)
        if isinstance(to_return, Sequence):
            to_return = ', '.join(to_return)
        query = f'MATCH {expression} RETURN {to_return}'
        return db.cypher_query(query)

    @classmethod
    def query_nth_s(cls, from_node: AdvQueryNode, *rel_to_nodes: AdvQueryRel | AdvQueryNode, index: int | Sequence = -1, kind: str = 'n'):
        """
        :param kind: graphel kind to return [n(ode), r(relationship), e(lem)]
        :param n: nth graphel to return
        :return:
        """
        orig_index = _.to_list(index)
        max_size = len(rel_to_nodes) // 2 if kind in 'rn' else len(rel_to_nodes)
        if kind not in 'ner':
            raise ValueError(f'Unknown kind "{kind}". Available: [n(ode), r(relationship), e(lem)]')
        underflow = lambda v: max_size + v + 1
        index = _.map_(orig_index, c().apply_if(underflow, _.is_negative))
        if any(not (0 <= i <= max_size) for i in index):
            raise ValueError(f'Variable index={index} out of bound (-{max_size}, {max_size})')

        names = [f'e{i}' for i in range(len(rel_to_nodes) + 1)] if kind == 'e' else None
        to_return = [f'{kind}{i}' for i in index]
        return cls.query(from_node, *rel_to_nodes, names=names, to_return=to_return)

    # TODO: to test
    @classmethod
    def query_nth_node_s(cls, index: int | Sequence, from_node: AdvQueryNode, *rel_to_nodes: AdvQueryRel | AdvQueryNode):
        return cls.query_nth_s(from_node, *rel_to_nodes, kind='n', index=index)

    @classmethod
    def query_nth_rel_s(cls, index: int | Sequence, from_node: AdvQueryNode, *rel_to_nodes: AdvQueryRel | AdvQueryNode):
        return cls.query_nth_s(from_node, *rel_to_nodes, kind='r', index=index)

