from __future__ import annotations

import operator as op
from abc import ABC
from functools import reduce
from itertools import starmap
from typing import Optional, List, AnyStr, Iterable, Dict, Tuple, Any

from more_itertools import side_effect, consume
from pydantic import BaseModel, field_validator, model_validator, Extra
from toolz import curry, keyfilter

import src.utils as utils
from src.constants import SimpleTerms
from src.exceptions import ConflictingKeysException
from src.lang_typing import Config, Kind, Resolution, UnitConf
from src.language_components import Unit, Feature, Language


# TODO: Decision: do the I and potentially extend for the III one later and maybe with a flag
# see: https://github.com/ProxPxD/Langcode/issues/7


@curry
def config_to_unit(kind: str, name: str, config: Config):
    return Unit(name=name, kind=kind, features=config)


class MorphemeSpecificationSchema(BaseModel):
    pass


class MorphemesFeaturesSchema(BaseModel):
    pass


class UnitSchema(BaseModel, ABC):
    @classmethod
    def map_unit_conf_to_units(cls, elems: UnitConf, kind: Kind) -> Iterable[Unit]:
        normalized = utils.map_conf_list_to_dict(elems)
        unit_elems = list(starmap(cls.create_unit(kind), normalized.items()))  # TODO: think if initial structure of morpheme config is not required such as checking if features exist
        return unit_elems

    @classmethod
    @curry
    def create_unit(cls, kind: Kind, name: str, conf: dict) -> Unit:
        # TODO: Connect to features
        unit = Unit(name=name, kind=kind)
        unit.load_conf(conf)
        return unit


class MorphemesSchema(UnitSchema):
    elems: Optional[UnitConf] = None
    features: Optional[MorphemesFeaturesSchema] = None

    @field_validator('elems')
    def val_elems(cls, elems) -> Iterable[Unit]:
        return cls.map_unit_conf_to_units(elems, SimpleTerms.MORPHEME)


class GraphemesSchema(UnitSchema):
    elems: Optional[UnitConf] = None
    features: Optional[MorphemesFeaturesSchema] = None

    @field_validator('elems')
    def val_elems(cls, elems) -> Iterable[Unit]:
        return cls.map_unit_conf_to_units(elems, SimpleTerms.GRAPHEME)


class RulesSchema(BaseModel):
    pass


# ListConfigFeature = List[FeatureSchema | AnyStr]
# DictConfigFeature = Dict[AnyStr, FeatureSchema] | Dict[AnyStr, AnyStr]
# ConfigFeature = ListConfigFeature | DictConfigFeature


class FeatureSchema(BaseModel):
    type: Optional[Resolution] = None
    elems: Optional[List[FeatureSchema | AnyStr] | Dict[AnyStr, FeatureSchema] | Dict[AnyStr, AnyStr | List[AnyStr | FeatureSchema]]] = None  # TODO: name such type(s)
    # __data: Optional[Dict[str, Any]] = PrivateAttr({})

    class Config:
        extra = Extra.allow

    def __init__(self, **data):
        super().__init__(**self.normalize_feature_schema(data))

    @classmethod
    def normalize_feature_schema(cls, data: dict) -> dict:
        allowed_keys = (SimpleTerms.ELEMS, SimpleTerms.TYPE)
        direct_definitions = keyfilter(lambda key: key not in allowed_keys, data)

        if direct_definitions and SimpleTerms.ELEMS in data:
            raise ConflictingKeysException(direct_definitions)

        data[SimpleTerms.ELEMS] = reduce(op.or_, map(utils.map_conf_list_to_dict, (direct_definitions, data.get(SimpleTerms.ELEMS, []))))
        data = keyfilter(allowed_keys.__contains__, data)
        return data

    @classmethod
    @field_validator('elems')
    def create_features(cls, elems) -> List[Tuple[Feature, Dict]]:
        features = [(Feature(name=name, kind=None), conf) for name, conf in elems.items()]
        return features

    @classmethod
    @model_validator(mode='after')
    def set_children_and_type(cls, values):
        features: List[Tuple[Feature, Dict]] = values.elems or []
        for feature, conf in features:
            if elems := conf.get(SimpleTerms.ELEMS):
                children, children_conf = tuple(zip(*elems))
                default_feature_type = SimpleTerms.DISJOINT if utils.is_all_dict_of_none(children_conf) else SimpleTerms.JOINT
                feature.type = conf.get(SimpleTerms.TYPE, default_feature_type)
                consume(side_effect(feature.children.manager.connect, children))
        return values


class FeaturesSchema(BaseModel):
    graphemes: Optional[FeatureSchema] = None
    morphemes: Optional[FeatureSchema] = None

    @classmethod
    def set_kind(cls, phemes: list[Feature], kind: Kind) -> List[Feature]:
        utils.apply_to_tree(
            phemes or [],
            lambda curr: setattr(curr, 'kind', kind),
            lambda curr: curr.children,
        )
        return phemes

    @classmethod
    @field_validator('graphemes')
    def val_graphemes(cls, graphemes):
        return cls.set_kind(graphemes.elems, SimpleTerms.GRAPHEME)

    @classmethod
    @field_validator('morphemes')
    def val_morphemes(cls, morphemes):
        return cls.set_kind(morphemes.elems, SimpleTerms.MORPHEME)


class LanguageSchema(BaseModel):  # TODO: think if morphemes shouldn't be required
    general: Optional[Any] = None
    morphemes: Optional[MorphemesSchema] = None
    graphemes: Optional[GraphemesSchema] = None
    rules: Optional[RulesSchema] = None
    features: Optional[FeaturesSchema] = None

    @classmethod
    def to_lang(cls) -> Language:
        raise NotImplementedError
