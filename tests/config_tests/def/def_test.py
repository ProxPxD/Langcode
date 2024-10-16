from collections import namedtuple

from tests.lang_code_test import LangCodeTestGenerator


class DefTestGenerator(LangCodeTestGenerator):
    """
    aims to ensure the right functionality of "def" key and its configuration's structure
    but not the separate functionalities of its sub keys
    """
    tc = namedtuple('tc', ['name', 'descr', ''])

    tcs = [

    ]