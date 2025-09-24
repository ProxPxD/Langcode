from collections import namedtuple

from testing.core.TCG import TCG


class ConfNormTCG(TCG):
    tc = namedtuple('tc', ['name', 'descr', 'unnormeds', 'normed'])

    id = 'id'
    src = 'src'
    obj = 'obj'
    trg = 'trg'

    be = 'be'
    ex = 'ex'

    tcs = [
        tc(
            name='',
            descr='',
            unnormeds=[],
            normed=None,
        ),
        tc(
            name='ID',
            descr='',
            unnormeds=[
                {
                    'name': 'hidden',
                    '_dog': {
                        id: 'dog',
                    }
                },
                {
                    'name': 'key',
                    'dog': None
                }
            ],
            normed={
                id: 'dog',
            },
        ),
        tc(
            name='',
            descr='',
            unnormeds=[],
            normed=None,
        ),
        tc(
            name='',
            descr='',
            unnormeds=[
                {
                    'manner': {
                        ex: ['nasal', 'plosive'],
                    }
                },
                {
                    'manner': {
                        ex: {'nasal': None, 'plosive': None},
                    }
                }
            ],
            normed=[
                {
                    id: 'manner',
                    obj: {
                        ...
                    },
                }
            ],
        )
    ]


ConfNormTCG.parametrize('name', 'tc')
def test(name, tc):
    raise NotImplementedError