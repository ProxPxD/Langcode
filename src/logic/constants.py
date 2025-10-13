from src.logic.db import LoginData

neo4j_log = LoginData(
    uri='bolt://localhost',
    port=7687,
    user='neo4j',
    password='password',
    database='neo4j',
)

rdf_log = LoginData(
    uri='http://localhost',
    port=43953,
    user='langcode',
    password='langcode',
    database='langcode-dev',
)

log = rdf_log

TIMEOUT = 5

URI_PREFIX: str = 'http://langcode/'

