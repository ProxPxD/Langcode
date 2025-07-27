from typing import Optional, LiteralString

from neo4j import Driver, GraphDatabase, Session, Result

from src.logic.gdm import GDM, LoginData


class Neo4jGDM(GDM):
    def __init__(self, log: LoginData, *args, **kwargs):
        super().__init__(log, *args, **kwargs)
        self.driver: Driver = GraphDatabase.driver(log.uri, auth=log.auth)
        self._session: Optional[Session] = None

    def init_session(self, *args,  **kwargs):
        return self.driver.session(*args, **kwargs)

    def raw_query(self, query: LiteralString, **kwargs) -> Result:
        try:
            return self._session.run(query, **kwargs)
        except AttributeError:
            raise  # TODO ?

