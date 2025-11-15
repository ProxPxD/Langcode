from __future__ import annotations

from functools import cached_property
from typing import LiteralString, Sequence

from SPARQLWrapper import SPARQLWrapper, QueryResult, XML, BASIC, POST
from pydantic import BaseModel
from pydash import chain as c

from .login_data import LoginData


class ReadOps(BaseModel):
    SELECT: str = 'SELECT'
    CONSTRUCT: str = 'CONSTRUCT'
    DESCRIBE: str = 'DESCRIBE'
    ASK: str = 'ASK'

class WriteOps(BaseModel):
    INSERT: str = 'INSERT'
    DELETE: str = 'DELETE'
    LD: str = 'LD'
    CLEAR: str = 'CLEAR'

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
        self.database: str = log.database
        self.query_wrapper = SPARQLWrapper(log.endpoint)
        self.update_wrapper = SPARQLWrapper(f'{log.endpoint}/statements')
        self.__class__._gdm = self
        self._set_wrappers(log)

    @cached_property
    def _wrappers(self) -> Sequence[SPARQLWrapper]:
        return self.query_wrapper, self.update_wrapper

    def _set_wrappers(self, log: LoginData) -> None:
        for wrapper in self._wrappers:
            wrapper.setHTTPAuth(BASIC)
            wrapper.setCredentials(*log.auth)
        self.update_wrapper.setMethod(POST)

    def init_session(self, *args,  **kwargs):
        raise NotImplementedError('Not Possible')

    def raw_query(self, query: str, return_format: str = XML, **kwargs) -> QueryResult:
        wrapper = self._get_wrapper(query)
        wrapper.setQuery(query)
        wrapper.setReturnFormat(return_format)
        return wrapper.query()

    def _get_wrapper(self, query: str) -> SPARQLWrapper:
        op: str = (c(query).trim().split('\n')
                   .reject(lambda line: c(dict(UriKeywords()).values()).some(line.startswith).value())
                   .reject(lambda line: not line.strip() or line.startswith('#'))
                   .nth(0).split(' ').nth(0).value())
        match op:
            case _ if op in dict(ReadOps()).values():
                return self.query_wrapper
            case _ if op in dict(WriteOps()).values():
                return self.update_wrapper
            case _: raise ValueError(f'Operation {op} does not belong to any read nor write RDF operations')



