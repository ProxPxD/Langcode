from src.logic.db import LoginData

neo4j_log = LoginData(
    uri='bolt://localhost:7687',
    user='neo4j',
    password='password',
    database='neo4j',
)

rdf_log = LoginData(
    uri='http://localhost:43953',  # TODO: Port has to be dynamically got
    user='langcode',
    password='langcode',
    database='langcode-dev',
)

log = rdf_log

TIMEOUT = 5

