import re

from toolz.curried import *
from operator import *
import pydash as _
from pydash import chain as c
from pydash import spread

from toolz.curried.operator import *

print(
    'nth',
    _.nth(list(range(5)), -2),
    _.nth([1, 2, 3], 5)
)


arr = ['banana', 'apple']

print(
    c().map_(str.upper).pluck('0').apply('|'.join).apply(lambda s: s.join).flow(str.lower),
    c().map_(str.upper).pluck('0').apply('|'.join).apply(lambda s: s.join).flow(str.lower)(arr),
    c().map_(str.upper).pluck('0').apply('|'.join).apply(lambda s: s.join).flow(str.lower)(arr)(['xD', 'lol']),
    c().map_(str.upper).pluck('0').apply('|'.join).apply(lambda s: s.join)(arr),
    c().map_(str.upper).pluck('0').apply('|'.join).apply(lambda s: s.join)(arr)(['xD', 'lol']),
    c().map_(str.upper).pluck('0').apply('|'.join),
    c().map_(str.upper).pluck('0').apply('|'.join)(arr),
    _.flow('|'.join)(arr)
    ,
    sep='\n'
)

print('\n'*3)

compile_regexes = c().map_(re.compile)
compile_regexes_to_funcs = compile_regexes.pluck('search')
# join_regexes_to_juxt = _.flow(compile_regexes_to_funcs, _.spread(_.juxtapose))
join_regexes_to_juxt = c().apply(compile_regexes_to_funcs).apply(_.spread(_.juxtapose))
is_matching = curry(c().apply(join_regexes_to_juxt).flow)

regexes = ['^a', '^b']

print(
    compile_regexes(regexes),
    compile_regexes_to_funcs(regexes),
    join_regexes_to_juxt(regexes),
    join_regexes_to_juxt(regexes)('banana'),
    is_matching(any),
    is_matching(any)(regexes),
    is_matching(any)(regexes)('banan'),
    # '',
    # c().apply(join_regexes_to_juxt),
    # c().apply(join_regexes_to_juxt)(regexes),
    # c().apply(join_regexes_to_juxt)(regexes)('banan'),
    # '',
    # c().apply(join_regexes_to_juxt).flow(any),
    # c().apply(join_regexes_to_juxt).flow(any)(regexes),
    # c().apply(join_regexes_to_juxt).flow(any)(regexes)('banan'),
    sep='\n',
)
