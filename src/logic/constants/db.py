import os

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
    port=7001,
    user=os.getenv('GRAPHDB_DEV_USER'),
    password=os.getenv('GRAPHDB_DEV_PASS'),
    database='langcode-dev',
)

rdf_dev_log = LoginData(
    uri='http://localhost',
    port=7001,
    user=os.getenv('GRAPHDB_DEV_USER'),
    password=os.getenv('GRAPHDB_DEV_PASS'),
    database='langcode-dev',
)


TIMEOUT = 5

URI_PREFIX: str = 'http://langcode/'

