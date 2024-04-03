from __future__ import annotations

from abc import ABC
from itertools import starmap
from typing import Optional, List, AnyStr, Iterable, Dict, Tuple, Any

from more_itertools import side_effect, consume
from pydantic import BaseModel, field_validator, model_validator
from toolz import curry

import src.utils as utils
from src.constants import SimpleTerms
from src.lang_typing import Config, Kind, Resolution, UnitConf
from src.language_components import Unit, Feature, Language

# TODO: Decision: do the I and potentially extend for the III one later and maybe with a flag
# see: https://github.com/ProxPxD/Langcode/issues/7

ID = AnyStr


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


class FeatureSchema(BaseModel):
    type: Optional[Resolution] = None
    elems: List[FeatureSchema | AnyStr] | Dict[AnyStr, FeatureSchema] | Dict[AnyStr, AnyStr] = None  # TODO: name such type(s)

    @field_validator('elems')
    def create_features(cls, elems) -> List[Tuple[Feature, Dict]]:
        normalized = utils.map_conf_list_to_dict(elems)
        features = [(Feature(name=name, kind=None), conf) for name, conf in normalized.items()]
        return features

    @model_validator(mode='after')
    def set_children_and_type(cls, values):
        features: List[Tuple[Feature, Dict]] = values.get(SimpleTerms.ELEMS)
        for feature, conf in features:
            if elems := conf.get(SimpleTerms.ELEMS):
                children, children_conf = tuple(zip(*elems))
                default_feature_type = SimpleTerms.DISJOINT if utils.is_all_dict_of_none(children_conf) else SimpleTerms.JOINT
                feature.type = conf.get(SimpleTerms.TYPE, default_feature_type)
                consume(side_effect(feature.children.manager.connect, children))
        return values


class FeaturesSchema(BaseModel):
    graphemes: FeatureSchema
    morphemes: FeatureSchema

    @classmethod
    def set_kind(cls, phemes: list[Feature], kind: Kind) -> List[Feature]:
        utils.apply_to_tree(
            phemes,
            lambda curr: setattr(curr, 'kind', kind),
            lambda curr: curr.children,
        )
        return phemes

    @field_validator('graphemes')
    def val_graphemes(cls, graphemes):
        return cls.set_kind(graphemes, SimpleTerms.GRAPHEME)

    @field_validator('morphemes')
    def val_morphemes(cls, morphemes):
        return cls.set_kind(morphemes, SimpleTerms.MORPHEME)


class LanguageSchema(BaseModel):  # TODO: think if morphemes shouldn't be required
    general: Optional[Any] = None
    morphemes: Optional[MorphemesSchema] = None
    graphemes: Optional[GraphemesSchema] = None
    rules: Optional[RulesSchema] = None
    features: Optional[FeaturesSchema] = None

    @classmethod
    def to_lang(cls) -> Language:
        raise NotImplementedError
