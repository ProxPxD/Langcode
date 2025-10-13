from functools import cache

from SPARQLWrapper import SPARQLWrapper, JSON
from box import Box

from src.logic.constants import URI_PREFIX
from src.logic.db import GDM

from pydash import chain as c
import pydash as _

class RDFNode:
    # TODO: Think whether to pass attributes that are not plural somewhere
    def __init__(self, uri: str):
        self.uri = uri

    @cache
    @property
    def gdm(self) -> GDM:
        return GDM.curr()

    def __repr__(self) -> str:
        return f'<RDFNode {self.uri}>'

    def __getattr__(self, pred: str):
        """Dynamically resolve attributes as outgoing RDF relations."""
        pred_uri = f'{URI_PREFIX}{pred}'
        query = f'SELECT ?o WHERE {{ <{self.uri}> <{pred_uri}> ?o . }}'
        if not (results := self.gdm.raw_query(query, JSON)):
            raise AttributeError(f'No property "{pred}" for {self.uri}')
        results = results.convert().get('results', {}).get('bindings', [])
        # Return multiple values as a list
        objs = []
        for result in results:
            obj = Box(result['o'])
            objs.append(RDFNode(obj.value) if obj.type == 'uri' else obj.value)
        return objs