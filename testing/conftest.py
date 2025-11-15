import pytest
from testing.consts import KEEP_GRAPH_FLAG


def pytest_addoption(parser):
    parser.addoption(KEEP_GRAPH_FLAG, action='store_true', help='Ne forigu la grafon')
