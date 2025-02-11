from neomodel import StructuredNode

from src.lang_typing import YamlType

import pydash as _
from pydash import chain as c


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
