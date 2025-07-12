from collections import namedtuple

from testing.core import TCG


class ResolutionTCG(TCG):
    c = namedtuple('check', 'obj key val')
    tc = namedtuple('tc', 'name conf checks', defaults=[[], None])
    tcs = [
        tc(
            name='Trivial',
            conf=' - ',  # TODO: How to check?
        ),
        tc(
            name='LCID only',
            conf='lcid_structive:',
            checks=(c('lcid_structive', 'lcid', 'lcid_structive'),)
        ),
        tc(
            name='is defined in child',
            conf='''
            parent:
            child:
                is: parent
            ''',
            checks=(c('parent', 'ex', ''), c('child', 'is', ''))
        ),
        tc(
            name='ex defined in parent',
            conf='''
            child:
            parent:
                ex: child
            '''
        ),
    ]


@ResolutionTCG.parametrize('name, tc')
def test(name, tc):
    raise NotImplementedError