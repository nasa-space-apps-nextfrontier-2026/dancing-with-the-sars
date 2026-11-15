"""M3-01 loader: put the M1 NISAR results into PostGIS in one transaction.

Reads the private M1 outputs (damage tables per run) and the contract records written by
`pipelines/radar/nisar/export_contract.py`, then fills areas, datasets, processing_runs,
radar_artifacts, radar_area_results and metric_values. Re-running replaces the same runs
(idempotent); any error rolls the whole load back.

Needs the radar pipeline packages (pandas, pyarrow, h3) as well as the backend ones:
    python -m scripts.load_radar_results --replace

No raw rasters go into the database; artifacts keep a private relative path and a checksum.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = Path("data/private/nisar/model")
CONTRACT_DIR = Path("data/local/radar_contract")
MANIFESTS = Path("data/manifests")
AOI_ID = "south-lebanon-demo"
RELEASE_DELAY = dt.timedelta(hours=72)
NAMESPACE = uuid.UUID("6f1c7c2e-4b8a-4d55-9a57-2c1f5c0d7e11")  # fixed: same input -> same ids

# The 0001 schema allows three classifications; the detailed M1 level goes into reason_codes.
CLASS_MAP = {
    "destroyed_or_severe_candidate": "candidate_change",
    "moderate_candidate": "candidate_change",
    "possible_candidate": "candidate_change",
    "other_change": "other_change",
    "unknown": "Unknown",
}


def stable_id(*parts: str) -> str:
    return str(uuid.uuid5(NAMESPACE, "|".join(parts)))


def to_dt(ts: str) -> dt.datetime:
    return dt.datetime.fromisoformat(ts)


def classify(row: dict[str, Any]) -> dict[str, Any] | None:
    """One radar_area_results row, or None for 'no detected change' (absence = none detected)."""
    cls = CLASS_MAP.get(row["damage_class"])
    if cls is None:
        return None
    reasons = [r for r in (row.get("reasons") or "").split("|") if r]
    if cls == "candidate_change":
        reasons = [f"level:{row['damage_class']}", *reasons]
    ev = row.get("evidence_label")
    label = ("Unknown" if cls == "Unknown" else "Corroborated" if ev == "corroborated" else "Observed")
    score = None if cls == "Unknown" or row.get("score") is None else float(row["score"])
    return {"classification": cls, "anomaly_score": score, "evidence_label": label,
            "reason_codes": reasons}


def cell_polygon_wkt(cell: str) -> str:
    from h3.api import basic_str as h3s

    ring = [(lng, lat) for lat, lng in h3s.cell_to_boundary(cell)]
    ring.append(ring[0])
    return "POLYGON((" + ", ".join(f"{x:.7f} {y:.7f}" for x, y in ring) + "))"


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def runs_to_load(scenes: dict[str, Any]) -> list[dict[str, Any]]:
    """Tier A plus every time-slider pass, with the acquisitions each compares."""
    start = {s["date"]: s["selected"]["start"] for s in scenes["scenes"] if s["product"] == "GCOV"}
    before = sorted(s["date"] for s in scenes["scenes"] if s["tier"] == "A-before" and s["product"] == "GCOV")
    june = sorted(s["date"] for s in scenes["scenes"] if s["tier"] == "A-after" and s["product"] == "GCOV")
    mat = {s["date"]: s["selected"]["maturity"] for s in scenes["scenes"] if s["product"] == "GCOV"}
    runs = [{"dir": MODEL_DIR, "before": start[before[-1]], "after_first": start[june[0]],
             "after_last": start[june[-1]], "maturity": mat[june[-1]]}]
    for d in sorted(p.name for p in (MODEL_DIR / "slider").glob("*") if (p / "run.json").exists()):
        runs.append({"dir": MODEL_DIR / "slider" / d, "before": start[june[-1]],
                     "after_first": start[d], "after_last": start[d], "maturity": mat[d]})
    return runs


def load(engine: Any, replace: bool) -> dict[str, int]:
    import pandas as pd
    from sqlalchemy import text

    scenes = json.loads((MANIFESTS / "nisar.json").read_text(encoding="utf-8"))
    sources = json.loads((CONTRACT_DIR / "sources.json").read_text(encoding="utf-8"))
    values = json.loads((CONTRACT_DIR / "metric_values.json").read_text(encoding="utf-8"))
    runs = runs_to_load(scenes)
    counts = {"datasets": 0, "runs": 0, "areas": 0, "artifacts": 0, "results": 0, "values": 0}

    with engine.begin() as conn:  # one transaction: all or nothing
        for s in sources:
            conn.execute(text(
                "INSERT INTO datasets (id, provider, product, terms_url, approved) "
                "VALUES (:id, :provider, :product, :url, true) ON CONFLICT (id) DO UPDATE SET "
                "provider = EXCLUDED.provider, product = EXCLUDED.product, terms_url = EXCLUDED.terms_url"),
                {"id": s["source_id"], "provider": s["provider"], "product": s["name"],
                 "url": s["source_url"]})
            counts["datasets"] += 1

        conn.execute(text("INSERT INTO areas (area_id, resolution, parent_id, geom) "
                          "VALUES (:id, 0, NULL, NULL) ON CONFLICT (area_id) DO NOTHING"), {"id": AOI_ID})
        tables = {}
        for r in runs:
            run = json.loads((r["dir"] / "run.json").read_text(encoding="utf-8"))
            r["run_id"] = run["run_id"]
            tables[r["run_id"]] = pd.read_parquet(r["dir"] / "damage_cells.parquet")
        cells9 = sorted({c for t in tables.values() for c in t["h3_r9"]})
        cells8 = sorted({c for t in tables.values() for c in t["h3_r8"]} | {v["area_id"] for v in values})
        parent9 = {c: p for t in tables.values() for c, p in zip(t["h3_r9"], t["h3_r8"], strict=True)}
        area_rows = ([{"id": c, "res": 8, "parent": AOI_ID, "wkt": cell_polygon_wkt(c)} for c in cells8] +
                     [{"id": c, "res": 9, "parent": parent9[c], "wkt": cell_polygon_wkt(c)} for c in cells9])
        conn.execute(text(
            "INSERT INTO areas (area_id, resolution, parent_id, geom) VALUES "
            "(:id, :res, :parent, ST_GeomFromText(:wkt, 4326)) ON CONFLICT (area_id) DO NOTHING"), area_rows)
        counts["areas"] = len(area_rows) + 1

        for r in runs:
            rid = r["run_id"]
            if replace:
                conn.execute(text("DELETE FROM radar_area_results WHERE artifact_id IN "
                                  "(SELECT id FROM radar_artifacts WHERE run_id = :r)"), {"r": rid})
                conn.execute(text("DELETE FROM radar_artifacts WHERE run_id = :r"), {"r": rid})
                conn.execute(text("DELETE FROM metric_values WHERE run_id = :r"), {"r": rid})
                conn.execute(text("DELETE FROM processing_runs WHERE id = :r"), {"r": rid})
            conn.execute(text("INSERT INTO processing_runs (id, status, parameter_hash) "
                              "VALUES (:id, 'completed', :h)"),
                         {"id": rid, "h": hashlib.sha256(f"nisar-anomaly|{rid}".encode()).hexdigest()})
            counts["runs"] += 1

            artifact_id = stable_id("artifact", rid)
            parquet = r["dir"] / "damage_cells.parquet"
            conn.execute(text(
                "INSERT INTO radar_artifacts (id, area_id, run_id, source_id, schema_version, "
                "artifact_version, sha256, private_uri, track, frame, polarizations, "
                "before_acquired_at, after_acquired_at, processing_version, qa_status, safety_tag) VALUES "
                "(:id, :area, :run, :src, '0.1', :ver, :sha, :uri, 151, 72, CAST(:pols AS jsonb), "
                ":before, :after, :pver, 'm1_03_tests_reported', 'restricted_until_review')"),
                {"id": artifact_id, "area": AOI_ID, "run": rid,
                 "src": f"nisar-gcov-{r['maturity'].lower()}-151d72", "ver": rid,
                 "sha": file_sha256(parquet), "uri": parquet.as_posix(), "pols": '["HH", "HV"]',
                 "before": to_dt(r["before"]), "after": to_dt(r["after_first"]),
                 "pver": f"nisar-anomaly (after: {r['maturity']})"})
            counts["artifacts"] += 1

            release = to_dt(r["after_last"]) + RELEASE_DELAY
            rows = []
            for row in tables[rid].to_dict(orient="records"):
                res = classify(row)
                if res is None:
                    continue
                rows.append({"id": stable_id("result", rid, row["h3_r9"]), "area": row["h3_r9"],
                             "art": artifact_id, "cls": res["classification"],
                             "score": res["anomaly_score"], "ev": res["evidence_label"],
                             "reasons": json.dumps(res["reason_codes"]), "release": release})
            if rows:
                conn.execute(text(
                    "INSERT INTO radar_area_results (id, area_id, artifact_id, classification, "
                    "anomaly_score, evidence_label, reason_codes, qa_status, safety_tag, release_at) VALUES "
                    "(:id, :area, :art, :cls, :score, :ev, CAST(:reasons AS jsonb), "
                    "'m1_03_tests_reported', 'restricted_until_review', :release)"), rows)
            counts["results"] += len(rows)

        known_runs = {r["run_id"] for r in runs}
        vrows = [{"id": stable_id("value", v["value_id"]), "vid": v["value_id"], "area": v["area_id"],
                  "run": v["processing_run_id"], "metric": v["metric"], "low": v["low"], "high": v["high"],
                  "unit": v["unit"], "label": v["label"], "src": v["source"][0],
                  "obs": to_dt(v["acquired_at"]), "tag": v["safety_tag"],
                  "release": to_dt(v["release_at"]), "rec": json.dumps(v)}
                 for v in values if v["processing_run_id"] in known_runs]
        conn.execute(text(
            "INSERT INTO metric_values (id, value_id, area_id, run_id, metric, low, high, unit, label, "
            "source_id, observed_at, safety_tag, release_at, record) VALUES (:id, :vid, :area, :run, "
            ":metric, :low, :high, :unit, :label, :src, :obs, :tag, :release, CAST(:rec AS jsonb))"), vrows)
        counts["values"] = len(vrows)
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--replace", action="store_true", help="replace runs that are already loaded")
    args = ap.parse_args(argv)
    sys.path.insert(0, str(ROOT))
    from backend.app.db.base import make_engine

    print(json.dumps(load(make_engine(), args.replace)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
