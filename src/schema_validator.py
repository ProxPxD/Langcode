from __future__ import annotations

from abc import ABC
from itertools import starmap
from typing import Optional, List, AnyStr, Iterable, Dict, Tuple

from more_itertools import side_effect, consume
from pydantic import BaseModel, field_validator, model_validator
from toolz import curry

import utils
from src.constants import SimpleTerms
from src.lang_typing import Config, Kind, Resolution, UnitConf
from src.language_components import Unit, Feature

# TODO: Decision: do the I and potentially extend for the III one later and maybe with a flag
# see: https://github.com/ProxPxD/Langcode/issues/7

ID = AnyStr


@curry
def config_to_unit(kind: str, name: str, config: Config):
    return Unit(name=name, kind=kind, features=config)


class GeneralSchema(BaseModel):
    pass


class MorphemeSpecificationSchema(BaseModel):
    pass


class MorphemesFeaturesSchema(BaseModel):
    pass


class UnitSchema(BaseModel, ABC):
    @classmethod
    def map_unit_conf_to_units(cls, elems: UnitConf, kind: Kind) -> Iterable[Unit]:
        normalized = utils.map_conf_list_to_dict(elems)
        unit_elems = dict(starmap(cls.create_unit(kind), normalized.items()))  # TODO: think if initial structure of morpheme config is not required such as checking if features exist
        return unit_elems

    @classmethod
    @curry
    def create_unit(cls, kind: Kind, name: str, conf: dict) -> Unit:
        # TODO: Connect to features
        unit = Unit(name=name, kind=kind)
        unit.load_conf(conf)
        return unit


class MorphemesSchema(UnitSchema):
    elems: Optional[UnitConf]
    features: Optional[MorphemesFeaturesSchema]

    @field_validator('elems')  # TODO: think of validating it deeper
    def val_elems(self, elems) -> Iterable[Unit]:
        return self.map_unit_conf_to_units(elems, SimpleTerms.MORPHEME)


class RulesSchema(BaseModel):
    pass


class FeatureSchema(BaseModel):
    type: Optional[Resolution]
    elems: List[FeatureSchema | AnyStr] | Dict[AnyStr, FeatureSchema] | Dict[AnyStr, AnyStr]  # TODO: name such type(s)

    @field_validator('elems')
    def create_features(self, elems) -> List[Tuple[Feature, Dict]]:
        normalized = utils.map_conf_list_to_dict(elems)
        features = [(Feature(name=name, kind=None), conf) for name, conf in normalized.items()]
        return features

    @model_validator(mode='after')
    def set_children_and_type(self, values):
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
    def val_graphemes(self, graphemes):
        return self.set_kind(graphemes, SimpleTerms.GRAPHEME)

    @field_validator('morphemes')
    def val_morphemes(self, morphemes):
        return self.set_kind(morphemes, SimpleTerms.MORPHEME)


class LanguageSchema(BaseModel):  # TODO: think if morphemes shouldn't be required
    general: Optional[GeneralSchema]
    morphemes: Optional[MorphemesSchema]
    rules: Optional[RulesSchema]
    features: Optional[FeaturesSchema]
