"""Real-data area summary (DEMO_SYNTHETIC=false) for an H3 r8 neighbourhood.

People come only from Kisara's population file (K-04: DATA_ROOT/local/population.csv.gz with
cell_id, pop_low, pop_high, pop_year per H3 r9 cell). The AreaSummary contract requires whole-number
people ranges, so without that file the summary is unavailable: numbers are never invented.

Affected = residents of cells with any radar candidate; displaced uses the UNOSAT housing shares
(destroyed/severe 100%, moderate 50%, possible 20%). Derived values take the weakest evidence label
of their inputs (Unknown < Reported < Observed < Corroborated).
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import hashlib
from functools import lru_cache
from typing import Any

from backend.app.core.permissions import ROLE_LEVEL
from backend.app.core.security import Identity
from backend.app.policy.release import is_released, now_utc
from backend.app.services.live_real import iso
from backend.app.services.radar_real import data_root

POPULATION_FILE = "local/population.csv.gz"
DISPLACED_SHARE = {
    "destroyed_or_severe_candidate": 1.0,
    "moderate_candidate": 0.5,
    "possible_candidate": 0.2,
}
LABEL_RANK = {"Unknown": 0, "Reported": 1, "Observed": 2, "Corroborated": 3}
WARNING = (
    "Candidate radar change and modelled population (pre-displacement estimate). "
    "Not confirmed damage; people are ranges; verify before planning."
)


class Unavailable(Exception):
    """A required input (for example population) is not loaded."""


def weakest(*labels: str) -> str:
    return min(labels, key=lambda x: LABEL_RANK.get(x, 0))


@lru_cache(maxsize=2)
def _population(path: str, mtime: float) -> dict[str, tuple[int, int, int]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
        return {
            r["cell_id"]: (int(float(r["pop_low"])), int(float(r["pop_high"])), int(r["pop_year"]))
            for r in csv.DictReader(f)
            if r["pop_low"] not in ("", None)
        }


def population() -> dict[str, tuple[int, int, int]] | None:
    p = data_root() / POPULATION_FILE
    return _population(str(p), p.stat().st_mtime) if p.exists() else None


def _value(
    area: str,
    metric: str,
    low: int,
    high: int,
    label: str,
    sources: list[str],
    date: str,
    run: str,
    acquired: str,
    processed: str,
    limitations: list[str],
) -> dict[str, Any]:
    vid = "summary-" + hashlib.sha256(f"{area}|{metric}|{run}".encode()).hexdigest()[:24]
    return {
        "synthetic": False,
        "value_id": vid,
        "area_id": area,
        "metric": metric,
        "low": int(low),
        "high": int(high),
        "unit": "people",
        "label": label,
        "source": sources,
        "date": date,
        "safety_tag": "restricted_aggregate",
        "lineage_ids": [run],
        "processing_run_id": run,
        "processing_version": "area-summary-0.1",
        "confidence": None,
        "acquired_at": acquired,
        "processed_at": processed,
        "release_at": acquired,
        "freshness": "Stale",
        "cached": True,
        "limitations": limitations,
    }


def services_from(visible_alerts: list[Any]) -> list[dict[str, Any]]:
    """Power from released "Possible power loss" alerts; water, health and comms stay Unknown."""
    power = [a for a in visible_alerts if a.type == "possible_power_loss"]
    return [
        {
            "type": "power",
            "status": "Possible loss" if power else "Unknown",
            "label": power[0].label if power else "Unknown",
            "source": list(power[0].source) if power else [],
            "date": iso(power[0].detected_at) if power else None,
        },
        *(
            {"type": t, "status": "Unknown", "label": "Unknown", "source": [], "date": None}
            for t in ("water", "health", "comms")
        ),
    ]


def area_summary(
    engine: Any, area_id: str, identity: Identity, as_of: dt.datetime | None = None
) -> dict[str, Any] | None:
    """Held (unreleased) records are left out for every role; Admin is not a bypass for the hold or for area scope (doc 07)."""
    from sqlalchemy import text

    pop = population()
    if pop is None:
        raise Unavailable(
            "Population is not loaded (K-04); the summary needs it for people ranges."
        )
    current = now_utc()
    if as_of is not None and as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=dt.UTC)
    cutoff = min(as_of, current) if as_of is not None else current
    with engine.connect() as conn:
        area = conn.execute(
            text("SELECT area_id, resolution FROM areas WHERE area_id = :a"), {"a": area_id}
        ).first()
        if area is None:
            return None
        art = conn.execute(
            text(
                "SELECT a.id, a.run_id, a.after_acquired_at FROM radar_artifacts a "
                "JOIN areas requested ON requested.area_id = :a "
                "WHERE (a.area_id = requested.area_id OR a.area_id = requested.parent_id) "
                "AND a.before_acquired_at < '2026-06-01' AND a.after_acquired_at <= :cutoff "
                "AND EXISTS (SELECT 1 FROM radar_area_results visible "
                "JOIN areas visible_area ON visible_area.area_id = visible.area_id "
                "WHERE visible.artifact_id = a.id "
                "AND (visible_area.area_id = requested.area_id "
                "OR visible_area.parent_id = requested.area_id) "
                "AND visible.release_at IS NOT NULL AND visible.release_at <= :cutoff) "
                "ORDER BY a.after_acquired_at DESC LIMIT 1"
            ),
            {"a": area_id, "cutoff": cutoff},
        ).first()
        if art is None:
            raise Unavailable("No eligible released radar observation is available.")
        results = conn.execute(
            text(
                "SELECT r.area_id, r.classification, r.evidence_label, r.reason_codes, r.release_at "
                "FROM radar_area_results r JOIN areas c ON c.area_id = r.area_id "
                "WHERE r.artifact_id = :art AND (c.parent_id = :a OR c.area_id = :a)"
            ),
            {"art": art.id if art else "", "a": area_id},
        ).all()
        cells = [
            r[0]
            for r in conn.execute(
                text("SELECT area_id FROM areas WHERE parent_id = :a OR area_id = :a"),
                {"a": area_id},
            ).all()
        ]
        values = conn.execute(
            text("SELECT record FROM metric_values WHERE area_id = :a AND run_id = :r"),
            {"a": area_id, "r": art.run_id if art else ""},
        ).all()
        alerts = conn.execute(
            text(
                "SELECT alert_id, type, label, release_at, source, detected_at FROM alerts WHERE area_id = :a "
                "ORDER BY detected_at DESC"
            ),
            {"a": area_id},
        ).all()

    shown = [r for r in results if is_released(r.release_at, cutoff)]
    if not shown:
        raise Unavailable("The selected radar observation has no released area evidence.")
    level = {
        r.area_id: next(
            (c.split(":", 1)[1] for c in r.reason_codes if c.startswith("level:")), None
        )
        for r in shown
        if r.classification == "candidate_change"
    }
    corroborated = any(r.evidence_label == "Corroborated" for r in shown if r.area_id in level)
    radar_label = "Corroborated" if corroborated else weakest(*(r.evidence_label for r in shown))

    years = {pop[c][2] for c in cells if c in pop}
    res_low = sum(pop[c][0] for c in cells if c in pop)
    res_high = sum(pop[c][1] for c in cells if c in pop)
    aff_low = sum(pop[c][0] for c in level if c in pop)
    aff_high = sum(pop[c][1] for c in level if c in pop)
    dis_low = round(sum(pop[c][0] * DISPLACED_SHARE.get(level[c], 0) for c in level if c in pop))
    dis_high = round(sum(pop[c][1] * DISPLACED_SHARE.get(level[c], 0) for c in level if c in pop))

    run = art.run_id
    acquired = iso(art.after_acquired_at)
    processed = iso(cutoff)
    date = acquired[:10]
    pop_src = ["worldpop-lbn"]
    radar_src = ["nisar-gcov-beta-151d72", "nisar-gcov-provisional-151d72"]
    pre = [
        f"WorldPop {min(years) if years else 'n/a'} pre-displacement estimate, not people there now"
    ]
    residents = _value(
        area_id,
        "residents_baseline",
        res_low,
        res_high,
        "Reported",
        pop_src,
        date,
        run,
        acquired,
        processed,
        pre,
    )
    affected = _value(
        area_id,
        "potentially_affected",
        aff_low,
        aff_high,
        weakest("Reported", radar_label),
        pop_src + radar_src,
        date,
        run,
        acquired,
        processed,
        [*pre, "Residents of cells with candidate radar change"],
    )
    displaced = _value(
        area_id,
        "potentially_displaced",
        dis_low,
        dis_high,
        weakest("Reported", radar_label),
        pop_src + radar_src,
        date,
        run,
        acquired,
        processed,
        [*pre, "UNOSAT shares: destroyed/severe 100%, moderate 50%, possible 20%"],
    )

    visible_alerts = [
        a for a in alerts if a.detected_at <= cutoff and is_released(a.release_at, cutoff)
    ]
    power = [a for a in visible_alerts if a.type == "possible_power_loss"]
    services = services_from(visible_alerts)
    bring = (
        [
            {
                "item": "Generators and lights",
                "basis_value_ids": [a.alert_id for a in power],
                "quantity": None,
            }
        ]
        if power
        else []
    )
    bring.append(
        {
            "item": "Verify water and health services before supply planning",
            "basis_value_ids": [],
            "quantity": None,
        }
    )
    radar_vals = [
        v[0]
        for v in values
        if v[0]["low"] is not None
        and v[0]["date"] <= cutoff.date().isoformat()
        and is_released(v[0]["release_at"], cutoff)
    ]
    lvl = ROLE_LEVEL.get(identity.role, 0)
    return {
        "synthetic": False,
        "area_id": area_id,
        "name": f"Neighbourhood {area_id[:7]}",
        "as_of": processed,
        "people": {
            "residents": residents,
            "potentially_affected": affected,
            "potentially_displaced": displaced,
        },
        "vulnerable_groups": [],
        "services": services,
        "what_to_bring": bring,
        "facilities": [],
        "hazards": [{"alert_id": a.alert_id, "type": a.type} for a in visible_alerts],
        "severity": {
            "rank": None,
            "parts": ["damage", "people", "facilities", "services", "roads"],
            "reason": "No rank until facilities, services and roads are loaded",
        },
        "nearest_reported_operating_hospital": None,
        "route_options": [],
        "shelter_candidates": [],
        "permissions": {
            "routes": lvl >= ROLE_LEVEL["officer"],
            "shelters": lvl >= ROLE_LEVEL["coordinator"],
            "brief": True,
        },
        "evidence": [residents, affected, displaced, *radar_vals],
        "freshness": "Stale",
        "cached": True,
        "safety_tag": "restricted_aggregate",
        "warning": WARNING,
    }
