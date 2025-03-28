from __future__ import annotations

from itertools import repeat
from typing import Any, Tuple, List, Sequence

from numpy.distutils.system_info import agg2_info

from src.neomodel_utitilities import Neo4jQuerer
from src.structive.ogm import StructiveOGM
from src.utils import is_all_instance_of_dict

import pydash as _
from pydash import chain as c


class StructiveDAO:
    def __init__(self, *args, __is_forming: bool = False, **kwargs):
        match len(args), len(kwargs):
            case 1, 0: ogm = args[0]
            case 0, _: ogm = StructiveOGM(*args, **kwargs)
            case _: raise ValueError('Arguments can be either an OGM or kwargs')
        self._ogm: StructiveOGM = ogm
        self.__is_forming: bool = __is_forming

    def prop(self, **kwargs) -> StructiveDAO:
        self._ogm._data.update(kwargs)
        return self.form()

    def form(self) -> StructiveDAO:
        self.__is_forming = False
        return self

    @classmethod
    def ensure_dao(cls, obj: Any) -> StructiveDAO:
        match obj:
            case StructiveDAO(): return obj
            case StructiveOGM(): return StructiveDAO(obj)
            case dict(): return StructiveDAO(**obj)
            case _: raise NotImplementedError(f'Unpredicted Value: {obj}')

    # @classmethod
    # def get(cls, *props: dict[str, Any]):
    #     if not props:
    #         raise ValueError('Cannot get by no props')
    #     # TODO: make Neo4jQuerer.query accept all nodes
    #     query_nodes = zip(repeat('StructiveOGM'), props)
    #     ogms = map(lambda node: Neo4jQuerer.query(node, unique=True, single=True), query_nodes)
    #     daos = _.map(ogms, cls.ensure_dao)
    #     got = daos[0] if len(props) == 1 else daos
    #     return got

    def __getitem__(self, item: str) -> Any:
        return self.__props[item]

    def __getattr__(self, item: str) -> Any:
        return self[item]

    def is_(self, *structives: StructiveDAO) -> StructiveDAO:
        for structive in structives:
            self._ogm.is_.connect(structive._ogm)
        return self

    def ex(self, *structives: StructiveDAO | dict[str, Any], **dicted_structive) -> Sequence[StructiveDAO]:
        match bool(structives), bool(dicted_structive):
            case False, False: raise ValueError('Cannot create a relation to none')
            case False, True: structives = [dicted_structive]
            case True, True if _.every(structives, _.is_dict):
                structives = _.map(structives, c().assign(dicted_structive))
            case True, True: raise ValueError('Cannot assign properties to existing structives!')

        structives: List[StructiveDAO] = _.map(structives, self.ensure_dao)
        for structive in structives:
            structive.is_(self)
        return structives

    def __and__(self, other: StructiveDAO):
        if isinstance(other, StructiveDAO):
            raise ValueError('Conjuncted object has to be a DAO')
        match self.__is_forming:
            case False: return StructiveDAO(__is_forming=True).is_(self, other)
            case True: return self.is_(other)


S = StructiveDAO

################

manner = S(name='manner')
place = S(name='place')

manners = manner.ex(
    dict(name='nasal'),
    dict(name='plosive'),
)
places = place.ex(
    dict(name='labial'),
    dict(name='coronal'),
)

nasal, plosive = manners
labial, coronal = places

# Subplaces
labials = labial.ex(
    dict(name='bilabial'),
    dict(name='labiodental'),
)
coronals = coronal.ex(
    dict(name='alveolar'),
)
bilabial, labiodental = labials
alveolar, = coronals

labial_nasal = S(name='labial_nasal').is_(bilabial, nasal)
alveolar_nasal = (alveolar and nasal).prop(name='alveolar_nasal')
