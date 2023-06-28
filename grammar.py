from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor


grammar = Grammar(
    r"""
    main                    = (context context_sep)? ordered_expr
    context                 = ""
    ordered_expr            = same_order_expr        (diff_order_sep ordered_expr)? 
    same_order_expr         = single_same_order_expr (same_order_sep same_order_expr)? 
    single_same_order_expr  = cond_expr / single_expr
    cond_expr               = (cond cond_sep single_expr (else_sep single_expr)?) / (cond cond_sep else_sep single_expr)
    cond                    = not? ((alph_expr minus) / (minus alph_expr))
    single_expr             = single_expr_pre / single_expr_post
    single_expr_pre         = (alph_expr pm) single_expr_pre?
    single_expr_post        = (pm alph_expr) single_expr_post?

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
    
    context_sep             = ~r"\s*@\s*"
    diff_order_sep          = ~r"\s*;\s*"
    same_order_sep          = ~r"\s*,\s*"
    cond_sep                = ~r"\s*\?\s*"
    else_sep                = ~r"\s*:\s*"
    """
)
#((alph+ opt)? alph_expr) /
text = '-an+ta'
tree = grammar.parse(text)
if should_print := 0:
    print('tree text:', tree.text)
    print('tree expr:', tree.expr)
    alph_expr = tree.children[1].children[0].children[0].children[0].children[0]#.children[1]
    print('alph expr text:', alph_expr.text)
    print('alph expr expr:', alph_expr.expr_name)
    print('alph expr children:')
    for child in alph_expr.children:
        print(f'  - {child.expr.name:10}: ', child.text)
#print(tree)
#iv = NodeVisitor()
#output = iv.visit(tree)
#print(output)
Grammar('''
    tt_cond      =  tt_alph+ tt_cond_sep tt_alph+
    tt_alph      = ~r"[a-z]"
    tt_cond_sep  = ~r"\s*\?\s*"
''').parse('a?b')

Grammar('''
    t_cond_expr               = t_cond t_cond_sep t_single_expr (t_else_sep t_single_expr)? 
    t_cond                    = (t_alph_expr t_minus) / (t_minus t_alph_expr)
    
    t_single_expr             = (t_alph_expr t_pm) / (t_pm t_alph_expr)
    t_alph_expr               = t_alph+
    t_alph                    = ~r"[a-z]"
    
    t_pm                      = t_plus / t_minus
    t_plus                    = "+"
    t_minus                   = "-"
    t_cond_sep                = ~r"\s*\?\s*"
    t_else_sep                = ~r"\s*:\s*"
''').parse("-u?-u:+u")


tree = grammar.parse('(a)(b)+')
tree = grammar.parse('((ab))+')
tree = grammar.parse('(a)((b)(c))+')


"""
 a >> b
 a,b >> e,f >> c,d
 
"""
