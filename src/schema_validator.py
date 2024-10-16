from __future__ import annotations

import operator as op
from abc import ABC
from functools import reduce
from typing import Optional, List, AnyStr, Iterable, Dict, Tuple, Any

import pydash as _
from pydantic import BaseModel, field_validator, model_validator
from pydash import chain as c
from toolz import keyfilter

import src.utils as utils
from src.constants import ST
from src.exceptions import ConflictingKeysException
from src.lang_typing import Kind, Resolution, ElemsConf, ComplexYamlType, FeatureConf, YamlType
from src.language_components import Unit, Feature, Language
from src.utils import is_list


# TODO: Decision: do the I and potentially extend for the III one later and maybe with a flag
# see: https://github.com/ProxPxD/Langcode/issues/7


class IToDict(BaseModel):
    @model_validator(mode='after')
    @classmethod
    def to_dict(cls, schema: BaseModel) -> dict:
        return schema.model_dump()


class UnitFeaturesSchema(IToDict, BaseModel):
    class Config:
        extra = 'allow'

    @model_validator(mode='before')
    @classmethod
    def flatten(cls, values: ComplexYamlType):
        return utils.merge_to_flat_dict(values)


class UnitSchema(IToDict, BaseModel, ABC):
    elems: Optional[ElemsConf] = None
    features: Optional[UnitFeaturesSchema | FeatureConf] = None

    @field_validator('elems')
    @classmethod
    def val_elems(cls, elems) -> Iterable[Unit]:
        normalized = utils.map_conf_list_to_dict(elems)
        units = [Unit(name=name, conf=conf) for name, conf in normalized.items()]  # TODO: think if initial structure of morpheme config is not required such as checking if features exist
        return units


class RulesSchema(BaseModel):
    pass


class FeatureSchema(BaseModel):
    type: Optional[Resolution] = None
    elems: Optional[
        None
        | List[AnyStr]
        | Dict[AnyStr, None]
        | List[FeatureSchema]
        | Dict[AnyStr, FeatureSchema]
        | Dict[AnyStr, List[Any] | Dict[AnyStr, AnyStr]]
    ] = None

    @classmethod
    def normalize_feature_schema(cls, data: dict | list) -> dict:
        allowed_keys = (ST.ELEMS, ST.TYPE)
        direct_definitions = keyfilter(lambda key: key not in allowed_keys, data)

        if direct_definitions and ST.ELEMS in data:
            raise ConflictingKeysException(direct_definitions)

        data = keyfilter(allowed_keys.__contains__, data)
        data[ST.ELEMS] = reduce(op.or_, map(utils.map_conf_list_to_dict, (direct_definitions, data.get(ST.ELEMS, []))))
        return data

    @model_validator(mode='before')
    @classmethod
    def normalize_schema(cls, values):
        values = utils.map_conf_list_to_dict(values)  # if is_list(values) or values is None else values
        return cls.normalize_feature_schema(values)

    @field_validator('elems')
    @classmethod
    def create_features(cls, elems) -> List[Tuple[Feature, FeatureSchema]]:
        features = c(elems.items()).map_(_.spread(cls.create_feature)).value()
        return features

    @classmethod
    def create_feature(cls, name: str, conf: YamlType) -> Feature:
        match conf:
            case _: return Feature(name, conf)

    @model_validator(mode='after')
    @classmethod
    def set_children_and_type(cls, values):
        features: List[Tuple[Feature, FeatureSchema]] = values.elems or []
        if not is_list(features):
            return values
        for feature, conf in features:
            if conf.elems:
                children, children_conf = tuple(zip(*conf.elems))
                default_feature_type = ST.DISJOINT if all(filter(lambda schema: not schema.elems, children_conf)) else ST.JOINT  # TODO: verify the cond in case if only some values have sub values as in Polish gender
                feature.type = conf.type or default_feature_type
                # TODO: base
                # consume(side_effect(feature.children.connect, children))
        return values


class MainFeaturesSchema(BaseModel):
    graphemes: Optional[FeatureSchema] = None
    morphemes: Optional[FeatureSchema] = None

    @classmethod
    def set_kind(cls, phemes: list[tuple[Feature, ...]], kind: Kind) -> list[tuple[Feature, ...]]:
        utils.apply_to_tree(
            phemes or [],
            apply_func=lambda a: a,  # lambda curr: setattr(curr, 'kind', kind),  # TODO: base
            get_children=lambda a: [],  #lambda curr: curr.children.all(),  # TODO: base
            map_curr=lambda pair: pair[0],
        )
        return phemes

    @classmethod
    def set_kind_for(cls, phemes_schema: FeatureSchema):
        return cls.set_kind(phemes_schema.elems, ST.MORPHEME) if phemes_schema else None

    @field_validator('graphemes', mode='after')
    @classmethod
    def val_graphemes(cls, graphemes):
        return cls.set_kind_for(graphemes)

    @field_validator('morphemes', mode='after')
    @classmethod
    def val_morphemes(cls, morphemes):
        return cls.set_kind_for(morphemes)


class LanguageSchema(BaseModel):  # TODO: think if morphemes shouldn't be required
    general: Optional[Any] = None
    features: Optional[MainFeaturesSchema] = None
    morphemes: Optional[UnitSchema] = None
    graphemes: Optional[UnitSchema] = None
    rules: Optional[RulesSchema] = None

    class Config:
        extra = 'ignore'

    def to_lang(self, name: str) -> Language:
        lang = Language(name=name)
        raise NotImplementedError
