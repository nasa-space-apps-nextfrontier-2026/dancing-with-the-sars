"""U-06: load the agents' published output into PostGIS (one transaction; replaces the previous load).

    python -m worker.main --agents --table data/local/building_table.parquet --out data/published
    python -m scripts.load_agent_outputs [--published data/published]

Reads incidents.json, recommendations.json, insights.json, budget.json and buildings/<r8>.json
written by worker/agents/publish_agents.py. A failure leaves the database unchanged. No residents
per building are stored (the publish step never writes them; checked here again).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import text

CHUNK = 5000
ROLES = ("analyst", "officer", "coordinator")


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _ts(value: str | None) -> dt.datetime | None:
    return dt.datetime.fromisoformat(value) if value else None


def load_files(published: Path) -> dict[str, Any]:
    needed = ["incidents.json", "recommendations.json", "insights.json", "budget.json"]
    missing = [n for n in needed if not (published / n).exists()]
    if missing:
        raise SystemExit(f"Missing published files: {', '.join(missing)}. Run worker.main --agents first.")
    data = {n.split(".")[0]: _read(published / n) for n in needed}
    data["buildings"] = [_read(f) for f in sorted((published / "buildings").glob("*.json"))]
    for area in data["buildings"]:
        for feat in area["features"]:
            if any(k.startswith("resident") for k in feat["properties"]):
                raise SystemExit("Refusing to load: a building carries residents (doc 07).")
    return data


def load(engine: Any, data: dict[str, Any]) -> dict[str, int]:
    inc = data["incidents"]
    run_id = hashlib.sha256(json.dumps(inc["generated_at"]).encode()).hexdigest()[:16]
    counts = {"incidents": len(inc["items"]),
              "recommendations": sum(len(v) for v in data["recommendations"]["by_role"].values()),
              "insights": len(data["insights"]["items"]),
              "budgets": 1 + len(data["budget"]["areas"]),
              "buildings": sum(len(a["features"]) for a in data["buildings"])}
    with engine.begin() as conn:
        for table in ("agent_recommendations", "agent_incidents", "agent_insights", "agent_budgets",
                      "agent_buildings", "agent_runs"):
            conn.execute(text(f"DELETE FROM {table}"))
        conn.execute(text(
            "INSERT INTO agent_incidents (incident_id, area_id, kind, rank, score_low, score_high, release_at, record) "
            "VALUES (:id, :area, :kind, :rank, :lo, :hi, :rel, CAST(:rec AS jsonb))"),
            [{"id": i["incident_id"], "area": i["area_id"], "kind": i["kind"], "rank": i["rank"],
              "lo": i["score_low"], "hi": i["score_high"], "rel": _ts(i.get("release_at")),
              "rec": json.dumps({k: v for k, v in i.items() if k != "release_at"})} for i in inc["items"]])
        rec_rows = [{"id": iid, "role": role, "rec": json.dumps(r)}
                    for role in ROLES for iid, r in data["recommendations"]["by_role"].get(role, {}).items()]
        if rec_rows:
            conn.execute(text("INSERT INTO agent_recommendations (incident_id, role, record) "
                              "VALUES (:id, :role, CAST(:rec AS jsonb))"), rec_rows)
        if data["insights"]["items"]:
            conn.execute(text("INSERT INTO agent_insights (record) VALUES (CAST(:rec AS jsonb))"),
                         [{"rec": json.dumps(x)} for x in data["insights"]["items"]])
        budget = data["budget"]
        rel = _ts(budget.get("release_at"))
        conn.execute(text("INSERT INTO agent_budgets (area_id, release_at, record) "
                          "VALUES (:a, :rel, CAST(:rec AS jsonb))"),
                     [{"a": "south-lebanon-demo", "rel": rel,
                       "rec": json.dumps(budget["whole_demo_box"] | {"area_id": "south-lebanon-demo"})}]
                     + [{"a": a, "rel": rel, "rec": json.dumps(b)} for a, b in budget["areas"].items()])
        rows = [{"id": f["properties"]["building_id"], "r8": area["area_id"], "rel": _ts(area.get("release_at")),
                 "g": json.dumps(f["geometry"]) if f["geometry"] else None, "p": json.dumps(f["properties"])}
                for area in data["buildings"] for f in area["features"]]
        stmt = text("INSERT INTO agent_buildings (building_id, h3_r8, release_at, geom, properties) VALUES "
                    "(:id, :r8, :rel, ST_SetSRID(ST_GeomFromGeoJSON(:g), 4326), CAST(:p AS jsonb))")
        for start in range(0, len(rows), CHUNK):
            conn.execute(stmt, rows[start:start + CHUNK])
        conn.execute(text("INSERT INTO agent_runs (run_id, generated_at, loaded_at, counts) "
                          "VALUES (:r, :g, :l, CAST(:c AS jsonb))"),
                     {"r": run_id, "g": _ts(inc["generated_at"]), "l": dt.datetime.now(dt.UTC),
                      "c": json.dumps(counts)})
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--published", type=Path, default=Path("data/published"))
    args = ap.parse_args(argv)
    from backend.app.db.base import make_engine

    print(json.dumps(load(make_engine(), load_files(args.published))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
