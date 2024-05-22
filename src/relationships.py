from neomodel import StructuredRel


# has a feature
class Features(StructuredRel):
    rel_name = 'FEATURES'


# is a parent (feature)
class IsSuperOf(StructuredRel):
    rel_name = 'IS_SUPER_OF'


# Is part of [language]
class Belongs(StructuredRel):
    rel_name = 'BELONGS'

