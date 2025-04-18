import pandas as pd
import operator as op
from pandas import Series, DataFrame

c: Series = Series(['c'])
h: Series = Series(['h'])
a: Series = Series(['a'])


ch_graphemes: Series = pd.Series.combine(c, h, op.add)
ch_chars: Series = pd.concat([c, h])

print(ch_graphemes)
print(ch_chars)
print('-'*42)

cha_graphemes: Series = pd.concat([ch_graphemes, a])
cha_chars_from_chars: Series = pd.concat([c, h, a])
cha_chars_from_graphemes: Series = Series([g for gs in cha_graphemes for g in gs])


print(cha_graphemes)
print(cha_chars_from_chars)
print(cha_chars_from_graphemes)
print('-'*42)


class Arrow:
    ...

# concat = Arrow(when=True, then=lambda *args: args)
#
# concat = Arrow(lambda a, b: list(a) + list(b))  # Both lists and strings
