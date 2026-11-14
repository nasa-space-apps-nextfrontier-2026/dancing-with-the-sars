"""Callable night-light power-loss function for the alert plumbing (task M1-04, model A).

Combines the per-satellite rule from `nightlights.assess` with the two-satellite agreement rule
measured on real data (0.73% flags when both agree, versus 2.7% for one satellite):

* both satellites flag the cell      -> possible_power_loss, confidence high or medium
* only one satellite flags the cell  -> possible_power_loss, confidence low, not corroborated
* no flag and at least one assessable satellite -> no_change
* nothing assessable                 -> unknown, with the reasons

Pure functions, standard library only. Wording is "possible power loss", never "blackout", and the
result is an observation from satellite data, not proof of a cause.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from worker.services.nightlights import Assessment, Night, assess

LEVEL = {"none": 0, "low": 1, "medium": 2, "high": 3}
NAME = {v: k for k, v in LEVEL.items()}
SOURCE = "Black Marble VJ146A2/VJ246A2 (NASA, NOAA-20 and NOAA-21)"


@dataclass(frozen=True)
class CellPowerLoss:
    cell: str
    status: str                 # possible_power_loss | no_change | unknown
    confidence: str             # high | medium | low | none
    corroborated: bool          # True only when both satellites flag the cell
    date: str | None            # date of the latest night used
    satellites_flagged: tuple[str, ...]
    reasons: tuple[str, ...] = field(default_factory=tuple)
    label: str = "Observed"
    source: str = SOURCE


def combine(cell: str, by_satellite: dict[str, tuple[list[Night], list[Night]]]) -> CellPowerLoss:
    """`by_satellite` maps a satellite name to (history, recent nights), oldest first."""
    results: dict[str, Assessment] = {sat: assess(history, recent)
                                      for sat, (history, recent) in by_satellite.items()}
    flagged = tuple(sorted(s for s, r in results.items() if r.status == "possible_power_loss"))
    assessable = [s for s, r in results.items() if r.status in ("possible_power_loss", "no_change")]
    dates = [n.date for _, recent in by_satellite.values() for n in recent]
    latest = max(dates) if dates else None
    reasons = tuple(f"{s}: {r.reason}" for s, r in sorted(results.items()))
    if len(flagged) >= 2:
        floor = min(LEVEL[results[s].confidence] for s in flagged)
        confidence = "high" if floor >= LEVEL["medium"] else "medium"
        return CellPowerLoss(cell, "possible_power_loss", confidence, True, latest, flagged, reasons)
    if len(flagged) == 1:
        return CellPowerLoss(cell, "possible_power_loss", "low", False, latest, flagged, reasons)
    if assessable:
        return CellPowerLoss(cell, "no_change", "none", False, latest, (), reasons)
    return CellPowerLoss(cell, "unknown", "none", False, latest, (), reasons)


def power_loss_events(series: dict[tuple[str, str], list[Night]], recent_nights: int = 2) -> list[dict]:
    """Alert events for every cell flagged on its latest nights.

    `series` maps (satellite, cell) to that satellite's nights, oldest first, as returned by
    `evaluate_nightlights.load`. Each event has the fields the alert feed needs: area, time, source,
    label, confidence, plus whether two satellites agree.
    """
    cells: dict[str, dict[str, tuple[list[Night], list[Night]]]] = {}
    for (satellite, cell), nights in series.items():
        if len(nights) > recent_nights:
            cells.setdefault(cell, {})[satellite] = (nights[:-recent_nights], nights[-recent_nights:])
    events = []
    for cell, by_satellite in sorted(cells.items()):
        result = combine(cell, by_satellite)
        if result.status == "possible_power_loss":
            events.append({"kind": "possible_power_loss", "area": cell, "time": result.date,
                           "source": result.source, "label": result.label,
                           "confidence": result.confidence, "corroborated": result.corroborated,
                           "satellites": list(result.satellites_flagged),
                           "reasons": list(result.reasons)})
    return events
