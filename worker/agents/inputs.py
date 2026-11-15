"""Shared inputs for the agents: per-neighbourhood (H3 r8) facts from the building table, plus the
published alerts and source status (worker/publish.py). Nothing here invents a value: a fact that
cannot be computed is None, and the agents report it as unknown."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

CANDIDATES = ("destroyed_or_severe_candidate", "moderate_candidate", "possible_candidate")
ASSESSED = (*CANDIDATES, "no_detected_change", "other_change")
FACILITY_USES = ("hospital", "clinic", "water", "power", "school")


@dataclass
class AreaFacts:
    area_id: str
    buildings: int
    residents_low: int | None          # area total from the population file; None: not loaded
    residents_high: int | None
    candidate_cells: dict[str, int]    # class -> number of r9 cells
    corroborated_cells: int
    assessed_cells: int
    unknown_cells: int
    facilities_mapped: dict[str, int]  # use -> buildings tagged in OSM
    facilities_hit: dict[str, int]     # use -> buildings in candidate cells
    candidate_floor_m2: dict[str, float] = field(default_factory=dict)  # class -> floor area (middle floors)
    candidate_floor_low_m2: dict[str, float] = field(default_factory=dict)
    candidate_floor_high_m2: dict[str, float] = field(default_factory=dict)
    run_id: str | None = None


def area_people(population: pd.DataFrame | None) -> dict[str, tuple[int, int]]:
    """People per H3 r8 area from the population file (K-04: cell_id r9, pop_low, pop_high).

    Uses every r9 cell of the area, including cells with no OSM building, so area totals are not
    reduced to the people that could be placed in buildings."""
    if population is None:
        return {}
    import h3

    pop = population.dropna(subset=["pop_low", "pop_high"])
    parents = pop["cell_id"].map(lambda c: h3.cell_to_parent(c, 8))
    sums = pop.groupby(parents)[["pop_low", "pop_high"]].sum()
    return {a: (round(float(r.pop_low)), round(float(r.pop_high))) for a, r in sums.iterrows()}


def area_facts(table: pd.DataFrame, population: pd.DataFrame | None = None) -> dict[str, AreaFacts]:
    """One AreaFacts per r8 area of the building table (pipelines/buildings/table.py).

    People come from the population file (area totals), never from summing building rows; without
    the file they are None (unknown)."""
    people = area_people(population)
    out: dict[str, AreaFacts] = {}
    cells = table.drop_duplicates("h3_r9")[["h3_r9", "h3_r8", "damage_class", "evidence_label"]]
    for area, g in table.groupby("h3_r8"):
        c = cells[cells["h3_r8"] == area]
        cand = g[g["damage_class"].isin(CANDIDATES)]
        fl_low = cand["footprint_m2"] * cand["floors_low"]
        fl_high = cand["footprint_m2"] * cand["floors_high"]
        out[area] = AreaFacts(
            area_id=area, buildings=len(g),
            residents_low=people.get(area, (None, None))[0], residents_high=people.get(area, (None, None))[1],
            candidate_cells={k: int((c["damage_class"] == k).sum()) for k in CANDIDATES},
            corroborated_cells=int(((c["evidence_label"] == "corroborated") & c["damage_class"].isin(CANDIDATES)).sum()),
            assessed_cells=int(c["damage_class"].isin(ASSESSED).sum()),
            unknown_cells=int((~c["damage_class"].isin(ASSESSED)).sum()),
            facilities_mapped={u: int((g["use"] == u).sum()) for u in FACILITY_USES},
            facilities_hit={u: int((cand["use"] == u).sum()) for u in FACILITY_USES},
            candidate_floor_m2={k: float((cand["footprint_m2"] * (cand["floors_low"] + cand["floors_high"]) / 2)
                                         [cand["damage_class"] == k].sum()) for k in CANDIDATES},
            candidate_floor_low_m2={k: float(fl_low[cand["damage_class"] == k].sum()) for k in CANDIDATES},
            candidate_floor_high_m2={k: float(fl_high[cand["damage_class"] == k].sum()) for k in CANDIDATES},
            run_id=str(g["run_id"].dropna().iloc[0]) if g["run_id"].notna().any() else None,
        )
    return out


def load_published(directory: Path) -> tuple[list[dict], dict[str, dict]]:
    """(alerts, sources by id) from worker.publish output; empty when not published."""
    alerts_f, manifest_f = directory / "alerts.json", directory / "manifest.json"
    alerts = json.loads(alerts_f.read_text(encoding="utf-8"))["items"] if alerts_f.exists() else []
    sources = ({s["id"]: s for s in json.loads(manifest_f.read_text(encoding="utf-8"))["sources"]}
               if manifest_f.exists() else {})
    return alerts, sources


def source_ok(sources: dict[str, dict], name: str) -> bool:
    s = sources.get(name)
    return bool(s and s.get("last_success_at") and not s.get("failure"))


def parse_time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def load_population(path: Path | None) -> pd.DataFrame | None:
    """K-04 population file, or None when it is not there (people then stay unknown)."""
    return pd.read_csv(path) if path is not None and Path(path).exists() else None


def load_table(path: Path) -> pd.DataFrame:
    import pyarrow.parquet as pq

    return pq.read_table(path).to_pandas()


def as_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)
