from typing import Optional

from neo4j import GraphDatabase, Driver, Session, Query, Result


class DBManager:
    """
    DBM
    """
    def __init__(self, *,
            uri: str,
            user: str = None,
            password: str = None,
            auth: tuple[str, str] = None,
            db: str = None,

        ):
        if not auth and (not user or not password):
            raise ValueError(f'{DBManager.__name__} requires "auth" or "user" and "password" in init')
        self.driver: Driver = GraphDatabase.driver(uri, auth=(user or auth[0], password or auth[1]))
        self.db: Optional[str] = db

    def __del__(self):
        self.driver.close()

    def run(self, query: str | Query, **kwargs) -> Result:
        with self.driver.session(database=self.db) as session:
            return session.run(query, **kwargs)
