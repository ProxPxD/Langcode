from dataclasses import dataclass

from src.logic.blocks.node import N
from testing.core import TCG


@dataclass
class TC:
    descr: str


@dataclass
class Tc:
    ...



class InnerLogicTCG(TCG):
    tcs = [
        TC('---'),
    ]


@InnerLogicTCG.parametrize('tc')
def test(tc: Tc | TC):
    struct_kind = N(name='Struct')
    param_feature_kind = N(name='ParamFeature')
    struct_feature_kind = N(name='StructFeature')

    param_feature = N(name='param_feature', be=param_feature_kind)
    struct_feature = N(name='struct_feature', be=struct_feature_kind)

    main_param = N(name='main_param', name_='main_param', be=param_feature)
    second_param = N(name='second_param', name_='second_param', default='s')
    
    source = N(name='source', param=(main_param, second_param))
    target = N(name='target')
    struct = N(name='struct', be=(struct_kind, struct_feature), src=source, trg=target)
