from contextlib import contextmanager

import pytest

# @contextmanager
# def database():
#     try:
#         config.DATABASE_URL = 'bolt://neo4j:password@localhost:7687'
#     finally:
#         db.cypher_query('MATCH (n) DETACH DELETE n')


if __name__ == '__main__':
        pytest.main([
            '-s',
            '-v',
            #'--log-cli-level=DEBUG',
            'tests/gen_test.py',
        ])
