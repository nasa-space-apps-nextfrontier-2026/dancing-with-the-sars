"""U-06: publish the agents' output for the API (doc 25). The API reads these files; it computes nothing.

    python -m worker.main --publish ... --out data/published        (Thanoban's step: alerts, damage, status)
    python -m worker.main --agents --table data/local/building_table.parquet --out data/published

Writes into the published folder, shaped to the contract (PR #24):
- incidents.json        ranked incidents (Incident) + release_at for the 72-hour gate
- insights.json         template sentences (Insight)
- recommendations.json  CIVISAR assistant output per role (analyst, officer, coordinator)
- budget.json           Budget for the whole demo box and each neighbourhood with damage candidates
- buildings/<r8>.json   buildings per H3 r8 neighbourhood for the 3D view: height ranges and the CELL
                        damage result; never residents per building (doc 07)
- agents_manifest.json  counts, inputs and time

Restricted output: the folder is outside Git and read only behind sign-in, role and scope checks.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from worker.agents.assistant import advise
from worker.agents.budget import area_budget, load_assumptions
from worker.agents.inputs import area_facts, load_published, load_table
from worker.agents.insights import insights
from worker.agents.ranking import rank

ROLES = ("analyst", "officer", "coordinator")
INCIDENT_KEYS = ("incident_id", "area_id", "kind", "rank", "score_low", "score_high", "could_rank_higher",
                 "parts", "reasons", "unknowns")
BUDGET_KEYS = ("area_id", "label", "cost_usd", "duration_months", "work_floor_area_m2", "crew_scale",
               "buildings_in_candidate_cells", "assumptions", "limits")
BUILDING_KEYS = ("building_id", "h3_r9", "use", "height_low_m", "height_mid_m", "height_high_m", "height_source",
                 "floors_low", "floors_high", "damage_class", "evidence_label", "second_sensor_agrees")


def _write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, separators=(",", ":"), default=str), encoding="utf-8")


def radar_release(out: Path) -> str | None:
    f = out / "damage.json"
    return json.loads(f.read_text(encoding="utf-8")).get("release_at") if f.exists() else None


def building_features(table: Any, base_path: Path) -> dict[str, list[dict]]:
    """GeoJSON features per r8 area. Geometry from U-01 (WGS84, 6 decimals). Column-wise for speed."""
    import pandas as pd
    import pyarrow.parquet as pq
    import shapely

    geoms = pq.read_table(base_path, columns=["building_id", "geom"]).to_pandas().set_index("building_id")["geom"]
    df = table[["h3_r8", *BUILDING_KEYS]].copy()
    for k in ("height_low_m", "height_mid_m", "height_high_m"):
        df[k] = df[k].astype(float)
    for k in ("floors_low", "floors_high"):
        df[k] = df[k].astype(int)
    sa = df["second_sensor_agrees"].astype(object)
    df["second_sensor_agrees"] = [None if pd.isna(v) else bool(v) for v in sa]
    shapes = shapely.set_precision(shapely.from_wkb(geoms.reindex(df["building_id"]).to_numpy()), 1e-6)
    texts = shapely.to_geojson(shapes)
    out: dict[str, list[dict]] = {}
    for rec, text in zip(df.to_dict("records"), texts, strict=True):
        area = rec.pop("h3_r8")
        rec["height_tag"], rec["damage_tag"] = "Inferred", "From data (cell result)"
        out.setdefault(area, []).append({"type": "Feature", "geometry": json.loads(text) if text else None,
                                         "properties": rec})
    return out


def publish_agents(out_dir: str | Path, table_path: str | Path,
                   base_path: str | Path = "data/local/buildings_base.parquet",
                   now: datetime | None = None) -> dict:
    out, table_path, base_path = Path(out_dir), Path(table_path), Path(base_path)
    now = now or datetime.now(UTC)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    table = load_table(table_path)
    facts = area_facts(table)
    alerts, sources = load_published(out)
    released = radar_release(out)
    alert_release = {a["alert_id"]: a.get("release_at") for a in alerts}

    ranked = rank(alerts, facts, sources, now=now)
    items = [{**{k: i[k] for k in INCIDENT_KEYS},
              "release_at": alert_release.get(i["incident_id"], released)} for i in ranked["items"]]
    _write(out / "incidents.json", {"synthetic": False, "generated_at": ranked["generated_at"],
                                    "weights": ranked["weights"], "data_age": ranked["data_age"], "items": items})
    _write(out / "insights.json", {"generated_at": stamp, "items": insights(ranked, facts, alerts, sources)})

    by_role = {role: {} for role in ROLES}
    for item in ranked["items"]:
        for role in ROLES:
            rec = advise(item, facts.get(item["area_id"]), alerts, sources, role, now)
            by_role[role][item["incident_id"]] = {k: rec[k] for k in ("assistant", "situation", "options",
                                                                       "we_do_not_know", "checklist",
                                                                       "next_review", "note")}
    _write(out / "recommendations.json", {"generated_at": stamp, "by_role": by_role})

    a = load_assumptions()

    def shaped(b: dict) -> dict:
        return {"synthetic": False, **{k: b[k] for k in BUDGET_KEYS}}

    damaged = [area for area, f in facts.items() if sum(f.candidate_cells.values())]
    _write(out / "budget.json", {"generated_at": stamp, "release_at": released,
                                 "whole_demo_box": shaped(area_budget(table, None, a)),
                                 "areas": {area: shaped(area_budget(table, area, a)) for area in damaged}})

    features = building_features(table, base_path) if base_path.exists() else {}
    bdir = out / "buildings"
    for area, feats in features.items():
        _write(bdir / f"{area}.json", {"area_id": area, "release_at": released, "features": feats})

    manifest = {
        "generated_at": stamp, "synthetic": False,
        "inputs": {"building_table": hashlib.sha256(table_path.read_bytes()).hexdigest(),
                   "alerts": len(alerts), "sources": sorted(sources)},
        "incidents": len(items), "insights": len(json.loads((out / "insights.json").read_text())["items"]),
        "budget_areas": len(damaged), "building_files": len(features),
        "buildings": sum(len(v) for v in features.values()),
        "rule": "Restricted: serve only after sign-in, role, area scope and release_at checks. No residents per building.",
    }
    _write(out / "agents_manifest.json", manifest)
    return manifest
