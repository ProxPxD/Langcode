from itertools import product
from unittest import SkipTest

from parsimonious.exceptions import IncompleteParseError, VisitationError

from grammar import grammar, GrammarVisitor, T
from tests.abstractTest import AbstractTest
from tests.testutils import sort_result


@sort_result(0, by_length=True)
def gen_affix_parameters():
        affixes = ('en', 'e^n')
        pms = ('+', '-', '.')
        verb_dict = {'+': 'add', '-': 'remove'}
        get_opt = lambda affix: '_with_optional' if '^' in affix else ''
        for pm, affix in product(pms, affixes):
            yield f'{verb_dict[pm]}_postfix{get_opt(affix)}', pm+affix
            yield f'{verb_dict[pm]}_prefix{get_opt(affix)}', affix+pm


class GrammarTest(AbstractTest):
    @classmethod
    def _get_test_name(cls) -> str:
        return 'Grammar'

    is_generated = False
    visitor = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_generated:
            GrammarTest.visitor = GrammarVisitor()
            self.gen_all_grammar_tests()
            self.is_generated = True

    grammar_parameters = [
        *list(gen_affix_parameters()),

        ('add_circumfix', 'ge+t'),
        ('remove_circumfix', 'ge-t'),
        ('create_interfix', '+o+'),
        ('add_larger_optional_prefix', 'i(ch)^+'),           # add i if starts with ch else add ich
        ('add_larger_optional_postfix', '+i(ch)^'),
        ('two_actions_equal', 'ge-,-t'),                 # remove prefix ge- and  remove suffix -t
        ('two_actions_equal_with_parenthesis', '(ge-),(-t)'),                 # remove prefix ge- and  remove suffix -t
        ('two_actions_ordered', 'ge-;-t'),               # remove prefix ge- than remove suffix -t
        ('two_actions_ordered_with_parenthesis', '(ge-);(-t)'),               # remove prefix ge- than remove suffix -t


        ('simple_condition', '-u?-u:+u'),                # if it ends          with u      than remove u else add it
        ('elseless_condition', '-r?-r'),                 # if it ends          with r      than remove r (else nothing)
        ('trueless_condition', '-a?:+a'),                # if it ends          with a      than nothing else add a
        ('trueless_elseless_contition', '-a?:', False),  # if it ends          with a      than nothing
        ('or_condition', '-a|-o?+j:+i'),                 # if it ends          with a or 0 than add j else add i
        ('short_action_remove', 'e-?-'),                 # if it starts        with e      than remove it
        ('short_action_add',    '~e-?+'),                # if it doesn't start with e      than add it

        ('two_conditions_equal', '(-a|-o?-),(-a?+y:+a)'),          # Two equal conditions
        ('two_conditions_ordered', '-s?+y;-y?+t:+s'),              # Two ordered conditions
        ('many_conditions_ordered', '-a?-;-k?-k+e^cz;+k'),  # Many ordered conditions
        ('many_conditions_ordered_with_reference', '-a?-;-k?-k+e^cz;+k;&?1?+a'),  # Many ordered conditions
        ('prefixes_and_suffixes', 'z+-a+u'),
        ('prefixes_and_suffixes_in_same_condition', '-a?z+-a+u:m+'),
    ]

    @classmethod
    def gen_all_grammar_tests(cls):
        for (name, expr, *expected_param) in cls.grammar_parameters:
            should_succeed = True if not expected_param else expected_param[0]
            name = name.lower()
            grammar_test_name = f'test_{name}'
            grammar_test = cls.gen_test_grammar(expr, should_succeed)
            setattr(GrammarTest, grammar_test_name, grammar_test)
            if should_succeed:
                visit_test_name = f'test_visit_{name}'
                visit_test = cls.gen_test_visit(expr)
                setattr(GrammarTest, visit_test_name, visit_test)

    @classmethod
    def gen_test_grammar(cls, expr: str, should_succeed: bool):
        def test_grammar(self, *args):
            try:
                tree = grammar.parse(expr)
                if not should_succeed:
                    self.fail()  # TODO
            except IncompleteParseError as ipe:
                if should_succeed:
                    self.fail(f'IncompleteParseError {ipe.args}')  # TODO
            except SkipTest as st:
                raise st
            except Exception as e:
                self.fail('Unknown exception')
        return test_grammar

    @classmethod
    def gen_test_visit(cls, expr: str):
        def test_visit(self, *args):
            try:
                tree = grammar.parse(expr)
                structure = cls.visitor.visit(tree)
                self._test_structure(structure)
            except IncompleteParseError as ipe:
                self.skipTest('Error in parsing, not in visitor')
            except SkipTest as st:
                raise st
            except VisitationError as vel:
                self.fail(f'VisitationError {vel.args}')
            except Exception as e:
                self.fail('Unknown exception')
        return test_visit

    def _test_structure(self, structure):
        self._test_context(structure)
        self._test_ordered_expression(structure)

    def _test_context(self, structure):
        self.assertIn(T.context, structure)

    def _test_ordered_expression(self, structure):
        self.assertIn(T.ordered_expressions, structure)
        self.assertIsInstance(structure[T.ordered_expressions], list)
        for same_order in structure[T.ordered_expressions]:
            self._test_same_order_expression(same_order)

    def _test_same_order_expression(self, same_order):
        self.assertIsInstance(same_order, list)
        for change in same_order:
            self._test_change(change)

    # Think of name
    def _test_change(self, change):
        self.assertIsInstance(change, dict)
        self.assertIn(T.operation, change)
        self.assertIsInstance(change[T.operation], str)
        self.assertIn(change[T.operation], (T.prefix, T.postfix, T.interfix, T.circumfix))
        self.assertIn(T.operands, change)
        self.assertIsInstance(change[T.operands], list)
