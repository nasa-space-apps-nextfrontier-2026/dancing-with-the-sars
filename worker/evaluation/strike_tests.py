"""Strike-enrichment test for the damage model (task M1-04, model C). Standard library only.

Question: are cells flagged as candidate damage more common near reported strike events than far
from them? Reports are approximate and a strike is not a collapse, so this is evidence about the
model, never proof. The same-district control checks that the result is not just "some districts
have more of both". Too little data gives `insufficient`, not a number.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from statistics import median

NEAR_KM = 2.0
MIN_CELLS_EACH_SIDE = 30
LIMITS = ("Radar misses some damage, so flagged counts are minimums. Strike reports are approximate "
          "and a strike is not a collapse. Results are candidates, never confirmed damage.")


@dataclass(frozen=True)
class Cell:
    cell_id: str
    lat: float
    lon: float
    district: str
    flagged: bool      # model class is a candidate-damage class at the chosen threshold


@dataclass(frozen=True)
class Event:
    lat: float
    lon: float


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    h = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(h))


def is_near(cell: Cell, events: list[Event], near_km: float = NEAR_KM) -> bool:
    return any(_km(cell.lat, cell.lon, e.lat, e.lon) <= near_km for e in events)


def _share(cells: list[Cell]) -> float | None:
    return sum(c.flagged for c in cells) / len(cells) if cells else None


def strike_enrichment(cells: list[Cell], events: list[Event], near_km: float = NEAR_KM) -> dict:
    near = [c for c in cells if is_near(c, events, near_km)]
    far = [c for c in cells if c not in near]
    out = {"near_km": near_km, "cells": len(cells), "events": len(events),
           "near_cells": len(near), "far_cells": len(far), "limits": LIMITS}
    if len(near) < MIN_CELLS_EACH_SIDE or len(far) < MIN_CELLS_EACH_SIDE:
        return {**out, "status": "insufficient",
                "reason": f"need at least {MIN_CELLS_EACH_SIDE} cells near and far"}
    near_share, far_share = _share(near), _share(far)
    # same-district control: compare near and far only inside districts that have both
    diffs = []
    for district in sorted({c.district for c in cells}):
        n = [c for c in near if c.district == district]
        f = [c for c in far if c.district == district]
        if len(n) >= 5 and len(f) >= 5:
            diffs.append(_share(n) - _share(f))
    return {**out, "status": "ok",
            "near_flagged_share": near_share, "far_flagged_share": far_share,
            "difference": near_share - far_share,
            "relative_rate": (near_share / far_share) if far_share else None,
            "false_alarm_rate_far": far_share,   # far cells are the quiet comparison group
            "districts_compared": len(diffs),
            "same_district_median_difference": median(diffs) if diffs else None}
