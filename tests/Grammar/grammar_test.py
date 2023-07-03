from itertools import product

from parsimonious.exceptions import IncompleteParseError

from grammar import grammar
from tests.abstractTest import AbstractTest
from tests.testutils import sort_result


@sort_result(0, by_length=True)
def gen_affix_parameters():
        affixes = ('en', 'e^n')
        pms = ('+', '-')
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_generated:
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

    ]

    @classmethod
    def gen_all_grammar_tests(cls):
        for (name, expr, *expected_param) in cls.grammar_parameters:
            expected = True if not expected_param else expected_param[0]
            test_name = f'test_{name}'.lower()
            test = cls.gen_test_grammar(expr, expected)
            setattr(GrammarTest, test_name, test)

    @classmethod
    def gen_test_grammar(cls, expr: str, should_succeed):
        def test_grammar(self, *args):
            try:
                tree = grammar.parse(expr)
                if not should_succeed:
                    self.fail()  # TODO
            except IncompleteParseError as e:
                if should_succeed:
                    self.fail(e.args)  # TODO
            except Exception as e:
                self.fail('Unknown exception')
        return test_grammar

    def test_or_condition(self):
        self.run_current_test_with_params()