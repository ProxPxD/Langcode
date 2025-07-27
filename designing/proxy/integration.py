from prompt_toolkit.widgets import Box

from designing.proxy.category import Category

alphabet = 'abc'
alphacats = Box({letter: Category(unicode=letter) for letter in alphabet})

digraphs = ['ch', 'zh', 'sh']
digraphcats = Box({digraph: Category(unicode=digraph) for digraph in digraphs})


grapheme = Category()
grapheme_cats = Box({
    'a':  grapheme.ex_(unicode='a', name='a'),
    'b':  grapheme.ex_(unicode='b', name='be'),
    'c':  grapheme.ex_(unicode='c', name='ce'),
    'h':  grapheme.ex_(unicode='h', name='ha')
})