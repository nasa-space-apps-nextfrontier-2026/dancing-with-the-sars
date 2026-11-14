"""Fire event model (task M1-04, model B). Standard library only.

Turns FIRMS VIIRS points into "Fire detected" events: drop low-confidence points, drop spots that
burn all the time (industry, flares, landfill), then group points within 1 km and 12 hours.
A satellite fire detection is a heat signal, never proof of a cause, so events carry no cause.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from math import asin, cos, radians, sin, sqrt

CLUSTER_KM = 1.0
CLUSTER_HOURS = 12.0
PERMANENT_DAYS = 5      # distinct days with a detection in the baseline period
GRID_DEG = 0.003        # about 330 m cells for permanent hot spots
CONFIDENCE_RANK = {"low": 0, "l": 0, "nominal": 1, "n": 1, "high": 2, "h": 2}


@dataclass(frozen=True)
class FirePoint:
    lat: float
    lon: float
    time: str          # ISO 8601, UTC
    confidence: str    # low | nominal | high (or l | n | h)
    satellite: str     # e.g. NOAA-20, NOAA-21


@dataclass(frozen=True)
class FireEvent:
    kind: str          # always "fire_detected"
    start: str
    end: str
    lat: float
    lon: float
    points: int
    satellites: tuple[str, ...]
    confidence: str


def _when(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _km(a: FirePoint, b: FirePoint) -> float:
    dlat, dlon = radians(b.lat - a.lat), radians(b.lon - a.lon)
    h = sin(dlat / 2) ** 2 + cos(radians(a.lat)) * cos(radians(b.lat)) * sin(dlon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(h))


def _cell(p: FirePoint) -> tuple[int, int]:
    return round(p.lat / GRID_DEG), round(p.lon / GRID_DEG)


def permanent_spots(baseline: list[FirePoint], min_days: int = PERMANENT_DAYS) -> set[tuple[int, int]]:
    """Grid cells with detections on at least `min_days` different days in the baseline period."""
    days: dict[tuple[int, int], set[str]] = defaultdict(set)
    for p in baseline:
        days[_cell(p)].add(p.time[:10])
    return {cell for cell, d in days.items() if len(d) >= min_days}


def keep(points: list[FirePoint], permanent: set[tuple[int, int]]) -> list[FirePoint]:
    return [p for p in points
            if CONFIDENCE_RANK.get(p.confidence.lower(), 0) >= 1 and _cell(p) not in permanent]


def cluster(points: list[FirePoint]) -> list[FireEvent]:
    """Single-link grouping: a point joins an event if it is within 1 km and 12 h of any member."""
    ordered = sorted(points, key=lambda p: _when(p.time))
    groups: list[list[FirePoint]] = []
    for p in ordered:
        joined = [g for g in groups if any(
            _km(p, q) <= CLUSTER_KM and abs((_when(p.time) - _when(q.time)).total_seconds()) <= CLUSTER_HOURS * 3600
            for q in g)]
        if not joined:
            groups.append([p])
            continue
        joined[0].append(p)
        for extra in joined[1:]:        # a bridging point merges two groups
            joined[0].extend(extra)
            groups.remove(extra)
    return [_event(g) for g in groups]


def _event(group: list[FirePoint]) -> FireEvent:
    times = sorted(p.time for p in group)
    best = max(group, key=lambda p: CONFIDENCE_RANK.get(p.confidence.lower(), 0)).confidence.lower()
    best = {"l": "low", "n": "nominal", "h": "high"}.get(best, best)
    return FireEvent("fire_detected", times[0], times[-1],
                     sum(p.lat for p in group) / len(group), sum(p.lon for p in group) / len(group),
                     len(group), tuple(sorted({p.satellite for p in group})), best)


def fire_events(points: list[FirePoint], baseline: list[FirePoint] | None = None) -> list[FireEvent]:
    return cluster(keep(points, permanent_spots(baseline or [])))
