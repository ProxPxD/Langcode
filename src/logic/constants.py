from src.logic.gdm import LoginData

neo4j_log = LoginData(
    uri='bolt://localhost:7687',
    user='neo4j',
    password='password',
    database='neo4j',
)

rdf_log = LoginData(
    uri='http://localhost:7200',
    user='langcode',
    password='langcode',
    database='langcode-dev',
)

log = rdf_log

TIMEOUT = 5
