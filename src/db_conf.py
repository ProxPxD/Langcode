from neomodel import config


def configure():
    #config.DATABASE_URL = 'bolt://neo4j_username:neo4j_password@localhost:7687'
    config.DATABASE_URL = 'bolt://neo4j:password@localhost:7687'