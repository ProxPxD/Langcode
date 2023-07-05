from dataclasses import dataclass
from typing import Iterable

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor, Node

from tests.testutils import reapply


@dataclass
class Terms:
    main = 'main'
    context = 'context'
    ordered_expressions = 'ordered_expressions'
    prefix = 'prefix'
    postfix = 'postfix'
    interfix = 'interfix'
    circumfix = 'circumfix'

    plus = 'plus'
    minus = 'minus'
    l = 'l'
    r = 'r'

    operation = 'operation'  # prefix, postfix, etc.
    operation_type = 'operation_type'  # +/-
    expressions = 'expressions'
    operands = 'operands'


T = Terms

grammar = Grammar(
    r"""
    main                    = (context context_sep)? ordered_expressions
    context                 = ""
    ordered_expressions     = (same_order_whole  / (l same_order_whole r))    (diff_order_sep ordered_expressions)? 
    same_order_whole        = (same_order_single / (l same_order_single r))   (same_order_sep same_order_whole)? 
    same_order_single       = (cond_whole / segment)
    cond_whole              = (complex_cond cond_sep cond_quasi_expr (else_sep cond_quasi_expr)?) / (complex_cond cond_sep else_sep cond_quasi_expr)
    cond_quasi_expr         = segment_single / pm
    complex_cond            = basic_cond (or_sep complex_cond)?
    basic_cond              = not? ((alph_expr minus) / (minus alph_expr))
    segment                 = interfix / segment_single
    segment_single          = circumfix / prefix / postfix
    prefix                  = ((alph_expr pm) (prefix / postfix)?) 
    postfix                 = ((pm alph_expr) postfix?)
    circumfix               = alph_expr pm alph_expr
    interfix                = (minus alph_expr minus) / (plus alph_expr plus)

    alph_expr               = (opt_expr alph_expr?) / (alph_full alph_expr?) 
    opt_expr                = (alph opt) / (l alph_full r opt)
    alph_full               = ((l alph_full r) alph_full?) / alph+
    alph                    = ~r"[a-z]"
    
    pm                      = plus / minus
    plus                    = "+"
    minus                   = "-"
    opt                     = "^"
    not                     = "~"
    l                       = "("
    r                       = ")"
    ref                     = "&"
    
    context_sep             = ~r"\s*@\s*"
    diff_order_sep          = ~r"\s*;\s*"
    same_order_sep          = ~r"\s*,\s*"
    cond_sep                = ~r"\s*\?\s*"
    else_sep                = ~r"\s*:\s*"
    or_sep                  = ~r"\s*\|\s*"
    """
)


class GrammarVisitor(NodeVisitor):
    def visit_main(self, node: Node, visited_children: list[Node]):
        context, ordered_expressions = visited_children
        # TODO: when implement context change none
        return {T.context: None, T.ordered_expressions: ordered_expressions}

    def visit_ordered_expressions(self, node: Node, visited_children):
        return self._visit_potentially_parenthesified_with_sep(visited_children, 1)

    def visit_same_order_whole(self, node: Node, visited_children):
        return self._visit_potentially_parenthesified_with_sep(visited_children, 2)

    def _visit_potentially_parenthesified_with_sep(self, to_process, depth=1):
        curr = reapply(depth, lambda arr: arr[0], to_process)
        extended = self._deparethesify(curr)
        if isinstance(to_process[1], list):
            extended.extend(to_process[1][0][1])
        return extended

    def _deparethesify(self, to_deparethesify):
        if not len(to_deparethesify):
            return to_deparethesify
        if isinstance(to_deparethesify[0], Node) and to_deparethesify[0].expr_name == T.l:
            return to_deparethesify[1]
        return to_deparethesify

    def visit_same_order_single(self, node: Node, visited_children):
        return visited_children[0]

    def visit_segment(self, node: Node, visited_children):
        return visited_children[0]

    def visit_segment_single(self, node: Node, visited_children):
        return visited_children[0]

    def visit_prefix(self, node: Node, visited_children):
        return self._visit_operations(node, T.prefix, visited_children)

    def visit_postfix(self, node: Node, visited_children):
        return self._visit_operations(node, T.postfix, visited_children)

    def visit_interfix(self, node: Node, visited_children: list[Node]):
        op1, inter, op2 = self._to_text(node.children[0].children)
        op = op1 if op1 == op2 else None
        return [{T.operation: T.interfix, T.operation_type: op, T.operands: [inter]}]

    def visit_circumfix(self, node: Node, visited_children):
        pre, op, post = node.children
        return [{T.operation: T.circumfix, T.operation_type: op.text, T.operands: [pre.text, post.text]}]

    def _visit_operations(self, node: Node, operation: str, visited_children):
        curr = {T.operation: operation, **self._get_operation_expression_tuple(node)}
        first, others = visited_children
        other = [] if not isinstance(others, list) else others[0]
        return [curr] + other

    def _get_operation_expression_tuple(self, node: Node) -> dict[str, str]:
        children = node.children[0].children
        expressions = list(filter(lambda s: s.isalnum(), map(self._to_text, children)))
        operation_type = next(filter(lambda n: not n.text.isalnum(), children)).text
        return {T.operation_type: operation_type, T.operands: expressions}

    def _to_text(self, to_change: Node | Iterable[Node]) -> str | tuple[str, ...]:
        return to_change.text if isinstance(to_change, Node) else tuple(filter(self._to_text, to_change))

    def generic_visit(self, node: Node, visited_children: list[Node]):
        """ The generic visit method. """
        return visited_children or node


v = GrammarVisitor()
#-p-c
parsed = grammar.parse('(-p+f),a+;j+a,(+s)')  # '-p+f,a+;j+a,+s'
output = v.visit(parsed)
#print('#'*100)
#print(parsed)


if visit := True:
    print('#'*100)
    print('Visitor: ')
    print('\tContext:', output[T.context])
    print('\tOrdered:')
    for i, ordered in enumerate(output[T.ordered_expressions]):
        print(f'\t\t{i+1}. Same order:')
        for j, same_order in enumerate(ordered):
            print(f'\t\t\t{j+1}. {same_order}')

    print('\n'*3)
    #print(output)

#((alph+ opt)? alph_expr) /
# text = '-an+ta'
# tree = grammar.parse(text)
# if should_print := 0:
#     print('tree text:', tree.text)
#     print('tree expr:', tree.expr)
#     alph_expr = tree.children[1].children[0].children[0].children[0].children[0]#.children[1]
#     print('alph expr text:', alph_expr.text)
#     print('alph expr expr:', alph_expr.expr_name)
#     print('alph expr children:')
#     for child in alph_expr.children:
#         print(f'  - {child.expr.name:10}: ', child.text)
# parsimonious.expressions.Quantifier
# seq = parsimonious.expressions.Sequence()
# seq.parse()
#print(tree)
#iv = NodeVisitor()
#output = iv.visit(tree)
#print(output)
# Grammar('''
#     tt_cond      =  tt_alph+ tt_cond_sep tt_alph+
#     tt_alph      = ~r"[a-z]"
#     tt_cond_sep  = ~r"\s*\?\s*"
# ''').parse('a?b')
#
# Grammar('''
#     t_cond_whole               = t_cond t_cond_sep t_single_expr (t_else_sep t_single_expr)?
#     t_cond                    = (t_alph_expr t_minus) / (t_minus t_alph_expr)
#
#     t_single_expr             = (t_alph_expr t_pm) / (t_pm t_alph_expr)
#     t_alph_expr               = t_alph+
#     t_alph                    = ~r"[a-z]"
#
#     t_pm                      = t_plus / t_minus
#     t_plus                    = "+"
#     t_minus                   = "-"
#     t_cond_sep                = ~r"\s*\?\s*"
#     t_else_sep                = ~r"\s*:\s*"
# ''').parse("-u?-u:+u")
#
#
# tree = grammar.parse('(a)(b)+')
# tree = grammar.parse('((ab))+')
# tree = grammar.parse('(a)((b)(c))+')
#
