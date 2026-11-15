"""U-03: check building heights against known heights and calibrate the GHSL ranges (doc 25).

    python -m pipelines.buildings.height_check

Reference: buildings whose OSM `building:levels` tag is known (height = levels x 3 m). GHSL is
compared with them; the reference never comes from GHSL itself.

Calibration: for each band of GHSL height (and, where at least MIN_CELL references exist, footprint
size), the reference heights give a middle value (median) and a range (quantiles). Scored with
5-fold cross-validation grouped by H3 r8 area, so a building is never scored by a table fitted on
its own neighbourhood. The variant with the best single-value accuracy among those whose range holds
the reference at least 70% of the time on held-out areas is kept (narrower, then simpler, on ties); the final table is then fitted on all references.

Writes data/manifests/buildings_height_calibration.json (table and scores, no coordinates).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

STOREY_M = 3.0
GHSL_EDGES = [0.0, 2.5, 4.0, 6.0, 9.0, 13.0, 1000.0]
FOOT_EDGES = [0.0, 150.0, 1e12]
MIN_CELL = 15            # fewer references than this in a (GHSL, footprint) cell -> use the GHSL band
TARGET = 0.70
FOLDS = 5
VARIANTS = [  # (low quantile, high quantile, use footprint)
    (0.15, 0.85, False), (0.15, 0.85, True), (0.10, 0.90, False), (0.10, 0.90, True),
    (0.05, 0.95, False), (0.05, 0.95, True),
]


def references(base: pd.DataFrame, heights: pd.DataFrame) -> pd.DataFrame:
    """Buildings with a known OSM level count and a GHSL value."""
    df = heights.merge(base[["building_id", "osm_levels"]], on="building_id")
    df = df[df["osm_levels"].ge(1) & df["ghsl_height_m"].notna()].copy()
    df["ref_m"] = df["osm_levels"] * STOREY_M
    return df.reset_index(drop=True)


def fold_of(area: str) -> int:
    return int(hashlib.sha256(area.encode()).hexdigest(), 16) % FOLDS


def _band(values: np.ndarray, edges: list[float]) -> np.ndarray:
    return np.clip(np.searchsorted(edges, values, side="left") - 1, 0, len(edges) - 2)


def fit(df: pd.DataFrame, q_lo: float, q_hi: float, use_footprint: bool) -> list[dict]:
    g = _band(df["ghsl_height_m"].to_numpy(), GHSL_EDGES)
    f = _band(df["footprint_m2"].to_numpy(), FOOT_EDGES) if use_footprint else np.zeros(len(df), int)
    table = []
    for gi in range(len(GHSL_EDGES) - 1):
        in_g = g == gi
        if not in_g.any():
            continue
        for fi in range(len(FOOT_EDGES) - 1 if use_footprint else 1):
            sel = in_g & (f == fi)
            if sel.sum() < MIN_CELL:
                sel = in_g  # not enough: the whole GHSL band
            ref = df["ref_m"].to_numpy()[sel]
            table.append({
                "ghsl_from_m": GHSL_EDGES[gi], "ghsl_to_m": GHSL_EDGES[gi + 1],
                "footprint_from_m2": FOOT_EDGES[fi] if use_footprint else 0.0,
                "footprint_to_m2": FOOT_EDGES[fi + 1] if use_footprint else FOOT_EDGES[-1],
                "n": int(sel.sum()), "mid_m": float(np.median(ref)),
                "low_m": float(max(STOREY_M, np.quantile(ref, q_lo))), "high_m": float(np.quantile(ref, q_hi)),
            })
    return table


def predict(table: list[dict], ghsl_m: np.ndarray, footprint_m2: np.ndarray) -> np.ndarray:
    """(n, 3) array of mid, low, high; NaN where no row applies."""
    out = np.full((len(ghsl_m), 3), np.nan)
    for row in table:
        sel = ((ghsl_m > row["ghsl_from_m"]) | (row["ghsl_from_m"] == 0.0)) & (ghsl_m <= row["ghsl_to_m"]) & \
              (footprint_m2 >= row["footprint_from_m2"]) & (footprint_m2 < row["footprint_to_m2"])
        out[sel] = (row["mid_m"], row["low_m"], row["high_m"])
    # values above the last edge use the top band
    return out


def scores(ref: np.ndarray, mid: np.ndarray, low: np.ndarray, high: np.ndarray) -> dict:
    err = mid - ref
    return {"n": len(ref), "within_one_storey": round(float(np.mean(np.abs(err) <= STOREY_M)), 3),
            "mean_abs_error_m": round(float(np.mean(np.abs(err))), 2), "bias_m": round(float(np.mean(err)), 2),
            "range_holds_reference": round(float(np.mean((ref >= low) & (ref <= high))), 3),
            "mean_range_width_m": round(float(np.mean(high - low)), 1)}


def cross_validate(df: pd.DataFrame, q_lo: float, q_hi: float, use_footprint: bool) -> pd.DataFrame:
    folds = df["h3_r8"].map(fold_of).to_numpy()
    pred = np.full((len(df), 3), np.nan)
    for k in range(FOLDS):
        test = folds == k
        if not test.any():
            continue
        table = fit(df[~test], q_lo, q_hi, use_footprint)
        pred[test] = predict(table, df["ghsl_height_m"].to_numpy()[test], df["footprint_m2"].to_numpy()[test])
    out = df.copy()
    out["mid"], out["low"], out["high"] = pred[:, 0], pred[:, 1], pred[:, 2]
    return out


def by_levels(df: pd.DataFrame, mid: str, low: str, high: str) -> dict:
    bands = pd.cut(df["osm_levels"], [0, 2, 4, 8, 1000], labels=["1-2", "3-4", "5-8", "9+"])
    return {str(b): scores(g["ref_m"].to_numpy(), g[mid].to_numpy(), g[low].to_numpy(), g[high].to_numpy())
            for b, g in df.groupby(bands, observed=True)}


def run(base_path: Path, heights_path: Path, out_path: Path) -> dict:
    base = pq.read_table(base_path, columns=["building_id", "osm_levels"]).to_pandas()
    heights = pq.read_table(heights_path).to_pandas()
    df = references(base, heights)

    # Before: the raw GHSL value and the U-02 ranges (minus 3 m to plus 4.5 m)
    from pipelines.buildings.heights import height_range
    raw = np.array([height_range(None, g, "unknown")[:2] for g in df["ghsl_height_m"]])
    df["raw_mid"], df["raw_low"], df["raw_high"] = df["ghsl_height_m"], raw[:, 0], raw[:, 1]
    before = scores(df["ref_m"].to_numpy(), df["raw_mid"].to_numpy(), df["raw_low"].to_numpy(),
                    df["raw_high"].to_numpy())

    tried = []
    for q_lo, q_hi, foot in VARIANTS:
        cv = cross_validate(df, q_lo, q_hi, foot)
        ok = cv["mid"].notna()
        s = scores(cv.loc[ok, "ref_m"].to_numpy(), cv.loc[ok, "mid"].to_numpy(), cv.loc[ok, "low"].to_numpy(),
                   cv.loc[ok, "high"].to_numpy())
        tried.append({"quantiles": [q_lo, q_hi], "footprint_bands": foot, "held_out": s, "_cv": cv[ok]})
    passing = [t for t in tried if t["held_out"]["range_holds_reference"] >= TARGET]
    # Among variants that hold the reference >= 70% of the time: best single-value accuracy, then the
    # narrower range, then the simpler table (no footprint split). None passing: best coverage.
    chosen = (min(passing, key=lambda t: (-t["held_out"]["within_one_storey"], t["held_out"]["mean_range_width_m"],
                                          t["footprint_bands"])) if passing
              else max(tried, key=lambda t: t["held_out"]["range_holds_reference"]))
    q_lo, q_hi = chosen["quantiles"]
    table = fit(df, q_lo, q_hi, chosen["footprint_bands"])

    report = {
        "kind": "buildings_height_calibration", "task": "U-03", "synthetic": False,
        "built_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reference": "OSM building:levels x 3 m (buildings that also have a GHSL value)",
        "reference_buildings": len(df), "reference_areas_r8": int(df["h3_r8"].nunique()),
        "reference_levels": {str(int(k)): int(v) for k, v in df["osm_levels"].round().value_counts().sort_index().items()},
        "method": {"folds": FOLDS, "grouped_by": "h3_r8", "min_cell": MIN_CELL, "target": TARGET,
                   "ghsl_edges_m": GHSL_EDGES[:-1], "footprint_edges_m2": FOOT_EDGES[:-1]},
        "before": {"all": before, "by_levels": by_levels(df, "raw_mid", "raw_low", "raw_high")},
        "variants_held_out": [{k: v for k, v in t.items() if k != "_cv"} for t in tried],
        "chosen": {"quantiles": chosen["quantiles"], "footprint_bands": chosen["footprint_bands"],
                   "meets_target": bool(passing), "held_out": chosen["held_out"],
                   "held_out_by_levels": by_levels(chosen["_cv"], "mid", "low", "high")},
        "table": table,
        "limits": [
            "References are OSM-tagged buildings: mostly towns, taller and better mapped than the rest.",
            "Levels x 3 m is itself approximate (ground floors and roofs vary).",
            "No independent survey heights for Lebanon were found; published tower heights were not used.",
            "Heights describe the building stock around 2018, before the war.",
        ],
        "rebuild": "python -m pipelines.buildings.height_check",
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", type=Path, default=Path("data/local/buildings_base.parquet"))
    ap.add_argument("--heights", type=Path, default=Path("data/local/buildings_height.parquet"))
    ap.add_argument("--out", type=Path, default=Path("data/manifests/buildings_height_calibration.json"))
    args = ap.parse_args(argv)
    r = run(args.base, args.heights, args.out)
    print(json.dumps({"reference_buildings": r["reference_buildings"], "before": r["before"]["all"],
                      "variants": [(v["quantiles"], v["footprint_bands"], v["held_out"])
                                   for v in r["variants_held_out"]],
                      "chosen": r["chosen"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
