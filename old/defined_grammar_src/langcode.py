from __future__ import annotations

import abc
import operator as op
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from functools import reduce
from itertools import product
from typing import Iterable, Callable

# from parsimonious.grammar import Grammar
# from parsimonious.nodes import NodeVisitor, Node

# from utils import reapply, to_last_list, clean_empty



@dataclass(frozen=True)
class Operators:
    l = '('
    r = ')'
    opt = '^'
    plus = '+'
    minus = '-'
    dot = '.'


@dataclass(frozen=True)
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
    opt = 'opt'
    alph = 'alph'
    alph_expr = 'alph_expr'
    opt_expr = 'opt_expr'

    operation = 'operation'  # prefix, postfix, etc.
    operation_type = 'operation_type'  # +/-
    expressions = 'expressions'
    operands = 'operands'
    content = 'content'
    content_type = 'content_type'




T = Terms
O = Operators



def get_name(instance):
    return instance.name if 'name' in instance.__dir__ else instance if isinstance(instance, str) else None


class MetaLanguages(type):
    _languages: dict = {}
    _current: Language | None = None

    def __getitem__(cls, lang: str | Language) -> Language:
        return cls._languages[get_name(lang)]

    def __setitem__(cls, name: str, lang: Language):
        if isinstance(lang, Language):
            cls._languages[name] = lang
            cls._current = lang
        else:
            raise NotImplementedError

    def __contains__(self, name):
        return name in self._languages

    def keys(cls):
        return cls._languages.keys()

    def values(cls):
        return cls._languages.values()

    def items(cls):
        return cls._languages.items()

    @property
    def current(cls) -> Language | None:
        return cls._current

    @current.setter
    def current(cls, new_current: Language | str | None) -> None:  # TODO test setting ways
        name = get_name(new_current)
        if new_current is None or name in cls._languages:
            cls._current = cls._languages[name]
        else:
            raise NotImplementedError  # TODO test error

    def associate(cls, to_associate: Iterable | object) -> None:  # TODO add annotation
        if cls._current is not None:
            cls._current.associate(to_associate)


class languages(metaclass=MetaLanguages):  # TODO test access
    pass


class Language:
    def __init__(self, name: str):
        languages[name] = self
        self._name: str = name
        self._morphemes: list = []

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self):
        return f'{self.__class__.__name__}({str(self.__dict__)[1:-2]})'

    def associate(self, to_associate: Iterable | object) -> None:  # TODO add annotation
        if not isinstance(to_associate, Iterable):
            self._associate_single(to_associate)
        else:
            deque(map(self.associate, to_associate), 0)

    def _associate_single(self, to_associate) -> None:  # TODO add annotation
        pass


class FormPotential:
    def __init__(self, *forms: str | FormPotential):
        self.basic_forms: list[str | FormPotential] = list(forms)

    @property
    def forms(self) -> Iterable[str]:
        for form in self.basic_forms:
            if isinstance(form, FormPotential):
                yield from form.forms
            else:
                yield form

    @property
    def max_form(self) -> str:
        return max(self.forms, key=len)

    def insert_as_first(self, form_to_insert_to: str) -> str:
        return self.insert_at(form_to_insert_to, 1)

    def insert_as_last(self, form_to_insert_to: str) -> str:
        return self.insert_at(form_to_insert_to, -1)

    def insert_at(self, form_to_insert_to: str, at: int) -> str:
        if at < 0:
            return self._inverse_problem(FormPotential.insert_at, form_to_insert_to, at)
        place = at - 1
        concat = self._concat_op(place)
        scores = {}
        for form in self.forms:
            concated = concat(form_to_insert_to, form)
            true_form = self.get_form_at(concated, at)
            scores[form] = (len(true_form) - len(form)), len(form), concated
        ordered = sorted(scores, key=lambda form: scores[form][1], reverse=True)
        ordered = sorted(ordered, key=lambda form: scores[form][0], reverse=True)
        return scores[ordered[0]][2]

    def remove_at(self, form_to_remove_from: str, at: int) -> str:
        if at < 0:
            return self._inverse_problem(FormPotential.remove_at, form_to_remove_from, at)
        place = at-1
        to_remove = self.get_form_at(form_to_remove_from, at)
        return form_to_remove_from[:place] + form_to_remove_from[place:].replace(to_remove, '')

    def is_at(self, form_to_check: str, at: int):
        return self.get_form_at(form_to_check, at) != ''

    def get_form_at(self, form_to_check: str, at: int) -> str:
        if not at:
            raise ValueError
        if at < 0:
            return self._inverse_problem(FormPotential.get_form_at, form_to_check, at)
        place = at - 1
        placements = ((form, form_to_check.index(form) if form in form_to_check else None) for form in self.forms)
        existing = filter(lambda t: t[1] is not None, placements)
        corrects = filter(lambda t: t[1] == place, existing)
        increasing = sorted(corrects, key=lambda c: len(c[0]), reverse=True)
        return increasing[0][0] if increasing else ''

    def _inverse_problem(self, problem: Callable, form: str, at: int):
        reverse_result = problem(~self, form[::-1], -at)
        return reverse_result[::-1]

    def _concat_op(self, place: int) -> Callable[[str, str], str]:
        return lambda form_to_concat_to, concat_form: form_to_concat_to[:place] + concat_form + form_to_concat_to[place:]

    def _calculate_place(self, at: int) -> int:
        sign = at//abs(at)
        return sign*(abs(at) - 1)

    def __repr__(self) -> str:
        return repr(tuple(map(str, self.forms)))

    def __invert__(self) -> FormPotential:
        return FormPotential(*tuple(map(lambda s: s[::-1], self.forms)))

    def __or__(self, other: FormPotential | str) -> FormPotential:
        return FormPotential(self, other)

    def __add__(self, other: FormPotential | str) -> FormPotential:
        if isinstance(other, str):
            other = FormPotential(other)
        return FormPotential(*tuple(f1+f2 for f1, f2 in zip(self.forms, other.forms)))

    def __mul__(self, other: FormPotential | str) -> FormPotential:
        if isinstance(other, str):
            other = FormPotential(other)
        return FormPotential(*tuple(f1+f2 for f1, f2 in product(self.forms, other.forms)))

# SameOrderLevel = tuple[list[Morpheme], list[Morpheme]]
# Ordered = list[SameOrderLevel]

class Morpheme:

    def __init__(self, *contents: tuple[Morpheme | str, ...]):
        languages.associate(self)
        self._interpretation: list[tuple[list[Morpheme], list[Morpheme]]]
        # TODO: continue here
        # for content in contents:
        #     match content:
        #         case Morpheme():
        #             self._interpretation = content
        #         case str():
        #             self._interpretation = GrammarVisitor.interpret(content)
        #         case _:
        #             self._interpretation = NullMorpheme()

    def __call__(self, form: str):
        return self.apply_to(form)

    @abstractmethod
    def apply_to(self, form: str) -> str:
        return self._interpretation(form)

    @property
    def form(self) -> str:
        return self._interpretation.form

    def associate_to(self, lang: str | Language) -> Morpheme:
        languages[lang].associate(self)
        return self

    def __repr__(self) -> str:
        return self.form

    def __add__(self, morpheme: Morpheme) -> Morpheme:
        raise NotImplementedError

# Affixes
# eme Affix():
# 	pass

class NullMorpheme(Morpheme):
    def __init__(self):
        super().__init__(self)

    def __call__(self, to_apply_to: str):
        return to_apply_to

    @property
    def form(self) -> str:
        return ''


class Affix(Morpheme, ABC):
    def __init__(self, content: str, operation_type: str = O.dot):
        super().__init__(self)
        self.content: FormPotential = FormPotential(content)
        self.kind: str = operation_type


class Adfix(Affix):
    _at: int = 0

    def apply_to(self, form: str, kind: str = None) -> str:
        kind = kind or self.kind
        match kind:
            case O.plus:  return self.content.insert_at(form, self._at)  # TODO last: how to economically use FormPotential?
            case O.minus: return self.content.remove_at(form, self._at)
            case O.dot:   return self.apply_to(form, O.minus if self.content.is_at(form, self._at) else O.plus)

    @property
    def form(self) -> str:
        return '|'.join(map(lambda bf: bf[:self._at] + self.kind + bf[self._at:], self.content.forms))


class Prefix(Adfix):
    _at = 1


class Postfix(Adfix):
    _at = -1


class Circumfix(Morpheme):
    def __init__(self, pre: str, post: str, kind: str = None):
        super().__init__(self)
        self._kind = kind
        self.prefix = Prefix(pre, kind)
        self.postfix = Postfix(post, kind)

    @property
    def kind(self) -> str:
        return self._kind

    @kind.setter
    def kind(self, kind: str):
        self.prefix.kind = kind
        self.postfix.kind = kind

    def apply_to(self, form: str, kind: str = None) -> str:
        kind = kind or self.kind
        for adfix in (self.prefix, self.postfix):
            form = adfix.apply_to(form, kind)
        return form

    @property
    def form(self) -> str:
        return self.prefix.content.max_form + self.kind + self.postfix.content.max_form


class Infix(Affix):  # tmesis
    pass


class Interfix(Affix):
    pass


# ?? Simulfix 	mouse → mice == ?
# ?? Suprafix  pro'duce vs 'produce  ?= vocalic

# end affixes
from __future__ import annotations

import abc
import operator as op
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from functools import reduce
from itertools import product
from typing import Iterable, Callable

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor, Node

from utils import reapply, to_last_list, clean_empty



@dataclass(frozen=True)
class Operators:
    l = '('
    r = ')'
    opt = '^'
    plus = '+'
    minus = '-'
    dot = '.'


@dataclass(frozen=True)
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
    opt = 'opt'
    alph = 'alph'
    alph_expr = 'alph_expr'
    opt_expr = 'opt_expr'

    operation = 'operation'  # prefix, postfix, etc.
    operation_type = 'operation_type'  # +/-
    expressions = 'expressions'
    operands = 'operands'
    content = 'content'
    content_type = 'content_type'




T = Terms
O = Operators



def get_name(instance):
    return instance.name if 'name' in instance.__dir__ else instance if isinstance(instance, str) else None


class MetaLanguages(type):
    _languages: dict = {}
    _current: Language | None = None

    def __getitem__(cls, lang: str | Language) -> Language:
        return cls._languages[get_name(lang)]

    def __setitem__(cls, name: str, lang: Language):
        if isinstance(lang, Language):
            cls._languages[name] = lang
            cls._current = lang
        else:
            raise NotImplementedError

    def __contains__(self, name):
        return name in self._languages

    def keys(cls):
        return cls._languages.keys()

    def values(cls):
        return cls._languages.values()

    def items(cls):
        return cls._languages.items()

    @property
    def current(cls) -> Language | None:
        return cls._current

    @current.setter
    def current(cls, new_current: Language | str | None) -> None:  # TODO test setting ways
        name = get_name(new_current)
        if new_current is None or name in cls._languages:
            cls._current = cls._languages[name]
        else:
            raise NotImplementedError  # TODO test error

    def associate(cls, to_associate: Iterable | object) -> None:  # TODO add annotation
        if cls._current is not None:
            cls._current.associate(to_associate)


class languages(metaclass=MetaLanguages):  # TODO test access
    pass


class Language:
    def __init__(self, name: str):
        languages[name] = self
        self._name: str = name
        self._morphemes: list = []

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self):
        return f'{self.__class__.__name__}({str(self.__dict__)[1:-2]})'

    def associate(self, to_associate: Iterable | object) -> None:  # TODO add annotation
        if not isinstance(to_associate, Iterable):
            self._associate_single(to_associate)
        else:
            deque(map(self.associate, to_associate), 0)

    def _associate_single(self, to_associate) -> None:  # TODO add annotation
        pass


class FormPotential:
    def __init__(self, *forms: str | FormPotential):
        self.basic_forms: list[str | FormPotential] = list(forms)

    @property
    def forms(self) -> Iterable[str]:
        for form in self.basic_forms:
            if isinstance(form, FormPotential):
                yield from form.forms
            else:
                yield form

    @property
    def max_form(self) -> str:
        return max(self.forms, key=len)

    def insert_as_first(self, form_to_insert_to: str) -> str:
        return self.insert_at(form_to_insert_to, 1)

    def insert_as_last(self, form_to_insert_to: str) -> str:
        return self.insert_at(form_to_insert_to, -1)

    def insert_at(self, form_to_insert_to: str, at: int) -> str:
        if at < 0:
            return self._inverse_problem(FormPotential.insert_at, form_to_insert_to, at)
        place = at - 1
        concat = self._concat_op(place)
        scores = {}
        for form in self.forms:
            concated = concat(form_to_insert_to, form)
            true_form = self.get_form_at(concated, at)
            scores[form] = (len(true_form) - len(form)), len(form), concated
        ordered = sorted(scores, key=lambda form: scores[form][1], reverse=True)
        ordered = sorted(ordered, key=lambda form: scores[form][0], reverse=True)
        return scores[ordered[0]][2]

    def remove_at(self, form_to_remove_from: str, at: int) -> str:
        if at < 0:
            return self._inverse_problem(FormPotential.remove_at, form_to_remove_from, at)
        place = at-1
        to_remove = self.get_form_at(form_to_remove_from, at)
        return form_to_remove_from[:place] + form_to_remove_from[place:].replace(to_remove, '')

    def is_at(self, form_to_check: str, at: int):
        return self.get_form_at(form_to_check, at) != ''

    def get_form_at(self, form_to_check: str, at: int) -> str:
        if not at:
            raise ValueError
        if at < 0:
            return self._inverse_problem(FormPotential.get_form_at, form_to_check, at)
        place = at - 1
        placements = ((form, form_to_check.index(form) if form in form_to_check else None) for form in self.forms)
        existing = filter(lambda t: t[1] is not None, placements)
        corrects = filter(lambda t: t[1] == place, existing)
        increasing = sorted(corrects, key=lambda c: len(c[0]), reverse=True)
        return increasing[0][0] if increasing else ''

    def _inverse_problem(self, problem: Callable, form: str, at: int):
        reverse_result = problem(~self, form[::-1], -at)
        return reverse_result[::-1]

    def _concat_op(self, place: int) -> Callable[[str, str], str]:
        return lambda form_to_concat_to, concat_form: form_to_concat_to[:place] + concat_form + form_to_concat_to[place:]

    def _calculate_place(self, at: int) -> int:
        sign = at//abs(at)
        return sign*(abs(at) - 1)

    def __repr__(self) -> str:
        return repr(tuple(map(str, self.forms)))

    def __invert__(self) -> FormPotential:
        return FormPotential(*tuple(map(lambda s: s[::-1], self.forms)))

    def __or__(self, other: FormPotential | str) -> FormPotential:
        return FormPotential(self, other)

    def __add__(self, other: FormPotential | str) -> FormPotential:
        if isinstance(other, str):
            other = FormPotential(other)
        return FormPotential(*tuple(f1+f2 for f1, f2 in zip(self.forms, other.forms)))

    def __mul__(self, other: FormPotential | str) -> FormPotential:
        if isinstance(other, str):
            other = FormPotential(other)
        return FormPotential(*tuple(f1+f2 for f1, f2 in product(self.forms, other.forms)))

SameOrderLevel = tuple[list[Morpheme], list[Morpheme]]
Ordered = list[SameOrderLevel]

class Morpheme:

    def __init__(self, *contents: tuple[Morpheme | str, ...]):
        languages.associate(self)
        self._interpretation: list[tuple[list[Morpheme], list[Morpheme]]]
        # TODO: continue here
        # for content in contents:
        #     match content:
        #         case Morpheme():
        #             self._interpretation = content
        #         case str():
        #             self._interpretation = GrammarVisitor.interpret(content)
        #         case _:
        #             self._interpretation = NullMorpheme()

    def __call__(self, form: str):
        return self.apply_to(form)

    @abstractmethod
    def apply_to(self, form: str) -> str:
        return self._interpretation(form)

    @property
    def form(self) -> str:
        return self._interpretation.form

    def associate_to(self, lang: str | Language) -> Morpheme:
        languages[lang].associate(self)
        return self

    def __repr__(self) -> str:
        return self.form

    def __add__(self, morpheme: Morpheme) -> Morpheme:


# Affixes
# eme Affix():
# 	pass

class NullMorpheme(Morpheme):
    def __init__(self):
        super().__init__(self)

    def __call__(self, to_apply_to: str):
        return to_apply_to

    @property
    def form(self) -> str:
        return ''


class Affix(Morpheme, ABC):
    def __init__(self, content: str, operation_type: str = O.dot):
        super().__init__(self)
        self.content: FormPotential = FormPotential(content)
        self.kind: str = operation_type


class Adfix(Affix):
    _at: int = 0

    def apply_to(self, form: str, kind: str = None) -> str:
        kind = kind or self.kind
        match kind:
            case O.plus:  return self.content.insert_at(form, self._at)  # TODO last: how to economically use FormPotential?
            case O.minus: return self.content.remove_at(form, self._at)
            case O.dot:   return self.apply_to(form, O.minus if self.content.is_at(form, self._at) else O.plus)

    @property
    def form(self) -> str:
        return '|'.join(map(lambda bf: bf[:self._at] + self.kind + bf[self._at:], self.content.forms))


class Prefix(Adfix):
    _at = 1


class Postfix(Adfix):
    _at = -1


class Circumfix(Morpheme):
    def __init__(self, pre: str, post: str, kind: str = None):
        super().__init__(self)
        self._kind = kind
        self.prefix = Prefix(pre, kind)
        self.postfix = Postfix(post, kind)

    @property
    def kind(self) -> str:
        return self._kind

    @kind.setter
    def kind(self, kind: str):
        self.prefix.kind = kind
        self.postfix.kind = kind

    def apply_to(self, form: str, kind: str = None) -> str:
        kind = kind or self.kind
        for adfix in (self.prefix, self.postfix):
            form = adfix.apply_to(form, kind)
        return form

    @property
    def form(self) -> str:
        return self.prefix.content.max_form + self.kind + self.postfix.content.max_form


class Infix(Affix):  # tmesis
    pass


class Interfix(Affix):
    pass


# ?? Simulfix 	mouse → mice == ?
# ?? Suprafix  pro'duce vs 'produce  ?= vocalic

# end affixes


class Reduplication(Morpheme):
    pass


class Suppletion(Morpheme):
    pass


class Conversion(Morpheme):
    pass


# Vocalics
class Vocalic(Morpheme):  # Stress, Tone, Tonality, pitch-accent, etc.
    pass

# end vocalics


class Truncation(Morpheme):
    pass


class Blend(Morpheme):
    pass


class Abbreviation(Morpheme):
    pass


class Compound(Morpheme):
    pass


class Incorporation(Morpheme):
    pass


# Text


###########
# Grammar #
###########

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
    basic_cond              = not? ((alph_full pmd) / (pmd alph_full))
    
    segment                 = interfix / segment_single
    segment_single          = circumfix / prefix / postfix
    prefix                  = ((alph_full pmd) (prefix / postfix)?) 
    postfix                 = ((pmd alph_full) postfix?)
    circumfix               = alph_full pmd alph_full
    interfix                = (minus alph_full minus) / (plus alph_full plus) / (dot alph_full dot)

    alph_full               = (opt_expr alph_full?) / (alph_expr alph_full?) 
    opt_expr                = (alph opt) / (l alph_expr r opt)
    alph_expr               = ((l alph_expr r) alph_expr?) / alph+
    alph                    = ~r"[a-z]+"
    
    pmd                     = pm / dot
    pm                      = plus / minus
    plus                    = "+"
    minus                   = "-"
    dot                     = "."
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

    @classmethod
    def interpret(cls, form: str) -> Morpheme:
        return GrammarVisitor().parse(grammar.parse(form))

    def visit_main(self, node: Node, visited_children: list[Node]):
        context, ordered_expressions = visited_children
        # TODO: when implement context change none
        return {T.context: None, T.ordered_expressions: ordered_expressions}

    def visit_ordered_expressions(self, node: Node, visited_children):
        visited_children = list(clean_empty(visited_children))
        return

    def visit_same_order_whole(self, node: Node, visited_children):
        visited_children = list(clean_empty(visited_children))
        curr, *tail = visited_children
        curr = self._deparethesify(curr)
        if tail:
            curr += tail[0][1][0]
        return [curr] + tail  #self._visit_potentially_parenthesified_with_sep(visited_children, 2)

    def _visit_potentially_parenthesified_with_sep(self, to_process, depth=1):
        curr = reapply(lambda arr: arr[0], to_process, depth)
        extended = self._deparethesify(curr)
        if isinstance(to_process[1], list):
            extended.extend(to_process[1][0][1])
        return extended

    def _deparethesify(self, to_deparethesify):
        if not len(to_deparethesify):
            return to_deparethesify
        if (isinstance(to_deparethesify[0], str) and to_deparethesify[0] == O.l) or (isinstance(to_deparethesify[0], Node) and to_deparethesify[0].expr_name == T.l):
            return to_deparethesify[1]
        return to_deparethesify

    def visit_same_order_single(self, node: Node, visited_children):
        return visited_children[0]

    # Conditions


    def visit_cond_whole(self, node: Node, visited_children):
        return visited_children

    def visit_quasi_expr(self, node: Node, visited_children):
        return visited_children

    def visit_complex_cond(self, node: Node, visited_children):
        return visited_children

    def visit_basic_cond(self, node: Node, visited_children):
        not_, cond = visited_children
        minus, plus = visited_children
        return visited_children

    # Segments

    def visit_segment(self, node: Node, visited_children):
        return visited_children[0]

    def visit_segment_single(self, node: Node, visited_children):
        return visited_children[0]

    def visit_prefix(self, node: Node, visited_children):
        return visited_children
        #return self._visit_operations(node, T.prefix, visited_children)

    def visit_postfix(self, node: Node, visited_children):
        op, content = to_last_list(clean_empty(visited_children))
        return Postfix(content, op)

    def visit_interfix(self, node: Node, visited_children: list[Node]):
        op1, inter, op2 = self._to_text(node.children[0].children)
        op = op1 if op1 == op2 else None
        return [{T.operation: T.interfix, T.operation_type: op, T.operands: [inter]}]

    def visit_circumfix(self, node: Node, visited_children):
        pre, op, post = visited_children
        return

    # eme _visit_operations(self, node: Node, operation: str, visited_children):
    #     curr = {T.operation: operation, **self._get_operation_expression_tuple(node)}
    #     first, others = visited_children
    #     other = [] if not isinstance(others, list) else others[0]
    #     return [curr] + other
    #
    # eme _get_operation_expression_tuple(self, node: Node) -> dict[str, str]:
    #     children = node.children[0].children
    #     expressions = list(filter(lambda s: s.isalnum(), map(self._to_text, children)))
    #     operation_type = next(filter(lambda n: not n.text.isalnum(), children)).text
    #     return {T.operation_type: operation_type, T.operands: expressions}
    #
    # eme _to_text(self, to_change: Node | Iterable[Node]) -> str | tuple[str, ...]:
    #     return to_change.text if isinstance(to_change, Node) else tuple(filter(self._to_text, to_change))

    # Basics
    def visit_alph_full(self, node: Node, visited_children):
        form_potentials = filter(lambda e: isinstance(e, FormPotential), visited_children[0])
        return reduce(op.mul, form_potentials)

    def visit_opt_expr(self, node: Node, visited_children):
        if node.text.count(O.opt) != 1:
            raise ValueError
        return FormPotential(node.text.removesuffix(O.opt)) | ''

    def visit_alph_expr(self, node: Node, visited_children):
        expr = FormPotential('')
        visited_children = to_last_list(visited_children)
        for child in visited_children:
            child = to_last_list(child)
            child = child[1] if isinstance(child, list) else child
            expr += child
        return FormPotential(expr)

    def generic_visit(self, node: Node, visited_children):
        """ The generic visit method. """
        if visited_children:
            existing = filter(bool, visited_children)
            mapped = list(map(self.generic_func, existing))
            return mapped[0] if len(mapped) == 1 else mapped
        return node

    def generic_func(self, to_map):
        match to_map:
            case Node():                   return to_map.text
            case str() | FormPotential():  return to_map
            case _:                        return to_map


#((alph+ opt)? alph_full) /
# text = '-an+ta'
# tree = grammar.parse(text)
# if should_print := 0:
#     print('tree text:', tree.text)
#     print('tree expr:', tree.expr)
#     alph_full = tree.children[1].children[0].children[0].children[0].children[0]#.children[1]
#     print('alph expr text:', alph_full.text)
#     print('alph expr expr:', alph_full.expr_name)
#     print('alph expr children:')
#     for child in alph_full.children:
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
#     t_cond                    = (t_alph_full t_minus) / (t_minus t_alph_full)
#
#     t_single_expr             = (t_alph_full t_pm) / (t_pm t_alph_full)
#     t_alph_full               = t_alph+
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


if work_with_graph := True:
    v = GrammarVisitor()
    #-p-c
    parsed = grammar.parse('(-u),(+t);r-,g+')#'~-u?-u:+u,-u?-u:+u')  # '-p+f,a+;j+a,+s'  # '(-p+f),a+;j+a,(+s)'
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

if test_pot_form := False:
    fp = FormPotential('est', 'st', 't')
    for form in ('mach', 'mache', 'maches', 'sat', 'sast'):
       new_form = fp.insert_at(form, -1)
       old_form = fp.remove_at(new_form, -1)
       print(f'{new_form} was created from {form} and came back to {old_form}')
       print(f'Removed from original {form} to {fp.remove_at(form, -1)}')


class Reduplication(Morpheme):
    pass


class Suppletion(Morpheme):
    pass


class Conversion(Morpheme):
    pass


# Vocalics
class Vocalic(Morpheme):  # Stress, Tone, Tonality, pitch-accent, etc.
    pass

# end vocalics


class Truncation(Morpheme):
    pass


class Blend(Morpheme):
    pass


class Abbreviation(Morpheme):
    pass


class Compound(Morpheme):
    pass


class Incorporation(Morpheme):
    pass


# Text


###########
# Grammar #
###########

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
    basic_cond              = not? ((alph_full pmd) / (pmd alph_full))
    
    segment                 = interfix / segment_single
    segment_single          = circumfix / prefix / postfix
    prefix                  = ((alph_full pmd) (prefix / postfix)?) 
    postfix                 = ((pmd alph_full) postfix?)
    circumfix               = alph_full pmd alph_full
    interfix                = (minus alph_full minus) / (plus alph_full plus) / (dot alph_full dot)

    alph_full               = (opt_expr alph_full?) / (alph_expr alph_full?) 
    opt_expr                = (alph opt) / (l alph_expr r opt)
    alph_expr               = ((l alph_expr r) alph_expr?) / alph+
    alph                    = ~r"[a-z]+"
    
    pmd                     = pm / dot
    pm                      = plus / minus
    plus                    = "+"
    minus                   = "-"
    dot                     = "."
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

    @classmethod
    def interpret(cls, form: str) -> Morpheme:
        return GrammarVisitor().parse(grammar.parse(form))

    def visit_main(self, node: Node, visited_children: list[Node]):
        context, ordered_expressions = visited_children
        # TODO: when implement context change none
        return {T.context: None, T.ordered_expressions: ordered_expressions}

    def visit_ordered_expressions(self, node: Node, visited_children):
        visited_children = list(clean_empty(visited_children))
        return

    def visit_same_order_whole(self, node: Node, visited_children):
        visited_children = list(clean_empty(visited_children))
        curr, *tail = visited_children
        curr = self._deparethesify(curr)
        if tail:
            curr += tail[0][1][0]
        return [curr] + tail  #self._visit_potentially_parenthesified_with_sep(visited_children, 2)

    def _visit_potentially_parenthesified_with_sep(self, to_process, depth=1):
        curr = reapply(lambda arr: arr[0], to_process, depth)
        extended = self._deparethesify(curr)
        if isinstance(to_process[1], list):
            extended.extend(to_process[1][0][1])
        return extended

    def _deparethesify(self, to_deparethesify):
        if not len(to_deparethesify):
            return to_deparethesify
        if (isinstance(to_deparethesify[0], str) and to_deparethesify[0] == O.l) or (isinstance(to_deparethesify[0], Node) and to_deparethesify[0].expr_name == T.l):
            return to_deparethesify[1]
        return to_deparethesify

    def visit_same_order_single(self, node: Node, visited_children):
        return visited_children[0]

    # Conditions


    def visit_cond_whole(self, node: Node, visited_children):
        return visited_children

    def visit_quasi_expr(self, node: Node, visited_children):
        return visited_children

    def visit_complex_cond(self, node: Node, visited_children):
        return visited_children

    def visit_basic_cond(self, node: Node, visited_children):
        not_, cond = visited_children
        minus, plus = visited_children
        return visited_children

    # Segments

    def visit_segment(self, node: Node, visited_children):
        return visited_children[0]

    def visit_segment_single(self, node: Node, visited_children):
        return visited_children[0]

    def visit_prefix(self, node: Node, visited_children):
        return visited_children
        #return self._visit_operations(node, T.prefix, visited_children)

    def visit_postfix(self, node: Node, visited_children):
        op, content = to_last_list(clean_empty(visited_children))
        return Postfix(content, op)

    def visit_interfix(self, node: Node, visited_children: list[Node]):
        op1, inter, op2 = self._to_text(node.children[0].children)
        op = op1 if op1 == op2 else None
        return [{T.operation: T.interfix, T.operation_type: op, T.operands: [inter]}]

    def visit_circumfix(self, node: Node, visited_children):
        pre, op, post = visited_children
        return

    # eme _visit_operations(self, node: Node, operation: str, visited_children):
    #     curr = {T.operation: operation, **self._get_operation_expression_tuple(node)}
    #     first, others = visited_children
    #     other = [] if not isinstance(others, list) else others[0]
    #     return [curr] + other
    #
    # eme _get_operation_expression_tuple(self, node: Node) -> dict[str, str]:
    #     children = node.children[0].children
    #     expressions = list(filter(lambda s: s.isalnum(), map(self._to_text, children)))
    #     operation_type = next(filter(lambda n: not n.text.isalnum(), children)).text
    #     return {T.operation_type: operation_type, T.operands: expressions}
    #
    # eme _to_text(self, to_change: Node | Iterable[Node]) -> str | tuple[str, ...]:
    #     return to_change.text if isinstance(to_change, Node) else tuple(filter(self._to_text, to_change))

    # Basics
    def visit_alph_full(self, node: Node, visited_children):
        form_potentials = filter(lambda e: isinstance(e, FormPotential), visited_children[0])
        return reduce(op.mul, form_potentials)

    def visit_opt_expr(self, node: Node, visited_children):
        if node.text.count(O.opt) != 1:
            raise ValueError
        return FormPotential(node.text.removesuffix(O.opt)) | ''

    def visit_alph_expr(self, node: Node, visited_children):
        expr = FormPotential('')
        visited_children = to_last_list(visited_children)
        for child in visited_children:
            child = to_last_list(child)
            child = child[1] if isinstance(child, list) else child
            expr += child
        return FormPotential(expr)

    def generic_visit(self, node: Node, visited_children):
        """ The generic visit method. """
        if visited_children:
            existing = filter(bool, visited_children)
            mapped = list(map(self.generic_func, existing))
            return mapped[0] if len(mapped) == 1 else mapped
        return node

    def generic_func(self, to_map):
        match to_map:
            case Node():                   return to_map.text
            case str() | FormPotential():  return to_map
            case _:                        return to_map


#((alph+ opt)? alph_full) /
# text = '-an+ta'
# tree = grammar.parse(text)
# if should_print := 0:
#     print('tree text:', tree.text)
#     print('tree expr:', tree.expr)
#     alph_full = tree.children[1].children[0].children[0].children[0].children[0]#.children[1]
#     print('alph expr text:', alph_full.text)
#     print('alph expr expr:', alph_full.expr_name)
#     print('alph expr children:')
#     for child in alph_full.children:
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
#     t_cond                    = (t_alph_full t_minus) / (t_minus t_alph_full)
#
#     t_single_expr             = (t_alph_full t_pm) / (t_pm t_alph_full)
#     t_alph_full               = t_alph+
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


if work_with_graph := True:
    v = GrammarVisitor()
    #-p-c
    parsed = grammar.parse('(-u),(+t);r-,g+')#'~-u?-u:+u,-u?-u:+u')  # '-p+f,a+;j+a,+s'  # '(-p+f),a+;j+a,(+s)'
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

if test_pot_form := False:
    fp = FormPotential('est', 'st', 't')
    for form in ('mach', 'mache', 'maches', 'sat', 'sast'):
       new_form = fp.insert_at(form, -1)
       old_form = fp.remove_at(new_form, -1)
       print(f'{new_form} was created from {form} and came back to {old_form}')
       print(f'Removed from original {form} to {fp.remove_at(form, -1)}')
