from dataclasses import dataclass, field

from old_src2.model.constants import RelNames as R


@dataclass
class RelConf:
    name: str
    from_label: str = field(default='')
    to_label: str = field(default='')


rel_conf = [
    RelConf(R.EX),  # Hyper/Hypo(nymy)
    RelConf(R.FORMS),
    RelConf(R.YIELDS),
    RelConf(R.THROUGH),
]
