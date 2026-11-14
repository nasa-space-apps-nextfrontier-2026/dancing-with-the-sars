from dataclasses import dataclass
from enum import StrEnum


class Evidence(StrEnum):
    OBSERVED='Observed'; REPORTED='Reported'; CORROBORATED='Corroborated'; UNKNOWN='Unknown'

@dataclass(frozen=True)
class Result:
    area_id: str
    metric: str
    low: float | None
    high: float | None
    unit: str
    label: Evidence
    source_ids: tuple[str, ...]
    date: str | None
    safety_tag: str
    reason: str

NAMES = ('Damage','Facility','Services','People','Shelter','Route','Movement',
         'Alert','Corroboration','Orchestrator','Report','Safety')

def unavailable(name: str, area_id: str = 'demo-area-01') -> Result:
    if name not in NAMES:
        raise ValueError('Unknown function')
    return Result(area_id,name.lower(),None,None,'unknown',Evidence.UNKNOWN,(),None,
                  'restricted_aggregate',f'{name} requires validated inputs; scaffold only')
