from contextlib import contextmanager

import pytest
from neomodel import db, config


@contextmanager
def database():
    try:
        config.DATABASE_URL = 'bolt://neo4j:password@localhost:7687'
    finally:
        db.cypher_query('MATCH (n) DETACH DELETE n')


if __name__ == '__main__':
    with database():
        pytest.main([
            '-s',
            '-v',
            #'--log-cli-level=DEBUG',
            'neomodel_utilities_tests/',
        ])
