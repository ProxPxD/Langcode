from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import Sequence, Optional, Type, Tuple, Callable

import neomodel
import pydash as _
from neomodel import StructuredNode, NeomodelPath, StructuredRel, Database
from pydash import chain as c, curry
from toolz import keyfilter

from src import utils
from src.exceptions import PropertyNotFound, CannotCreatePropertyException, DoNotExistException, AmbiguousSubFeaturesException, IDynamicMessageException, AmbiguousNodeException
from src.lang_typing import YamlType, OneOrMore
from src.utils import exceptions_to, is_not, if_, to_list, pad_left_until, to_tuple


class FeaturesNotHierarchied(IDynamicMessageException):
    _make_msg = lambda parent, properties: f'{parent:node} is not a parent of a node with those properties: {properties}'


class ICorePropertied(StructuredNode):
    _core_properties_classes_or_names = []

    @property
    def core_property_names(self) -> set[str]:  # TODO: (neo4j) Consider other implementation for generalization
        names_or_classes = self._core_properties_classes_or_names or set()
        interface_to_name = c().get('__name__').tail().trim_end('Property').snake_case()
        interfaces_to_names = c().map_(interface_to_name).apply(set)
        return set(c(names_or_classes).apply_if(interfaces_to_names, is_not(str)).value())

    @property
    def core_properties(self) -> dict[str, YamlType]:
        return utils.map_to_dict(self.core_property_names, self.__getattribute__)

    @property
    def all_property_names(self) -> set[str]:
        return self.core_property_names

    @property
    def all_properties(self) -> dict[str, YamlType]:
        return self.core_properties


class ICustomPropertied(ICorePropertied):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._custom_property_names: set = set()

    @property
    def custom_property_names(self) -> set[str]:
        return self._custom_property_names.copy()

    @property
    def custom_properties(self) -> dict[str, YamlType]:
        return utils.map_to_dict(self.custom_property_names, self.get_property)

    def get_property(self, name: str) -> YamlType:
        if name not in self._custom_property_names:
            raise PropertyNotFound(self, name)
        return self.__getattribute__(name)

    @exceptions_to()
    def has_property(self, name: str) -> bool:
        return self.get_property(name)

    def set_property(self, name: str, val: YamlType = None) -> None:
        if name not in self.custom_property_names and hasattr(self, name):
            raise CannotCreatePropertyException(name)
        self._custom_property_names.add(name)
        setattr(self, name, val)

    def remove_property(self, name: str) -> None:
        if self.has_property(name):
            self.__delattr__(name)

    @property
    def all_property_names(self) -> set[str]:
        return super().all_property_names | self.custom_property_names

    @property
    def all_properties(self) -> dict[str, YamlType]:
        return super().core_properties | self.custom_properties


class INeo4jFormatable(ICorePropertied):
    @classmethod
    def format_to_neo4j_style(cls, format_spec: str, __label: str = None, **properties) -> str:  # TODO: consider many labels
        label = cls.__name__ if __label is None else __label
        match format_spec:
            case 'label' | 'l': return label
            case 'properties' | 'props': return str(properties)
            case 'node' | 'n': return f'(:{label} {str(properties)})'
            case _: raise ValueError(f'Format spec {format_spec} has not been defined')

    def __format__(self, format_spec) -> str:
        return self.format_to_neo4j_style(format_spec=format_spec, **self.all_properties)


@dataclass
class Orientation:
    UP = 'up'
    DOWN = 'down'


class INeo4jHierarchied(INeo4jFormatable):

    @property
    def labels(self):
        return self.__class__.__name__

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
            __connected_node: INeo4jFormatable = None,
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
    def _get_connection_part(cls, connected_node: INeo4jFormatable, connecting_rel) -> str:
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

QueryNode = str | StructuredNode | Type[StructuredNode]
SimplifiedQueryNode = str | StructuredNode | Type
QueryRel = Type[StructuredRel] | str
QueryDict = dict | str
FullQueryRel = QueryRel | OneOrMore[QueryNode] | QueryDict | Tuple[QueryRel, OneOrMore[QueryNode]] | Tuple[QueryRel, QueryDict] | Tuple[OneOrMore[QueryNode], QueryDict] | Tuple[QueryRel, OneOrMore[QueryNode], QueryDict]


class IRelationQuerable(INeo4jFormatable):
    # TODO: adjust node to mean label or at least allow many labels
    _main_property_name: str = 'name'

    def is_saved(self):
        return self.element_id is not None

    @classmethod
    def _format_relation_part(cls, relation: Type[StructuredRel] | str) -> str:
        match relation:
            case None: formatted = ''
            case str(): formatted = f':{relation}'
            case _ if hasattr(relation, 'get_rel_name'): formatted = f':{relation.get_rel_name()}'
            case type(): formatted = f':{c(relation.__name__).snake_case().upper_case().value()}'
            case _: formatted = str(relation)
        return f'[{formatted}]'

    @classmethod
    def _format_node_label_s(cls, label_s: OneOrMore[QueryNode]) -> str:
        return c(to_tuple(label_s)).map(cls._format_node_label).join('').value()

    @classmethod
    def _format_node_label(cls, label: QueryNode) -> str:
        match label:
            case None: return ''
            case str(): formatted = label
            case StructuredNode(): formatted = label.__class__.__name__
            case type(): formatted = label.__name__
            case _: formatted = str(label)
        return f':{formatted}'

    @classmethod
    def _adjust_props(cls, props: dict | str, **kwargs) -> dict:
        props = if_(props).is_(str).then_apply_(lambda p: {cls._main_property_name: str(p)})
        props.update(kwargs)
        return props

    @classmethod
    def _format_node_part(cls, label_s: OneOrMore[QueryNode], props: str | dict, name: str = '') -> str:
        node_label = cls._format_node_label_s(label_s)
        props = cls._adjust_props(props)
        return f'({name}{node_label} {props})'

    @classmethod
    def _format_relation_expression(cls, from_node_part: str, relation_part: str, to_node: str) -> str:
        return f'{from_node_part}-{relation_part}-{to_node}'

    @classmethod
    def get_all_by_rel_prop(cls,
            from_node: OneOrMore[QueryNode] = None,
            from_node_props: QueryDict = None,
            relation: QueryRel = None,
            to_node: OneOrMore[QueryNode] = None,
            to_node_props: QueryDict = None,
    ) -> Sequence[StructuredNode]:
        from_node_name = 'from_node'
        expression = cls._format_relation_expression(
            cls._format_node_part(from_node, from_node_props, from_node_name),
            cls._format_relation_part(relation),
            cls._format_node_part(to_node, to_node_props)
        )
        return Database().cypher_query(f'MATCH {expression} RETURN {from_node_name}')

    @classmethod
    def _adjust_inner_rel(cls, full_query_rel: FullQueryRel) -> FullQueryRel:
        insert_none_at_nth = curry(lambda n, arr: arr[:n] + [None] + arr[n:])
        get_insert_none_if_types = curry(lambda n, types: c().apply_if(
            insert_none_at_nth(n),
            c().nth(n).is_instance_of(types)
        ))

        full_query_rel = to_list(full_query_rel)
        full_query_rel = get_insert_none_if_types(0, SimplifiedQueryNode | list | dict)(full_query_rel)  # TODO: make sure that replacing "OneOrMore" with "QueryNode | list" bahave as expected
        full_query_rel = get_insert_none_if_types(1, dict)(full_query_rel)
        full_query_rel = pad_left_until(3, None)(full_query_rel)
        return full_query_rel

    @classmethod
    def _adjust_rels(cls, rels: Sequence[FullQueryRel], _adjust_inner_rel=None) -> list[FullQueryRel]:
        if rels and not c().nth(0).is_instance_of(Sequence)(rels):
            rels = (rels, )
        rels = _.map_(rels, _adjust_inner_rel or cls._adjust_inner_rel)
        return rels

    @classmethod
    def _get_all_by_rels_props(cls, *,
            rels: Sequence[FullQueryRel] = None,
            from_node: OneOrMore[QueryNode] = '',
            from_node_props: dict = None,
            _adjust_rels=None,
            **more_from_node_props
        ):
        """
        forms:
            - (Rel, ToNode, ToNodeProps)
            - (Rel, ToNode)
            - (Rel, ToNodeProps)
            - (ToNode, ToNodeProps)
            - Rel
            - ToNode
            - ToNodeProps
        """
        _adjust_rels = _adjust_rels or cls._adjust_rels
        from_node_name = 'from_node'
        from_node_props = cls._adjust_props(from_node_props, **more_from_node_props)
        from_node_part = cls._format_node_part(from_node, from_node_props, from_node_name)

        expr_parts = [
            cls._format_relation_expression(
                from_node_part,
                cls._format_relation_part(rel),
                cls._format_node_part(to_node, to_node_props)
            ) for rel, to_node, to_node_props in _adjust_rels(rels)
        ]

        if not expr_parts:
            return []
        query = f'MATCH {", ".join(expr_parts)} RETURN {from_node_name}'
        return Database().cypher_query(query)

    @classmethod
    def get_one_by_rels_props(cls, *, rels: Sequence[FullQueryRel] = None, from_node: QueryNode = '', from_node_props: dict = None, _adjust_rels=None, **more_from_node_props):
        nodes = cls._get_all_by_rels_props(rels=rels, from_node=from_node, from_node_props=from_node_props, _adjust_rels=_adjust_rels, **more_from_node_props)
        match len(nodes):
            case 1: return nodes[0]
            case 0: raise DoNotExistException()  # TODO: think of rewriting the exceptions
            case _: raise AmbiguousNodeException()

    def _adjust_own_inner_rel(self, rel: FullQueryRel) -> FullQueryRel:
        return self._adjust_inner_rel(rel)

    def _adjust_own_rels(self, rels: Sequence[FullQueryRel]) -> list[FullQueryRel]:
        return self._adjust_rels(rels, _adjust_inner_rel=self._adjust_own_inner_rel)

    def _adjust_own_rels_if_saved(self, rels: Sequence[FullQueryRel], adjust: Callable[[Sequence[FullQueryRel]], Sequence[FullQueryRel]]) -> list[FullQueryRel]:
        if self.is_saved():
            rels = adjust(rels)
        return self._adjust_rels(rels)

    def get_all_own_by_rels_props(self, *, rels: Sequence[FullQueryRel] = None, from_node: QueryNode = '', from_node_props: dict = None, **more_from_node_props):
        """
        forms:
            - (Rel, ToNode, ToNodeProps)
            - (Rel, ToNode)
            - (Rel, ToNodeProps)
            - (ToNode, ToNodeProps)
            - Rel
            - ToNode
            - ToNodeProps
        """
        return self._get_all_by_rels_props(rels=rels, from_node=from_node, from_node_props=from_node_props, _adjust_rels=self._adjust_own_rels, **more_from_node_props)

    def get_one_own_by_rels_props(self, *, rels: Sequence[FullQueryRel] = None, from_node: QueryNode = '', from_node_props: dict = None, **more_from_node_props):
        return self.get_one_by_rels_props(rels=rels or [], from_node=from_node, from_node_props=from_node_props, _adjust_rels=self._adjust_own_rels, **more_from_node_props)
