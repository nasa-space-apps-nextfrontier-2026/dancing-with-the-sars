"""Night-light power-loss rule (task M1-04, model A). Pure functions, standard library only.

Rule from docs/18: build a baseline from the last 60 clear nights, then flag a possible power loss
when a cell is below 50% of its baseline on 2 clear nights. Too little evidence gives `unknown`,
never a guess. The wording is "possible power loss", never "blackout".
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import median

BASELINE_NIGHTS = 60
MIN_BASELINE_NIGHTS = 30
DROP_RATIO = 0.5
MIN_DROP_NIGHTS = 2
MIN_BASELINE_RADIANCE = 0.5  # nW/cm2/sr; darker cells give unstable ratios


@dataclass(frozen=True)
class Night:
    date: str                 # YYYY-MM-DD
    radiance: float | None    # None when missing
    clear: bool               # True only for good quality, no cloud, no strong moon


@dataclass(frozen=True)
class Assessment:
    status: str               # "possible_power_loss" | "no_change" | "unknown"
    confidence: str           # "low" | "medium" | "high" | "none"
    baseline: float | None
    ratio: float | None       # recent clear-night median / baseline
    baseline_nights: int
    recent_clear_nights: int
    reason: str


def _usable(nights: list[Night]) -> list[Night]:
    return [n for n in nights if n.clear and n.radiance is not None]


def baseline(history: list[Night], nights: int = BASELINE_NIGHTS) -> tuple[float | None, int]:
    """Median radiance of the latest clear nights in `history` (oldest first)."""
    used = _usable(history)[-nights:]
    if not used:
        return None, 0
    return median(n.radiance for n in used), len(used)


def assess(history: list[Night], recent: list[Night]) -> Assessment:
    base, used = baseline(history)
    now = _usable(recent)
    if base is None or used < MIN_BASELINE_NIGHTS:
        return Assessment("unknown", "none", base, None, used, len(now),
                          f"only {used} clear baseline nights (need {MIN_BASELINE_NIGHTS})")
    if base < MIN_BASELINE_RADIANCE:
        return Assessment("unknown", "none", base, None, used, len(now),
                          "baseline too dark for a stable ratio")
    if len(now) < MIN_DROP_NIGHTS:
        return Assessment("unknown", "none", base, None, used, len(now),
                          f"only {len(now)} clear recent nights (need {MIN_DROP_NIGHTS})")
    last = now[-MIN_DROP_NIGHTS:]
    ratio = median(n.radiance for n in last) / base
    if all(n.radiance < DROP_RATIO * base for n in last):
        if ratio < 0.25 and used >= BASELINE_NIGHTS:
            confidence = "high"
        elif ratio < 0.35:
            confidence = "medium"
        else:
            confidence = "low"
        return Assessment("possible_power_loss", confidence, base, ratio, used, len(now),
                          f"below {int(DROP_RATIO * 100)}% of baseline on {MIN_DROP_NIGHTS} clear nights")
    return Assessment("no_change", "none", base, ratio, used, len(now), "not below the drop threshold")
