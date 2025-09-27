from __future__ import annotations

from typing import LiteralString

from SPARQLWrapper import SPARQLWrapper, QueryResult
from pydantic import BaseModel
from pydash import chain as c

from login_data import LoginData


class ReadOps(BaseModel):
    SELECT: str = 'SELECT'
    CONSTRUCT: str = 'CONSTRUCT'
    DESCRIBE: str = 'DESCRIBE'
    ASK: str = 'ASK'

class WriteOps(BaseModel):
    INSERT: str = 'INSERT'
    DELETE: str = 'DELETE'
    LD: str = 'LD'

class UriKeywords(BaseModel):
    PREFIX: str = 'PREFIX'
    BASE: str = 'BASE'

class QueryKeywords(ReadOps, WriteOps, UriKeywords):
    pass


QK = QueryKeywords


class GDM:
    """
    Graph Database Manager -- Interface for common queries
    """

    _gdm = None

    @classmethod
    def curr(cls) -> GDM:
        return cls._gdm

    def __init__(self, log: LoginData, *args, **kwargs):
        super().__init__(log, *args, **kwargs)
        self.query_wrapper = SPARQLWrapper(query_endpoint := f'{log.uri}/repositories/{log.repo}')
        self.update_wrapper = SPARQLWrapper(f'{query_endpoint}/statements')
        self._gdm = self

    def init_session(self, *args,  **kwargs):
        raise NotImplementedError('Not Possible')

    def raw_query(self, query: LiteralString, **kwargs) -> QueryResult:
        wrapper = self._get_wrapper(query)
        wrapper.setQuery(query)
        return wrapper.query()

    def _get_wrapper(self, query: LiteralString) -> SPARQLWrapper:
        op: str = (c(query).trim().split('\n')
         .reject(lambda line: c(dict(UriKeywords()).values()).some(line.startswith))
         .nth(0).split(' ').nth(0).value())
        match op:
            case _ if op in dict(ReadOps()).values():
                return self.query_wrapper
            case _ if op in dict(WriteOps()).values():
                return self.update_wrapper
            case _: raise ValueError(f'Operation {op} does not belong to any read nor write RDF operations')



