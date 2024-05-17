from __future__ import annotations

from typing import Dict, Optional

import pydash as _
# noinspection PyUnresolvedReferences
from neomodel import StructuredNode, StringProperty, RelationshipTo, StructuredRel, DoesNotExist, MultipleNodesReturned, NeomodelPath, NodeMeta, config, \
    Property  # For some reason, the neomodel requires to import it
from pydash import chain as c
from toolz import itemmap

from src import utils
from src.constants import CT
from src.exceptions import AmbiguousNameException, DoNotExistException
from src.lang_typing import YamlType, Config, BasicYamlType
from src.neomodel_mixins import ICorePropertied, INeo4jFormatable, INeo4jHierarchied
from src.utils import is_dict, adjust_str, exceptions_to

config.DATABASE_URL = 'bolt://neo4j_username:neo4j_password@localhost:7687'


class LangCodeNode(ICorePropertied, INeo4jFormatable, StructuredNode):
    # TODO: resolve as in: https://stackoverflow.com/questions/5189699/how-to-make-a-class-property
    # @classmethod
    # @property
    # def main_label(cls) -> str:
    #     return cls.__class__.__name__

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__custom_property_names: set = set()

    @classmethod
    def get_from_all(cls, raises: bool = True, **kwargs) -> Optional[LangCodeNode]:
        try:
            return cls.nodes.get(**kwargs)
        except MultipleNodesReturned:
            exception = AmbiguousNameException(**kwargs)
        except DoesNotExist:
            exception = DoNotExistException(**kwargs)
        except Exception as e:
            exception = e

        if raises and exception:
            raise exception
        return None

    @classmethod
    @exceptions_to(true=AmbiguousNameException, false=DoesNotExist, if_none=True)
    def is_node_existing(cls, **kwargs):  # The name to minimalize the chances for the name to be a property
        return cls.get_from_all(raises=True, **kwargs)

    @adjust_str('.self')
    def __repr__(self):
        return f'{self:label}({self.name=}, {self.kind=})'


class Featuring(StructuredRel):
    rel_name = 'FEATURES'


class IsSuperOf(StructuredRel):
    rel_name = 'IS_SUPER'


class Feature(LangCodeNode, INeo4jHierarchied):
    type = StringProperty(
        choices=utils.map_conf_list_to_dict(CT.FEATURE_TYPES)
    )
    children = RelationshipTo(
        cls_name='Feature',  # TODO: check if "Feature.__class__.__name__" can work
        relation_type=IsSuperOf.rel_name,
        model=IsSuperOf,
    )

    @adjust_str('.self')
    def __repr__(self):
        repr: str = super().__repr__()
        return repr[:-1] + f', {self.type=})'

    def is_leaf(self) -> bool:
        return not self.children.manager.is_connected()


class IFeatured(LangCodeNode):
    def get_feature(self, feature_name: str) -> Feature:
        raise NotImplementedError
        # return Feature.get_one_next_up_for(name=feature_name, kind=self.kind, __connected_node=self)

    def has_feature(self, feature_name: str):
        raise NotImplementedError

    def set_feature(self, feature_name: str, feature_val: YamlType) -> None:
        raise NotImplementedError


class Unit(LangCodeNode, IFeatured):
    features = RelationshipTo(
        cls_name=Feature.__class__.__name__,
        relation_type=Featuring.rel_name,
        model=Featuring,
    )

    def is_(self, feature_name: str) -> bool:
        paths = self._get_paths_down_for(feature_name)
        return bool(paths)

    def set_conf(self, conf: Config) -> None:
        self.clean_conf()
        self.update_conf(conf)

    def clean_conf(self) -> None:
        c(self.__class__.__all_properties__).keys().without(self.core_property_names).for_each(self.__delattr__)  # TODO: make sure that for_each executes the statement

    def update_conf(self, conf: Config) -> None:
        itemmap(_.spread(self.set_conf_entry), conf or {})

    def set_conf_entry(self, key: str, val: YamlType) -> None:
        self

    def set_feature(self, feature_name: str, val: BasicYamlType | Dict) -> None:
        # TODO: think how to handle lists
        # TODO: think of and analyze a critical section to differentiate the exceptions of
        #  - non-existance
        #  - non-connnection
        #  PS: add retries as decorator
        feature = Feature.get_from_all(name=feature_name, kind=self.kind, raises=False)
        featuring_feature = Feature.get_from_all(name=val, kind=self.kind, raises=False)
        if not feature:
            setattr(self, feature_name, val)  # Either a dict or not
        elif feature and featuring_feature:
            self.features.manager.connect(featuring_feature)
        elif feature and not featuring_feature and not is_dict(val):
            self.features.manager.connect(feature, {'val': val})
        elif feature and not featuring_feature and is_dict(val):
            self.update_conf(val)  # TODO: add validation by feature type
        else:
            raise ValueError

