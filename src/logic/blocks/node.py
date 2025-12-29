from __future__ import annotations

import uuid
from functools import cached_property
from typing import Any, Optional, Collection

from SPARQLWrapper import JSON
from box import Box
from ordered_set import OrderedSet
from rdflib import XSD

from src.logic.consts.db import URI_PREFIX
from src.logic.db import GDM

RDFType = str | float | int | bool

class RDFNode:
    _prefix: str = URI_PREFIX
    _graph_name: str = None

    @classmethod
    def set_prefix(cls, prefix: str) -> None:
        cls._prefix = prefix

    @property
    def gdm(self) -> GDM:
        return GDM.curr()

    def __init__(self,
            uid: str = None, *, uri: str = None,
            **preds: Collection[RDFNode | RDFType] | RDFNode | RDFType,
        ):
        self.uid = self._extract_uid(uid, uri)
        self.create_triples(**preds)

    @classmethod
    def _extract_uid(cls, uid: Optional[str], uri: Optional[str]) -> str:  # noqa
        match bool(uid), bool(uri):  # noqa
            case (True, True): raise ValueError('Create RDFNode cannot have both "uri" or "uuid" to init')
            case (False, True): return uri.rsplit('/')[-1]
            case (False, False): return str(uuid.uuid4())
            case (True, False): return uid

    @cached_property
    def uri(self) -> str:
        return f'{self._prefix}{self.uid}'

    def __repr__(self) -> str:
        return f'<RDFNode {self.uri}>'

    def __hash__(self):
        return hash(self.uri)

    def __eq__(self, other) -> bool:
        match other:
            case RDFNode(): return self.uri == other.uri
            case _: return False

    def __getattr__(self, pred: str):
        try:
            return self.__getattribute__(pred)
        except AttributeError:
            return self.get_via_pred(pred)

    def __setattr__(self, pred, val: RDFNode | RDFType) -> Optional[RDFNode]:
        if pred.startswith("_") or pred in ('uri', 'gdm'):
            return super().__setattr__(pred, val)
        else:
            return self.create_triple(pred, val)

    def get_via_pred(self, pred: str) -> OrderedSet[RDFNode]:
        """Dynamically resolve attributes as outgoing RDF relations."""
        pred_uri = f'{self._prefix}{pred}'
        query = f'SELECT ?o WHERE {{ <{self.uri}> <{pred_uri}> ?o . }}'
        if not (results := self.gdm.raw_query(query, JSON)):
            raise AttributeError(f'No property "{pred}" for {self.uri}')
        results = results.convert().get('results', {}).get('bindings', [])
        # Return multiple values as a list
        objs = OrderedSet()
        for result in results:
            obj = Box(result['o'])
            objs.add(RDFNode(obj.value) if obj.type == 'uri' else obj.value)
        return objs

    def create_triples(self, **preds: Collection[RDFNode | RDFType] | RDFNode | RDFType) -> RDFNode:
        for verb_name, node_s in preds.items():
            nodes = [node_s] if isinstance(node_s, RDFNode) else node_s
            verb_name = verb_name.removesuffix('_')
            for node in nodes:
                self.create_triple(verb_name, node)
        return self

    def create_triple(self, pred: str, val: RDFNode | RDFType) -> RDFNode:
        """Create a relationship triple (self, pred, obj)."""
        pred_uri = f'{self._prefix}{pred}'
        obj = self._map_val_to_rdf(val)
        query = f'INSERT DATA {{ <{self.uri}> <{pred_uri}> {obj} }}'
        self.gdm.raw_query(query)
        return self

    @classmethod
    def _map_val_to_rdf(cls, val: Any) -> str:
        """TODO (PORFARO): Movu al iu utilaĵaro"""
        match val:
            case RDFNode(): return f'<{val.uri}>'
            case str():
                s = str(val).replace('"', '\\"')
                return f'"{s}"'
            case float(): return f'"{val}"^^<{XSD.decimal}>'
            case int(): return f'"{val}"^^<{XSD.integer}>'
            case bool(): return f'"{str(val).lower()}"^^<{XSD.boolean}>'
            case _: raise ValueError(f'Type "{type(val)}" is not supported yet')

N = RDFNode
