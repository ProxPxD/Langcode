from dataclasses import dataclass


@dataclass(frozen=True)
class RelNames:
    EX = 'EX'
    IS = 'IS'
    FORMS = 'FORMS'  # ?
    YIELDS = 'YIELDS'  # ?
    THROUGH = 'THROUGH'  # Same as 'EX' ?

