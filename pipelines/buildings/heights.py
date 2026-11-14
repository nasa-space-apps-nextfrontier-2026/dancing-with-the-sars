"""U-02: building height ranges for the demo box (doc 25, doc 24 section 15).

    python -m pipelines.buildings.heights

Order for every building (3D-GloBFP is not used: its authors are all at Chinese institutions,
which the project rules exclude):
  1. OSM `building:levels` tag (levels x 3 m, plus or minus 10%)
  2. GHSL height from GHS-OBAT (EU JRC, CC BY 4.0): the mean of the 100 m GHS-BUILT-H ANBH grid
     under an Overture footprint, about 2018. Matched to our OSM footprint when the OBAT
     footprint centre lies inside it, else the nearest centre within 10 m.
     GHSL reports a mean absolute error of 2.89 m and a tendency to underestimate, so the range is
     the value minus 3 m to plus 4.5 m. Values at GHSL's 2.5 m floor mean "low-rise, not
     resolved" and get 3 to 7 m.
  3. A default range for the building use.
Floors = height / 3 m, as a low-high range. Every row says where its height came from.
Heights describe the building stock before the war (2018 imagery), not what stands today.

Also adds GHSL's residential / non-residential use and construction epoch where matched; they
help where OSM has only `building=yes`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import shapely
from pyproj import Transformer

from pipelines.buildings.base import DEMO_BOX, METRIC_CRS

STOREY_M = 3.0
OSM_SPREAD = 0.10            # plus or minus 10% around levels x 3 m
GHSL_BELOW_M, GHSL_ABOVE_M = 3.0, 4.5   # MAE 2.89 m, heights tend to be low
GHSL_FLOOR_M = 2.5           # GHSL's lower limit: "not resolved"
GHSL_FLOOR_RANGE = (3.0, 7.0)
MIN_HEIGHT_M = 3.0           # one storey
MATCH_RADIUS_M = 10.0
NEARBY_RADIUS_M = 20.0     # second pass for buildings no OBAT footprint was matched to
DEFAULT_RANGE = {             # metres, used only when neither OSM nor GHSL gives a height
    "residential": (3.0, 12.0), "school": (4.0, 12.0), "clinic": (3.0, 9.0), "hospital": (6.0, 24.0),
    "water": (3.0, 15.0), "power": (3.0, 6.0), "other": (3.0, 9.0), "unknown": (3.0, 9.0),
}
GHSL_USE = {0: "outside_built_up", 1: "residential", 2: "non_residential"}
GHSL_EPOCH = {0: None, 1: "before_1980", 2: "1980_1990", 3: "1990_2000", 4: "2000_2010", 5: "2010_2020"}


def height_range(osm_levels: float | None, ghsl_m: float | None, use: str) -> tuple[float, float, str]:
    """(low, high, source) for one building, in the fixed priority order."""
    if osm_levels is not None and not math.isnan(osm_levels) and osm_levels >= 1:
        mid = osm_levels * STOREY_M
        return max(MIN_HEIGHT_M, mid * (1 - OSM_SPREAD)), max(MIN_HEIGHT_M, mid * (1 + OSM_SPREAD)), "osm"
    if ghsl_m is not None and not math.isnan(ghsl_m):
        if ghsl_m <= GHSL_FLOOR_M:
            return (*GHSL_FLOOR_RANGE, "ghsl")
        return max(MIN_HEIGHT_M, ghsl_m - GHSL_BELOW_M), ghsl_m + GHSL_ABOVE_M, "ghsl"
    return (*DEFAULT_RANGE.get(use, DEFAULT_RANGE["unknown"]), "default")


def _half_up(x: float) -> int:
    return math.floor(x + 0.5)


def floors(low_m: float, high_m: float, osm_levels: float | None = None) -> tuple[int, int]:
    """Floor range. OSM levels are used as tagged (2.5 -> 2 to 3); otherwise height / 3 m."""
    if osm_levels is not None and not math.isnan(osm_levels) and osm_levels >= 1:
        return max(1, math.floor(osm_levels)), max(1, math.ceil(osm_levels))
    lo = max(1, _half_up(low_m / STOREY_M))
    return lo, max(lo, _half_up(high_m / STOREY_M))


def match_obat(buildings_wkb: np.ndarray, obat: pd.DataFrame) -> pd.DataFrame:
    """For each building: mean GHSL height (weighted by OBAT footprint area), majority use, epoch.

    obat columns: lon, lat, height, use, epoch, area. Returns one row per building (NaN if none)."""
    to_m = Transformer.from_crs("EPSG:4326", METRIC_CRS, always_xy=True)
    polys = shapely.transform(shapely.from_wkb(buildings_wkb),
                              lambda xy: np.column_stack(to_m.transform(xy[:, 0], xy[:, 1])))
    x, y = to_m.transform(obat["lon"].to_numpy(), obat["lat"].to_numpy())
    pts = shapely.points(x, y)
    tree = shapely.STRtree(polys)
    pi, bi = tree.query(pts, predicate="within")
    inside = np.zeros(len(pts), dtype=bool)
    inside[pi] = True
    rest = np.flatnonzero(~inside)
    if len(rest):
        (ri, rb), _ = tree.query_nearest(pts[rest], max_distance=MATCH_RADIUS_M, return_distance=True,
                                            all_matches=False)
        pi = np.concatenate([pi, rest[ri]])
        bi = np.concatenate([bi, rb])
    m = obat.iloc[pi][["height", "use", "epoch", "area"]].reset_index(drop=True)
    m["b"] = bi
    m = m[m["height"].notna()]
    m["w"] = m["area"].clip(lower=1.0)
    m["hw"] = m["height"] * m["w"]
    agg = m.groupby("b").agg(hw=("hw", "sum"), w=("w", "sum"), n=("height", "size"),
                             use=("use", lambda s: s.mode().iloc[0]), epoch=("epoch", lambda s: s.mode().iloc[0]))
    out = pd.DataFrame(index=range(len(polys)))
    out["ghsl_height_m"] = (agg["hw"] / agg["w"]).reindex(out.index)
    out["ghsl_matches"] = agg["n"].reindex(out.index).fillna(0).astype(int)
    out["use_ghsl"] = agg["use"].reindex(out.index).map(GHSL_USE)
    out["built_epoch"] = agg["epoch"].reindex(out.index).map(GHSL_EPOCH)
    out["ghsl_match"] = np.where(out["ghsl_matches"] > 0, "footprint", "none")

    # Second pass: small buildings (annexes, sheds) are often merged into a neighbour's Overture
    # footprint. GHSL heights are 100 m grid means, so the nearest GHSL value within 20 m applies.
    todo = np.flatnonzero(out["ghsl_height_m"].isna().to_numpy())
    valid = obat["height"].notna().to_numpy()
    if len(todo) and valid.any():
        vidx = np.flatnonzero(valid)
        (ti, pj), _ = shapely.STRtree(pts[vidx]).query_nearest(
            polys[todo], max_distance=NEARBY_RADIUS_M, return_distance=True, all_matches=False)
        hit, src = todo[ti], obat.iloc[vidx[pj]]
        out.loc[hit, "ghsl_height_m"] = src["height"].to_numpy()
        out.loc[hit, "use_ghsl"] = src["use"].map(GHSL_USE).to_numpy()
        out.loc[hit, "built_epoch"] = src["epoch"].map(GHSL_EPOCH).to_numpy()
        out.loc[hit, "ghsl_match"] = "nearby"
    return out


def build(base: pd.DataFrame, obat: pd.DataFrame) -> pd.DataFrame:
    m = match_obat(base["geom"].to_numpy(), obat)
    rows = []
    for lv, gh, use in zip(base["osm_levels"], m["ghsl_height_m"], base["use"], strict=True):
        lo, hi, src = height_range(lv, gh, use)
        fl, fh = floors(lo, hi, lv if src == "osm" else None)
        rows.append((round(lo, 1), round(hi, 1), src, fl, fh))
    h = pd.DataFrame(rows, columns=["height_low_m", "height_high_m", "height_source", "floors_low", "floors_high"])
    return pd.concat([base[["building_id", "h3_r9", "h3_r8", "use", "footprint_m2"]].reset_index(drop=True), h,
                      m[["ghsl_height_m", "ghsl_match", "ghsl_matches", "use_ghsl", "built_epoch"]]], axis=1)


def load_obat(path: Path, box: tuple[float, float, float, float] = DEMO_BOX, margin: float = 0.01) -> pd.DataFrame:
    d = pd.read_csv(path, usecols=["lon", "lat", "height", "use", "epoch", "area"])
    w, s, e, n = box
    return d[d["lon"].between(w - margin, e + margin) & d["lat"].between(s - margin, n + margin)].reset_index(drop=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(base_path: Path, obat_csv: Path, out_path: Path, manifest_path: Path) -> dict:
    base = pq.read_table(base_path).to_pandas()
    obat = load_obat(obat_csv)
    rows = build(base, obat)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(rows, preserve_index=False), out_path)
    share = rows["height_source"].value_counts(normalize=True).round(4).to_dict()
    manifest = {
        "kind": "buildings_height", "task": "U-02", "synthetic": False,
        "built_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "inputs": {
            "buildings_base": {"file": str(base_path).replace("\\", "/"), "sha256": sha256(base_path)},
            "ghs_obat": {"file": obat_csv.name, "sha256": sha256(obat_csv), "rows_in_box": len(obat)},
        },
        "sources": {
            "osm": "OpenStreetMap building:levels (ODbL 1.0, (c) OpenStreetMap contributors)",
            "ghsl": ("GHS-OBAT R2024A, European Commission JRC, CC BY 4.0, doi:10.2905/"
                     "f41a22f1-5741-4c41-86eb-6384654f6927. Height = GHS-BUILT-H ANBH (100 m, ~2018) under "
                     "Overture footprints"),
            "default": "Fixed range by building use (DEFAULT_RANGE in pipelines/buildings/heights.py)",
            "not_used": "3D-GloBFP (all authors at Chinese institutions; excluded by project rule)",
        },
        "method": {"order": ["osm", "ghsl", "default"], "storey_m": STOREY_M, "osm_spread": OSM_SPREAD,
                   "ghsl_below_m": GHSL_BELOW_M, "ghsl_above_m": GHSL_ABOVE_M, "ghsl_floor_m": GHSL_FLOOR_M,
                   "ghsl_floor_range_m": list(GHSL_FLOOR_RANGE), "match_radius_m": MATCH_RADIUS_M,
                   "nearby_radius_m": NEARBY_RADIUS_M,
                   "default_range_m": {k: list(v) for k, v in DEFAULT_RANGE.items()}},
        "output": str(out_path).replace("\\", "/"), "output_sha256": sha256(out_path),
        "buildings": len(rows),
        "height_source_share": share,
        "ghsl_matched": rows["ghsl_match"].value_counts().to_dict(),
        "ghsl_at_floor": int((rows["ghsl_height_m"] <= GHSL_FLOOR_M).sum()),
        "use_ghsl_counts": rows["use_ghsl"].fillna("not_matched").value_counts().to_dict(),
        "height_range_m": {"low_median": float(rows["height_low_m"].median()),
                           "high_median": float(rows["height_high_m"].median())},
        "limits": [
            "Heights describe the building stock around 2018, before the war; they are not damage results.",
            "GHSL heights are 100 m grid means: a tall building among low ones is underestimated.",
            (f"{(rows['ghsl_height_m'] <= GHSL_FLOOR_M).mean():.0%} of buildings have a GHSL value at the "
             "2.5 m floor (not resolved); those get 3-7 m."),
            ("First check (14 Nov 2026) on 414 OSM-tagged buildings: GHSL within 3 m for 39%, range holds the "
             "tagged height for 51%; good for 1-2 storeys (78%), poor above (22-32%), towers about 11 m too low. "
             "These ranges are not final: U-03 calibrates them (docs/progress/BUILDING_HEIGHT_CHECK.md)."),
        ],
        "rebuild": "python -m pipelines.buildings.heights",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", type=Path, default=Path("data/local/buildings_base.parquet"))
    ap.add_argument("--obat", type=Path,
                    default=Path("data/raw/ghsl/obat_lbn/GHS_OBAT_CSV_LBN_E2020_R2024A_V1_0.csv"))
    ap.add_argument("--out", type=Path, default=Path("data/local/buildings_height.parquet"))
    ap.add_argument("--manifest", type=Path, default=Path("data/manifests/buildings_height.json"))
    args = ap.parse_args(argv)
    m = run(args.base, args.obat, args.out, args.manifest)
    print(json.dumps({k: m[k] for k in ("buildings", "height_source_share", "ghsl_matched", "ghsl_at_floor",
                                        "use_ghsl_counts", "height_range_m")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
