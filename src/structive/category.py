from __future__ import annotations

from more_itertools import bucket, collapse
from more_itertools.recipes import flatten
from neomodel.contrib.sync_.semi_structured import SemiStructuredNode
from numpy.random.mtrand import Sequence

from py2neo import Graph, Node, Relationship, Subgraph
from toolz.functoolz import return_none
import pydash as _
from pydash import chain as c, flow
from itertools import groupby, chain

from src import utils
from src.utils import is_sequence, is_dict, is_all_instance_of_str, is_not_sequence, is_not_dict, is_

graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))

Node().types()
Relationship.type()


class Category:
    def __init__(self, *labels, **props):
        self._subcategories = []
        self._labels = labels
        self._props = props

    def subcategory(self, *args, **kwargs) -> Category:
        self._subcategories.append(new_category := Category(*args, **kwargs))
        return new_category


C = Category


'''
compose(a, b, conjunction=True)  // a(x) & b(x)
compose(a, b, alternative=True)  // a(x) | b(x)
compose(a, [2, 1])          // a(x, y) => b(y, x)
compose(a, reverse=True)    // a(x, y) => b(y, x)
compose(a, b, concat=True)  // a(x), b(y) => c(x, y)
compose(a, b, {'a': [1, 2], 'b': [2, 3]})  // a(x, y), b(w, z) => c(x, y/w, z)
compose(a, b, edge=True)    // a(x, y), b(w, z) => c(x, y/w, z)

opposite(a)
... ?

and
or
not
'''

'''
rel(args=args, props=props)
__call__(self, *rels)
not_
perforate/sub

non = rel(func=not_, arity=1)
perforate = rel(arity=1, args=[holes: bool], func=lambda holes:
like = rel(arity=2,)
'''

def adjust_parameters(params):  # to utils?
    if is_dict(params):
        return None, params
    if is_all_instance_of_str(params):
       return params, None
    if len(params) != 2 or is_not_sequence(params[0]) or is_not_dict(params[1]):
        raise ValueError(f'Bla bla: {params}')
    args, kwargs = params
    return args or [], kwargs or {}


def adjust_for_moc(moc) -> Sequence[Moc]:  # returns single and collection, lol
    match moc:
        case Moc(): return [moc]
        case Node(): raise NotImplementedError
        case Subgraph(): return _.map(moc.nodes, adjust_for_moc)
        case _: raise ValueError


class Moc(Node):
    _is = Relationship.type('IS')

    def __init__(self, *labels, **kwargs):
        # when: kwarg({k: v}) is Moc
        # then: **k** is Moc of value **v**
        # else: props
        super().__init__(*labels, **kwargs)

    def __call__(self, *args, **kwargs) -> Moc | Sequence[Moc]:
        if c(args).every(c().is_string()):
            self._is(child := Moc(*args, **kwargs), self)
            return child

        moc_selector = bucket(args, _.is_instance_of_cmp(Moc))
        children = c([]).concat(
            moc_selector[True],
            c(moc_selector[False]).map(adjust_parameters).map(Moc).value()
        ).for_each(self.ex)
        return children if len(children) > 1 else children[0]

    def ex(self, *mocs: Moc) -> ...:
        raise NotImplementedError

    def is_(self, *mocs: Moc) -> ...:
        raise NotImplementedError

    def thru(self, *mocs) -> Moc:  # TODO: same as is_? or to remove other connections?
        mocs = _.flat_map(mocs, adjust_for_moc)
        self.is_(*mocs)
        return self


# Graphemes (top level)
Graph = Moc('Graph')
a, e, o, u, i = Graph([*'aeoui'])

# Phone(me)s

Phon = Moc('Phon')
Vowel = Phon('Vowel')  # TODO: make spectrum?
Height, Backness, Roundness = Vowel(['Height', 'Backness', 'Roundness'])
High, Mid, Low = Height(['High', 'Mid', 'Low'])
Front, Central, Back = Backness(['Front', 'Central', 'Back'])
Rounded, Unrounded = Roundness(['Rounded', 'Unrounded'])

# TODO: Think how to specify only rounded and infer unrounded
a_sound = Moc(ipa=a).thru(Low, Central, Unrounded)
e_sound = Moc(ipa=e).thru(Mid, Front, Unrounded)
o_sound = Moc(ipa=o).thru(Mid, Back, Rounded)
i_sound = Moc(ipa=i).thru(High, Front, Unrounded)
u_sound = Moc(ipa=u).thru(High, Back, Rounded)





Sem = Moc('Sem')
