"""M1-02: tier A run — crops -> QA checks -> cell features -> anomaly model -> damage table.

    python -m pipelines.radar.nisar.process --buildings data/raw/hotosm/lbn_buildings.parquet

Outputs (all git-ignored, private):
  data/private/nisar/model/damage_cells.parquet   one row per built-up H3 r9 cell
  data/private/nisar/model/run.json               QA checks, model settings, hold-out results
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import geopandas as gpd
import h5py
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import binary_dilation

from .features import (
    cell_table,
    destripe,
    mean_power,
    pixel_cells,
    pixel_features,
    read_grid,
    to_db,
)
from .model import MODEL_VERSION, fit_and_score, holdout_false_alarms, quiet_cells

CROP_INDEX = Path("data/manifests/nisar_crops.json")
OUT_DIR = Path("data/private/nisar/model")
MIN_BEFORE_DATES = 3
MIN_AFTER_DATES = 2
INCIDENCE_HEIGHT_M = 500.0
BUILT_BUFFER_M = 30.0
MIN_BUILT_DENSITY = 0.25  # share of a cell covered by buildings + 30 m; below = not assessed
QUIET_RADIUS_KM = 2.0
EVENT_START, EVENT_END = "2026-01-19", "2026-06-24"  # between the before and after passes
UCDP_MAX_PREC = 1  # 1 = exact location in the UCDP codebook


def load_ucdp_events(path: Path, start: str = EVENT_START, end: str = EVENT_END) -> pd.DataFrame:
    """Lebanon UCDP events with exact locations between the before and after passes."""
    df = pd.read_csv(path, low_memory=False)
    df = df[df["country"].astype(str).str.contains("Lebanon", case=False)]
    df = df[df["where_prec"] <= UCDP_MAX_PREC]
    when = pd.to_datetime(df["date_start"])
    df = df[(when >= start) & (when <= end)]
    return df.rename(columns={"latitude": "lat", "longitude": "lon"})[["lat", "lon", "date_start"]]
WATER_HV_DB = -20.5  # valley between water (~-23 dB) and land (~-15 dB) in mean HV, 14 Nov 2026
WATER_DILATE_PX = 2  # 40 m extra along shores (mixed land/water pixels)


def load_terrain_mask(ref: str) -> np.ndarray:
    """Layover, shadow and steep-slope mask from terrain.py (built on first use)."""
    from .terrain import OUT as TERRAIN_TIF
    from .terrain import terrain_mask

    if TERRAIN_TIF.exists():
        m, _, _ = read_grid(TERRAIN_TIF)
        return m.astype(bool)
    raw = min(glob.glob("data/raw/nisar/*GCOV*.h5"))
    return terrain_mask(raw, ref)[0]


def water_mask(index: dict[str, Any]) -> np.ndarray:
    """Water from mean HV over every cropped date (water is dark and stable in HV)."""
    hv = [next(o["path"] for o in v["outputs"] if o["term"] == "HVHV") for v in index["crops"].values()]
    mean_hv, _ = mean_power(hv)
    water = to_db(mean_hv) < WATER_HV_DB
    return binary_dilation(water, iterations=WATER_DILATE_PX)


def tier_paths(index: dict[str, Any], tier: str, term: str) -> list[tuple[str, str, str]]:
    rows = []
    for scene, v in index["crops"].items():
        if v["tier"] == tier:
            path = next(o["path"] for o in v["outputs"] if o["term"] == term)
            rows.append((v["date"], scene, path))
    return sorted(rows)


def built_mask(buildings: Path, ref_path: str) -> np.ndarray:
    with rasterio.open(ref_path) as r:
        transform, shape, crs, bounds = r.transform, r.shape, r.crs, r.bounds
    gdf = gpd.read_parquet(buildings)
    gdf = gdf.to_crs(crs).cx[bounds.left:bounds.right, bounds.bottom:bounds.top]
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
    shapes = gdf.geometry.buffer(BUILT_BUFFER_M)  # plan: OSM buildings + 30 m
    return rasterize(((g, 1) for g in shapes), out_shape=shape, transform=transform,
                     fill=0, dtype="uint8", all_touched=False).astype(bool)


def validity(index: dict[str, Any], scenes: list[str], shape: tuple[int, int]) -> np.ndarray:
    """GCOV mask: 0 = partially focused / invalid, 255 = outside; anything else is valid."""
    ok = np.ones(shape, dtype=bool)
    for scene in scenes:
        mpath = next((o["path"] for o in index["crops"][scene]["outputs"] if o["term"] == "mask"), None)
        if mpath:
            m, _, _ = read_grid(mpath)
            ok &= (m > 0) & (m < 255)
    return ok


def incidence_grid(raw_h5: str, ref_path: str) -> np.ndarray | None:
    """Incidence angle at ~500 m height from the radarGrid cube, interpolated to the crop grid."""
    with h5py.File(raw_h5) as h:
        rg = h["science/LSAR/GCOV/metadata/radarGrid"]
        heights = rg["heightAboveEllipsoid"][()]
        k = int(np.argmin(np.abs(heights - INCIDENCE_HEIGHT_M)))
        inc = rg["incidenceAngle"][k]
        x, y = rg["xCoordinates"][()], rg["yCoordinates"][()]
    if y[0] > y[-1]:
        y, inc = y[::-1], inc[::-1]
    f = RegularGridInterpolator((y, x), inc, bounds_error=False, fill_value=np.nan)
    with rasterio.open(ref_path) as r:
        rows, cols = np.mgrid[0:r.height, 0:r.width]
        xs, ys = rasterio.transform.xy(r.transform, rows.ravel(), cols.ravel(), offset="center")
    return f(np.column_stack([ys, xs])).reshape(rows.shape).astype("float32")


def version_check(index: dict[str, Any], built: np.ndarray, valid: np.ndarray) -> dict[str, Any]:
    """Per-date median dB on built-up and on all valid pixels, grouped by product maturity."""
    rows = []
    for scene, v in sorted(index["crops"].items(), key=lambda kv: kv[1]["date"]):
        row = {"date": v["date"], "maturity": v["maturity"], "crid": v["crid"]}
        for term in ("HHHH", "HVHV"):
            a, _, _ = read_grid(next(o["path"] for o in v["outputs"] if o["term"] == term))
            db = to_db(a)
            row[f"{term}_built_db"] = float(np.nanmedian(db[built & valid]))
            row[f"{term}_all_db"] = float(np.nanmedian(db[valid]))
        rows.append(row)
    df = pd.DataFrame(rows)
    out: dict[str, Any] = {"per_date": df.to_dict(orient="records")}
    for col in [c for c in df.columns if c.endswith("_db")]:
        g = df.groupby("maturity")[col]
        out[col] = {"mean_by_maturity": g.mean().round(2).to_dict(),
                    "spread_within_maturity_db": g.agg(lambda s: s.max() - s.min()).round(2).to_dict()}
    return out


def banding_check(d_hh: np.ndarray, valid: np.ndarray) -> dict[str, float]:
    """Column- and row-wise median of the HH change; large swings suggest stripes or ramps."""
    d = np.where(valid, d_hh, np.nan)
    col = np.nanmedian(d, axis=0)
    row = np.nanmedian(d, axis=1)
    return {"column_median_range_db": float(np.nanpercentile(col, 95) - np.nanpercentile(col, 5)),
            "row_median_range_db": float(np.nanpercentile(row, 95) - np.nanpercentile(row, 5)),
            "overall_median_db": float(np.nanmedian(d))}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--buildings", type=Path, required=True)
    ap.add_argument("--events", type=Path, default=None,
                    help="UCDP candidate GED CSV, used to pick quiet training cells")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--method", choices=["isolation_forest", "zscore"], default="isolation_forest")
    ap.add_argument("--after-date", default=None,
                    help="time-slider run: one later pass compared with the June-July baseline")
    args = ap.parse_args(argv)

    index = json.loads(CROP_INDEX.read_text(encoding="utf-8"))
    terms = ("HHHH", "HVHV")
    if args.after_date:
        before = {t: tier_paths(index, "A-after", t) for t in terms}
        after = {t: [r for r in tier_paths(index, "B", t) if r[0] == args.after_date] for t in terms}
        if not after["HHHH"]:
            raise SystemExit(f"No tier B pass on {args.after_date}")
        out_dir = OUT_DIR / "slider" / args.after_date
        min_before, min_after = 2, 1
        event_window = (before["HHHH"][-1][0], args.after_date)
    else:
        before = {t: tier_paths(index, "A-before", t) for t in terms}
        after = {t: tier_paths(index, "A-after", t) for t in terms}
        out_dir = OUT_DIR
        min_before, min_after = MIN_BEFORE_DATES, MIN_AFTER_DATES
        event_window = (EVENT_START, EVENT_END)
    ref = before["HHHH"][0][2]
    print(f"before dates: {[d for d, _, _ in before['HHHH']]}")
    print(f"after dates:  {[d for d, _, _ in after['HHHH']]}")

    scenes = [s for _, s, _ in before["HHHH"] + after["HHHH"]]
    _, transform, crs = read_grid(ref)
    bh, bh_n = mean_power([p for _, _, p in before["HHHH"]])
    bv, _ = mean_power([p for _, _, p in before["HVHV"]])
    ah, ah_n = mean_power([p for _, _, p in after["HHHH"]])
    av, _ = mean_power([p for _, _, p in after["HVHV"]])

    built = built_mask(args.buildings, ref)
    valid = validity(index, scenes, bh.shape) & (bh_n >= min_before) & (ah_n >= min_after)
    water = water_mask(index)
    terrain = load_terrain_mask(ref)
    valid &= ~water & ~terrain
    print(f"terrain mask (layover, shadow, slope > 25 deg): {terrain.mean():.1%} of the crop")
    print(f"built-up pixels: {int(built.sum()):,} ({built.mean():.1%} of the crop)")
    print(f"water mask: {water.mean():.1%} of the crop; built-up pixels on water: {int((built & water).sum()):,}")

    qa = {"version_check": None if args.after_date else version_check(index, built, valid),
          "terrain_masked_share": float(terrain.mean()),
          "water": {"threshold_mean_hv_db": WATER_HV_DB, "dilation_px": WATER_DILATE_PX,
                    "share_of_crop": float(water.mean()),
                    "built_pixels_masked": int((built & water).sum())}}
    feats = pixel_features(bh, bv, ah, av)
    feats["valid"] &= valid
    sample = feats["valid"]  # all valid land pixels: built-up alone left edge stripes (14 Nov)
    qa["banding_before_correction"] = banding_check(feats["d_hh"], sample)
    qa["destripe"] = {}
    for name in ("d_hh", "d_hv", "d_pol"):
        feats[name], qa["destripe"][name] = destripe(feats[name], sample)
    qa["banding_after_correction"] = banding_check(feats["d_hh"], sample)

    raw = sorted(glob.glob("data/raw/nisar/*.h5"))
    incidence = incidence_grid(raw[0], ref) if raw else None
    pixel_area = abs(transform.a * transform.e)
    cells_px = pixel_cells(transform, bh.shape, crs, built)
    cells = cell_table(cells_px, built, feats, pixel_area, incidence)
    print(f"built-up H3 r9 cells: {len(cells):,} (low coverage: {int(cells['low_coverage'].sum()):,})")

    # Sparse cells (isolated houses): the 30 m buffer then samples mostly fields and slopes,
    # which caused most false alarms in the 14 Nov top-20 eye check. Not assessed -> Unknown.
    cells["sparse_cell"] = cells["built_density"] < MIN_BUILT_DENSITY
    coverage_only = cells["low_coverage"].copy()
    cells["low_coverage"] = coverage_only | cells["sparse_cell"]
    print(f"sparse cells not assessed: {int(cells['sparse_cell'].sum()):,}")

    # Quiet controls from UCDP (CC BY 4.0). ACLED terms forbid training/testing models on its
    # data, and Insecurity Insight coordinates are censored. Without --events, all assessed
    # cells are used (assumes damage is a minority).
    if args.events:
        events = load_ucdp_events(args.events, *event_window)
        quiet = quiet_cells(cells, events, radius_km=QUIET_RADIUS_KM)
        quiet_note = (f"UCDP candidate events (where_prec<={UCDP_MAX_PREC}, {event_window[0]}..{event_window[1]}, "
                      f"n={len(events)}); no event within {QUIET_RADIUS_KM} km")
    else:
        quiet = np.ones(len(cells), dtype=bool)
        quiet_note = "all assessed cells (no event points given)"
    print(f"quiet cells: {int((quiet & ~cells['low_coverage']).sum()):,} of "
          f"{int((~cells['low_coverage']).sum()):,} assessed")
    out, fit = fit_and_score(cells, quiet, seed=args.seed, method=args.method)
    fa = holdout_false_alarms(out, fit)
    out["low_coverage"] = coverage_only.to_numpy()
    out.loc[out["sparse_cell"] & ~out["low_coverage"], "reasons"] = "sparse_buildings"

    run_key = json.dumps({"scenes": scenes, "seed": args.seed, "method": args.method,
                          "model": MODEL_VERSION}, sort_keys=True)
    run_id = hashlib.sha256(run_key.encode()).hexdigest()[:16]
    out["run_id"] = run_id
    out["pair_before"] = f"{before['HHHH'][0][0]}..{before['HHHH'][-1][0]}"
    out["pair_after"] = f"{after['HHHH'][0][0]}..{after['HHHH'][-1][0]}"
    maturities = {index["crops"][s]["maturity"] for s in scenes}
    out["version_confounded"] = len(maturities) > 1
    out["synthetic"] = False

    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_parquet(out_dir / "damage_cells.parquet", index=False)
    summary = {
        "schema_version": "0.1", "kind": "nisar_damage_run", "run_id": run_id,
        "created_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "model_version": MODEL_VERSION, "method": fit.method, "features": fit.features,
        "seed": fit.seed, "thresholds": fit.thresholds, "n_train": fit.n_train,
        "n_holdout": fit.n_holdout, "tail_reliable": fit.tail_reliable,
        "quiet_controls": quiet_note,
        "holdout_false_alarms": fa, "qa": qa,
        "class_counts": out["damage_class"].value_counts().to_dict(),
        "limits": [f"product maturities in this pair: {sorted(maturities)}",
                   "no water/shadow/slope mask yet (built-up only, GCOV validity mask applied)",
                   "OSM building coverage limits", "candidates only, not confirmed damage"],
    }
    (out_dir / "run.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("run_id", "n_train", "n_holdout", "class_counts")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
