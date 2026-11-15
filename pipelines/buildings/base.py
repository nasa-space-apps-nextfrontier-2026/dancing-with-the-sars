"""U-01: building footprints and types for the demo box (doc 25).

    python -m pipelines.buildings.base --input data/raw/hotosm/lbn_buildings.parquet

Reads the HOTOSM Lebanon buildings export (GeoParquet, OSM, ODbL), keeps polygon footprints whose
centre lies in the demo box, measures each footprint in a metric CRS (UTM 36N, never degrees), maps
the OSM `building` tag to a coarse use, and finds the H3 r9 and r8 cell of the centre.

Honest defaults:
- 97% of OSM buildings here are tagged only `building=yes`; their use is `unknown`, not residential.
- OSM tags such as `ruins` or `destroyed` are kept in `osm_condition_tag` as mapper reports of
  unknown date. They are not damage evidence.
- Points (buildings mapped without an outline) and empty or broken shapes are dropped and counted.

Outputs (outside Git): data/local/buildings_base.parquet, and the small manifest
data/manifests/buildings_base.json (counts only, no coordinates).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import h3
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import shapely
from pyproj import Transformer

DEMO_BOX = (35.0, 33.0, 36.0, 33.6)  # west, south, east, north (WGS84)
METRIC_CRS = "EPSG:32636"  # UTM 36N covers 30-36 E
USES = ("residential", "school", "clinic", "hospital", "water", "power", "other", "unknown")
FACILITY_USES = {"school", "clinic", "hospital", "water", "power"}

USE_BY_TAG = {
    **dict.fromkeys(("house", "apartments", "residential", "detached", "semidetached_house", "terrace",
                     "bungalow", "dormitory", "hut", "cabin", "farm"), "residential"),
    **dict.fromkeys(("school", "education", "kindergarten", "college", "university"), "school"),
    **dict.fromkeys(("clinic", "healthcare"), "clinic"),
    "hospital": "hospital",
    **dict.fromkeys(("water_tower", "pumping_station", "reservoir_covered"), "water"),
    **dict.fromkeys(("power_substation", "transformer_tower", "power"), "power"),
    # untyped, or a state rather than a type
    **dict.fromkeys(("yes", "ruins", "destroyed", "damage", "demolished", "construction", "roof"), "unknown"),
}
CONDITION_TAGS = {"ruins", "destroyed", "damage", "demolished", "construction"}


def use_of(tag: str | None) -> str:
    if not tag:
        return "unknown"
    return USE_BY_TAG.get(tag.strip().lower(), "other")


def parse_levels(value: str | None) -> float | None:
    """OSM building:levels as a number; junk or negative values become None."""
    if value is None:
        return None
    try:
        levels = float(str(value).strip().replace(",", "."))
    except ValueError:
        return None
    return levels if 0 <= levels <= 200 else None


def _polygonal(g: shapely.Geometry) -> shapely.Geometry:
    if shapely.get_type_id(g) in (3, 6):
        return g
    parts = [p for p in shapely.get_parts(g) if shapely.get_type_id(p) in (3, 6)]
    return shapely.union_all(parts) if parts else shapely.Polygon()


def build(table: pd.DataFrame, box: tuple[float, float, float, float] = DEMO_BOX) -> tuple[pd.DataFrame, dict]:
    """table: columns id, building, building_levels, geom (WKB, WGS84). Returns rows and counts."""
    counts = {"input_rows": len(table)}
    geoms = shapely.from_wkb(table["geom"].to_numpy())
    poly = np.isin(shapely.get_type_id(geoms), (3, 6))  # Polygon, MultiPolygon
    counts["dropped_points_or_lines"] = int((~poly).sum())
    df = table.loc[poly].reset_index(drop=True)
    geoms = geoms[poly]

    broken = np.flatnonzero(~shapely.is_valid(geoms))
    for i in broken:  # repair self-crossing outlines; keep only the polygon parts
        geoms[i] = _polygonal(shapely.make_valid(geoms[i]))
    counts["repaired_outlines"] = len(broken)
    to_m = Transformer.from_crs("EPSG:4326", METRIC_CRS, always_xy=True)
    metric = shapely.transform(geoms, lambda xy: np.column_stack(to_m.transform(xy[:, 0], xy[:, 1])))
    area = shapely.area(metric)
    keep = ~shapely.is_empty(geoms) & (area > 0)
    counts["dropped_broken_or_empty"] = int((~keep).sum())
    df, geoms, area = df.loc[keep].reset_index(drop=True), geoms[keep], area[keep]

    centre = shapely.centroid(geoms)
    lon, lat = shapely.get_x(centre), shapely.get_y(centre)
    w, s, e, n = box
    inside = (lon >= w) & (lon <= e) & (lat >= s) & (lat <= n)
    counts["dropped_outside_box"] = int((~inside).sum())
    df, geoms, area, lon, lat = df.loc[inside].reset_index(drop=True), geoms[inside], area[inside], lon[inside], lat[inside]

    dup = df["id"].duplicated(keep="first").to_numpy()
    counts["dropped_duplicate_ids"] = int(dup.sum())
    df, geoms, area, lon, lat = df.loc[~dup].reset_index(drop=True), geoms[~dup], area[~dup], lon[~dup], lat[~dup]

    r9 = [h3.latlng_to_cell(y, x, 9) for x, y in zip(lon, lat, strict=True)]
    tags = df["building"].astype("string").str.strip().str.lower()
    out = pd.DataFrame({
        "building_id": df["id"].astype(str),
        "osm_building_tag": tags.fillna("").to_numpy(),
        "use": [use_of(t) for t in tags.fillna("")],
        "osm_condition_tag": [t if t in CONDITION_TAGS else None for t in tags.fillna("")],
        "osm_levels": [parse_levels(v) for v in df["building_levels"]],
        "footprint_m2": np.round(area, 1),
        "h3_r9": r9,
        "h3_r8": [h3.cell_to_parent(c, 8) for c in r9],
        "geom": shapely.to_wkb(geoms),
    })
    out["facility_flag"] = out["use"].isin(FACILITY_USES)
    counts["buildings"] = len(out)
    return out, counts


def run(src: Path, out_path: Path, manifest_path: Path) -> dict:
    cols = ["id", "building", "building_levels", "geom"]
    table = pq.read_table(src, columns=cols).to_pandas()
    rows, counts = build(table)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(rows, preserve_index=False), out_path)
    sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    manifest = {
        "kind": "buildings_base", "task": "U-01", "synthetic": False,
        "source": "OpenStreetMap via HOTOSM export (HDX hotosm_lbn_buildings)",
        "licence": "ODbL 1.0; attribution: (c) OpenStreetMap contributors",
        "source_file": src.name,
        "source_file_date": dt.datetime.fromtimestamp(src.stat().st_mtime, dt.UTC).strftime("%Y-%m-%d"),
        "built_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "demo_box_wgs84": list(DEMO_BOX), "area_crs": METRIC_CRS,
        "output": str(out_path).replace("\\", "/"), "output_sha256": sha,
        "counts": counts,
        "use_counts": {u: int((rows["use"] == u).sum()) for u in USES},
        "facility_buildings": int(rows["facility_flag"].sum()),
        "with_osm_levels": int(rows["osm_levels"].notna().sum()),
        "with_condition_tag": int(rows["osm_condition_tag"].notna().sum()),
        "footprint_m2": {q: round(float(rows["footprint_m2"].quantile(p)), 1)
                         for q, p in (("p10", 0.1), ("median", 0.5), ("p90", 0.9))},
        "limits": [
            "Use comes from the OSM building tag only; most buildings are untyped (use unknown).",
            "Facility flags cover buildings tagged as such; facilities mapped as points are not here.",
            "osm_condition_tag values are mapper reports of unknown date, not damage evidence.",
            "OSM completeness in the demo box has not been measured against another source.",
        ],
        "rebuild": "python -m pipelines.buildings.base --input data/raw/hotosm/lbn_buildings.parquet",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, default=Path("data/raw/hotosm/lbn_buildings.parquet"))
    ap.add_argument("--out", type=Path, default=Path("data/local/buildings_base.parquet"))
    ap.add_argument("--manifest", type=Path, default=Path("data/manifests/buildings_base.json"))
    args = ap.parse_args(argv)
    m = run(args.input, args.out, args.manifest)
    print(json.dumps({"counts": m["counts"], "use_counts": m["use_counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
