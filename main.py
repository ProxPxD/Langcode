from itertools import product

from langcode import languages, Language, Morpheme

esp = Language('Spanish')

print(languages['Spanish'])


'''
interfix  := (W1-a?-),W1+o+W2     						# myśl, zbrodnia -> myślozbrodnia
interfix  := (W1-a?-),+o+         						#

> - later cond
, - cond at the beginning

C, V, W - consonants, vowels, words

inf    := +e^n
inf_1  := +en  -- is inf
inf_2  := +Cn  -- is inf
inf  := inf_1 | inf_2

think:
comp   :=  '-V1CC*~' + umlaut['V1'] + '?umlaut(V1)+er' # groß -> größer
comp   :=  '-V1CC*~' + umlaut + '(V1)?umlaut(V1)+er'   # groß -> größer

'''