from collections.abc import Sequence

import pydash as _
from pydash import chain as c

from src.logic.conf.types import YamlType, SimpleYamlType

ALT_KWS = (
    # Top level
    GENERAL_ALTS := (GENERAL := 'general',),
    INGRAINS_ALTS := (INGRAINS := 'ingrains',),
    STRUCTANTS_ALTS := (STRUCTANTS := 'structants',),
    # Structants
    STRUCTANT_ALTS := (STRUCTANT := 'structant',),
    SOURCE_ALTS := (SOURCE := 'source', 'src'),
    OBJECT_ALTS := (OBJECT := 'object', 'obj'),
    TARGET_ALTS := (TARGET := 'target', 'trg'),
    DEFINE_ALTS := (DEFINE := 'define', 'def'),
    ID_ALTS := (ID := 'id',),
    UID_ALTS := (UID := 'uid',),
    NONE_ID_PREFIX_ALTS := (NONE_ID_PREFIX := '_', ),
    ALIASES_ALTS := (ALIASES := 'aliases', 'alias'),
    IS_ALTS := (IS := 'is',),
    EX_ALTS := (EX := 'ex',),

)


NORM_BLOCKERS = (ALIASES_ALTS,)

STRUCTANT_KWS = (UID, SOURCE, OBJECT, TARGET, DEFINE, ALIASES)


def get_norm_group(key: str) -> Sequence[str]:
    return c(ALT_KWS).filter(c().includes(key)).get(0, (key,)).value()


def is_norm_stopper(key: str) -> bool:
    return get_norm_group(key) in NORM_BLOCKERS


def norm_key(key: str) -> str:
    return get_norm_group(key)[0]


def normize_keywords(data: YamlType) -> YamlType:
    match data:
        case simple if isinstance(simple, SimpleYamlType): return data
        case list(): return _.map_(data, normize_keywords)
        case dict(): return {norm_key(key): (_.identity, normize_keywords)[is_norm_stopper(key)](val) for key, val in data.items()}
        case _: raise ValueError(f'Unsupported type for normalization: {type(data)}')
