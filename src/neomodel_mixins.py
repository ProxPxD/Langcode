from abc import abstractmethod
from dataclasses import dataclass
from typing import Sequence

import neomodel
import pydash as _
from neomodel import StructuredNode, StringProperty, NeomodelPath
from pydash import chain as c

from src import utils
from src.exceptions import PropertyNotFound, CannotCreatePropertyException, DoNotExistException, AmbiguousSubFeaturesException
from src.lang_typing import YamlType
from src.utils import exceptions_to


## Properties


class IName(StructuredNode):
    name = StringProperty(required=True)


class IKind(StructuredNode):
    kind = StringProperty()


class ICorePropertied(IName, IKind):
    @property
    def core_property_names(self) -> set[str]:
        interface_to_name = c().get('__name__').tail().snake_case()
        interfaces_to_names = c().map_(interface_to_name).apply(set)
        return interfaces_to_names(self.__class__.__bases__)

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
        self.__custom_property_names: set = set()

    @property
    def custom_property_names(self) -> set[str]:
        return self.__custom_property_names.copy()

    @property
    def custom_properties(self) -> dict[str, YamlType]:
        return utils.map_to_dict(self.custom_property_names, self.get_property)

    def get_property(self, name: str) -> YamlType:
        if name not in self.__custom_property_names:
            raise PropertyNotFound(self, name)
        return self.__getattribute__(name)

    @exceptions_to()
    def has_property(self, name: str) -> bool:
        return self.get_property(name)

    def set_property(self, name: str, val: YamlType = None) -> None:
        if name not in self.custom_property_names and hasattr(self, name):
            raise CannotCreatePropertyException(name)
        self.__custom_property_names.add(name)
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


##

class INeo4jFormatable(ICorePropertied):
    @classmethod
    def format_to_neo4j_style(cls, format_spec: str, __label: str = None, **properties) -> str:  # TODO: consider many labels
        label = cls.__name__ if __label is None else __label
        name = properties.get('name', '')
        kind = properties.get('kind', '')
        match format_spec:
            case 'label' | 'l': return label
            case 'kind': return kind
            case 'name': return name
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
        right, left = cls.__get_right_and_left_parts(orientation)
        start, end = cls.__get_start_and_end_parts(__start, __end, __n)
        connection_part = cls.__get_connection_part(__connected_node, __connecting_rel)

        return f'{connection_part}{node_repr}{left}-[:{rel_name}*{start}..{end}]-{right}(:{label})'

    @classmethod
    def __get_right_and_left_parts(cls, orientation: str) -> tuple[str, str]:
        right = '>' if orientation == Orientation.DOWN else ''
        left  = '<' if orientation == Orientation.UP   else ''
        return right, left

    @classmethod
    def __get_start_and_end_parts(cls, start: int, end: int, n: int) -> tuple[str, str]:
        match (n, start, end):
            case (None, int(), int()): pass
            case (None, None, None): (start, end) = ('0', '')
            case (None, int(), None): end = ''
            case (None, None, int()): start = '0'
            case (int(), None, None): start = end = n
            case _: raise ValueError(f'Value "__n" cannot be set together with "__start" and "__end"')
        return str(start), str(end)

    @classmethod
    def __get_connection_part(cls, connected_node: INeo4jFormatable, connecting_rel) -> str:
        match (connected_node, connecting_rel):
            case (None, None): return ''
            case (None, _): raise ValueError('Cannot define "__connecting_rel" without "__connected_node"')
            case _:
                connected_node_repr = cls.format_to_neo4j_style('node', connected_node.label **connected_node.all_properties)
                rel_repr = f'[:{connecting_rel}]' if connecting_rel else ''
        return f'{connected_node_repr}-{rel_repr}-'

    @classmethod
    def get_paths_for_expression(cls, expression: str) -> Sequence[NeomodelPath]:
        query = cls.surround_with_path_query(expression)
        return neomodel.db.cypher_query(query)

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
    def get_all_next_for(cls, orientation: str, **kwargs):
        cls.get_paths_for(orientation, n=1, **kwargs)

    def get_all_next(self, orientation: str, **kwargs):
        self.get_all_next_for(orientation, n=1, **kwargs, **self.all_properties)

    @classmethod
    def get_one_next_for(cls, orientation: str, **kwargs):
        match next_node := cls.get_next(orientation, **kwargs):
            case None: raise DoNotExistException(cls.__name__, kwargs.get('kind', ''))
            case list(): raise AmbiguousSubFeaturesException(cls.__name__, kwargs.get('kind', ''))
            case _: return next_node

    @classmethod
    def get_one_next_up_for(cls, **kwargs):
        return cls.get_one_next_for(Orientation.UP, **kwargs)

    @classmethod
    def get_one_next_down_for(cls, **kwargs):
        return cls.get_one_next_for(Orientation.DOWN, **kwargs)
