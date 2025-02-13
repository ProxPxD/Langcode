from itertools import cycle, chain
from itertools import cycle
from math import ceil
from typing import Type, Sequence, Optional

import more_itertools
import pydash as _
from more_itertools import distribute, take, unique_everseen, padded
from neomodel import StructuredNode, StructuredRel, db
from pydash import chain as c

from src import utils
from src.lang_typing import YamlType
from src.utils import is_sequence, to_list, div_round_up

QueryNode = str | StructuredNode | Type[StructuredNode]
QueryRel = str | Type[StructuredRel]

AdvQueryRel = QueryRel | tuple[QueryRel, dict]
AdvQueryNode = QueryNode | tuple[QueryNode, dict]
AdvQueryComp = QueryRel | QueryNode


def take_out_arrows(labels: list) -> tuple[list, str, str]:
    if not (arrow := next(filter('<>'.__contains__, labels), None)):
        return labels, '', ''
    labels = labels[::]
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
    def get_query_expression(cls, from_node: AdvQueryNode, *rel_to_nodes: AdvQueryRel | AdvQueryNode,
            names: Sequence[str] = None,
        ) -> str:
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
        if len(names) != len(rel_to_nodes) + 1:
            raise ValueError('Graphel names should be as many as graphels')
        # Normalize graphels
        from_node = cls._normalize_query_component(from_node)
        rel_to_nodes = c(rel_to_nodes).map(cls._normalize_query_component).value()
        # Create Query
        query = Neo4jFormatter.format_to_node(from_node[0], from_node[1], names[0])
        for rel_name, node_name, (rel_labels, rel_props), (node_labels, node_props) \
                in zip(*distribute(2, names[1:]), *distribute(2, rel_to_nodes)):
            rel_labels, l, r = take_out_arrows(rel_labels)
            rel_str = Neo4jFormatter.format_to_node(rel_labels, rel_props, rel_name, parenthesis='[]').replace(':*', '*')  # Adjust for variable length
            node_str = Neo4jFormatter.format_to_node(node_labels, node_props, node_name, parenthesis='()')
            query += f'{l}-{rel_str}-{r}{node_str}'
        return query

    @classmethod
    def _adjust_index(cls, index: Optional[int | Sequence[int]], max_size: int) -> list[int]:
        underflow = lambda v: max_size + v
        index = _.map_(_.to_list(index if index is not None else []), c().apply_if(underflow, _.is_negative))
        if any(not (0 <= i <= max_size) for i in index):
            raise ValueError(f'Variable index={index} out of bound (-{max_size}, {max_size})')
        return index

    @classmethod
    def _create_expression_names(cls,
            count: int,
            kind: str = None,
        ) -> list[str]:
        """
        :param kind: graphel kind to return [n(ode), r(relationship), e(lem)]
        :param count: count of names
        :return:
        """
        match kind:
            case 'e': names = [f'e{i}' for i in range(count + 1)]
            case None | 'r' | 'n': names = ['n0'] + take(count, (f'{name}{i//2 + 1}' for i, name in enumerate(cycle('rn'))))
            case _: raise ValueError(f'Unknown kind "{kind}". Available: [n(ode), r(relationship), e(lem)]')
        return names

    @classmethod
    def _create_graphels_to_return(cls, to_return: str | list, names: Sequence[Optional[str]], index: Sequence, kind: str = None) -> list[str]:
        match to_return:
            case str(): return to_return.replace(',', '').replace('\\s', ' ').split(' ')
            case list(): return to_return
        if index:
            adjusted_for_kind = _.filter_(names, c().starts_with(kind)) if kind else names
            return _.at(adjusted_for_kind, *index)
        return _.filter_(names, bool)

    @classmethod
    def query(cls, from_node: AdvQueryNode, *rel_to_nodes: AdvQueryRel | AdvQueryNode,
            names: Sequence[Optional[str]] = None,
            index: int | Sequence = None,
            kind: str = None,
            to_return: str | Sequence = None,
            unique_graphels: bool = False,
            exact_return: bool = False,
        ):
        n_graphel = div_round_up(len(rel_to_nodes), 2)
        rel_to_nodes = list(padded(rel_to_nodes, None, n_graphel)) if n_graphel else []
        names = names or cls._create_expression_names(n_graphel, kind=kind)
        expression = cls.get_query_expression(from_node, *rel_to_nodes, names=names)
        kind_names = _.filter_(names, c().starts_with(kind)) if kind else names
        index = cls._adjust_index(index, len(kind_names))
        to_returns = cls._create_graphels_to_return(to_return, names=kind_names, index=index, kind=kind)
        return_expr = ', '.join(to_returns)
        query = f'MATCH {expression} RETURN {return_expr}'
        table, names = db.cypher_query(query)
        orig_table = table

        # Managing return
        if unique_graphels:
            table = _.uniq(graphel for row in table for graphel in row)
        if exact_return:
            if len(table) > 1:  # TODO rephrase
                raise ValueError('Queried for an exact return, but got more options', query, orig_table)
            table = table[0]
        return table, names


