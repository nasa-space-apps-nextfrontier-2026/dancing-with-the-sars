"""Load Kisara's K-03 facility file into PostGIS (one transaction; replaces the previous load).

    python -m scripts.load_facilities [--facilities data/local/facilities.csv]
                                      [--boundaries data/local/boundaries.geojson]

Keeps only clinics, hospitals, schools, water and power sites whose point lies inside the Lebanon
boundary (K-01): the demo box also covers part of northern Israel, while buildings and population
cover Lebanon only. Excluded types (military, police, prison) are never stored, and names are not
stored. A failure leaves the database unchanged.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import h3
from shapely.geometry import Point, shape
from shapely.ops import unary_union
from sqlalchemy import text

TYPES = ("clinic", "hospital", "school", "water", "power")


def _ts(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    t = dt.datetime.fromisoformat(value)
    return t if t.tzinfo else t.replace(tzinfo=dt.UTC)


def read(facilities: Path, boundaries: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    for path in (facilities, boundaries):
        if not path.exists():
            raise SystemExit(f"Missing {path}. It comes from Kisara's K-01/K-03 scripts (never from Git).")
    lebanon = unary_union([shape(f["geometry"]) for f in
                           json.loads(boundaries.read_text(encoding="utf-8"))["features"]])
    rows, outside, excluded = [], 0, 0
    with facilities.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            kind = (r.get("type") or "").strip().lower()
            if kind not in TYPES:
                excluded += 1
                continue
            lat, lon = float(r["lat"]), float(r["lon"])
            if not lebanon.contains(Point(lon, lat)):
                outside += 1
                continue
            r9 = h3.latlng_to_cell(lat, lon, 9)
            rows.append({"id": r["facility_id"], "type": kind, "r9": r9, "r8": h3.cell_to_parent(r9, 8),
                         "ts": _ts(r.get("osm_timestamp")), "lon": lon, "lat": lat})
    by_type = {t: sum(1 for x in rows if x["type"] == t) for t in TYPES}
    return rows, {"loaded": len(rows), "by_type": by_type, "outside_lebanon": outside,
                  "excluded_type": excluded}


def load(engine: Any, rows: list[dict[str, Any]], counts: dict[str, Any]) -> dict[str, Any]:
    run_id = hashlib.sha256(json.dumps(sorted(r["id"] for r in rows)).encode()).hexdigest()[:16]
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM facilities"))
        conn.execute(text("DELETE FROM facility_runs"))
        if rows:
            conn.execute(text(
                "INSERT INTO facilities (facility_id, type, h3_r9, h3_r8, osm_timestamp, geom) "
                "VALUES (:id, :type, :r9, :r8, :ts, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))"), rows)
        conn.execute(text("INSERT INTO facility_runs (run_id, loaded_at, counts) "
                          "VALUES (:r, :l, CAST(:c AS jsonb))"),
                     {"r": run_id, "l": dt.datetime.now(dt.UTC), "c": json.dumps(counts)})
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--facilities", type=Path, default=Path("data/local/facilities.csv"))
    ap.add_argument("--boundaries", type=Path, default=Path("data/local/boundaries.geojson"))
    args = ap.parse_args(argv)
    from backend.app.db.base import make_engine

    rows, counts = read(args.facilities, args.boundaries)
    print(json.dumps(load(make_engine(), rows, counts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
