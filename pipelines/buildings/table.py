"""U-04: the building table, one row per building (doc 25, doc 24 section 15.1). The agents read it.

    python -m pipelines.buildings.table

Joins:
- U-01 buildings and U-02 height ranges (by building_id),
- Udula's NISAR damage table by H3 r9 cell: class, evidence label, Sentinel-1 agreement, run id.
  These are CELL results copied to every building in the cell, never building results,
- population per H3 r9 cell (Kisara's K-04 file: cell_id, pop_low, pop_high, pop_year), spread
  over the cell's residential floor area. Without that file the resident columns stay empty and
  the manifest says "unavailable": people are never invented.

Residential floor area: footprint x middle floor count, for buildings whose OSM use is residential,
or whose OSM use is unknown and GHSL calls the place residential. Low and high are spread
separately with whole-number rounding that keeps each cell's total exact.

Restricted: building-level people and damage stay in this local table for the budget and ranking
agents. The API serves people at cell level only (doc 07: no identifiable civilian concentrations).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

DAMAGE_COLUMNS = {"damage_class": "damage_class", "evidence_label": "evidence_label",
                  "s1_agrees": "second_sensor_agrees", "run_id": "run_id"}


def residential_mask(use: pd.Series, use_ghsl: pd.Series) -> np.ndarray:
    return ((use == "residential") | ((use == "unknown") & (use_ghsl == "residential"))).to_numpy()


def spread(total: float, weights: np.ndarray) -> np.ndarray:
    """Whole people per building, proportional to weights, summing exactly to round(total)."""
    total = round(total)
    if weights.sum() <= 0:
        return np.zeros(len(weights), dtype=int)
    raw = total * weights / weights.sum()
    base = np.floor(raw).astype(int)
    left = total - base.sum()
    if left > 0:
        base[np.argsort(-(raw - base), kind="stable")[:left]] += 1
    return base


def add_residents(df: pd.DataFrame, population: pd.DataFrame | None) -> tuple[pd.DataFrame, dict]:
    df = df.copy()
    df["residential"] = residential_mask(df["use"], df["use_ghsl"])
    df["residential_floor_m2"] = np.where(
        df["residential"], df["footprint_m2"] * (df["floors_low"] + df["floors_high"]) / 2, 0.0)
    df["residents_low"] = pd.array([pd.NA] * len(df), dtype="Int64")
    df["residents_high"] = pd.array([pd.NA] * len(df), dtype="Int64")
    if population is None:
        return df, {"status": "unavailable", "reason": "population file (K-04) not loaded"}
    pop = population.dropna(subset=["pop_low", "pop_high"]).set_index("cell_id")
    unallocated_low = unallocated_high = 0
    cells_without_homes = 0
    for cell, idx in df.groupby("h3_r9").groups.items():
        if cell not in pop.index:
            continue  # no estimate for this cell: residents stay unknown
        w = df.loc[idx, "residential_floor_m2"].to_numpy(dtype=float)
        lo, hi = float(pop.at[cell, "pop_low"]), float(pop.at[cell, "pop_high"])
        if w.sum() <= 0:
            cells_without_homes += 1
            unallocated_low += round(lo)
            unallocated_high += round(hi)
            continue
        df.loc[idx, "residents_low"] = spread(lo, w)
        df.loc[idx, "residents_high"] = spread(hi, w)
    return df, {"status": "loaded", "pop_year": int(pop["pop_year"].max()) if len(pop) else None,
                "cells_with_people_but_no_residential_building": cells_without_homes,
                "people_not_allocated_low": unallocated_low, "people_not_allocated_high": unallocated_high}


def build(base: pd.DataFrame, heights: pd.DataFrame, damage: pd.DataFrame,
          population: pd.DataFrame | None) -> tuple[pd.DataFrame, dict]:
    keep = ["building_id", "footprint_m2", "use", "facility_flag", "osm_condition_tag"]
    df = heights.merge(base[keep], on=["building_id"], suffixes=("", "_base"), how="left")
    df = df.drop(columns=[c for c in df.columns if c.endswith("_base")])
    dmg = damage[["h3_r9", *DAMAGE_COLUMNS]].rename(columns=DAMAGE_COLUMNS)
    df = df.merge(dmg, on="h3_r9", how="left")
    df["damage_class"] = df["damage_class"].fillna("not_assessed")
    df["evidence_label"] = df["evidence_label"].fillna("unknown")
    # "Second sensor agrees" means Sentinel-1 confirms a damage CANDIDATE (doc 24). Elsewhere it does
    # not apply, so it is left empty rather than True/False.
    candidate = df["damage_class"].str.endswith("_candidate")
    df["second_sensor_agrees"] = df["second_sensor_agrees"].astype("boolean").where(candidate, pd.NA)
    df, people = add_residents(df, population)
    cols = ["building_id", "h3_r9", "h3_r8", "footprint_m2", "height_low_m", "height_mid_m", "height_high_m",
            "height_source", "floors_low", "floors_high", "use", "use_ghsl", "facility_flag", "osm_condition_tag",
            "residential", "residential_floor_m2", "residents_low", "residents_high",
            "damage_class", "evidence_label", "second_sensor_agrees", "run_id"]
    return df[cols], people


def load_population(path: Path) -> pd.DataFrame | None:
    return pd.read_csv(path) if path.exists() else None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(base_p: Path, heights_p: Path, damage_p: Path, pop_p: Path, out_p: Path, manifest_p: Path) -> dict:
    base = pq.read_table(base_p, columns=["building_id", "footprint_m2", "use", "facility_flag",
                                          "osm_condition_tag"]).to_pandas()
    heights = pq.read_table(heights_p).to_pandas()
    damage = pq.read_table(damage_p, columns=["h3_r9", *DAMAGE_COLUMNS]).to_pandas()
    population = load_population(pop_p)
    rows, people = build(base, heights, damage, population)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(rows, preserve_index=False), out_p)
    manifest = {
        "kind": "building_table", "task": "U-04", "synthetic": False,
        "safety_tag": "restricted_building_level",
        "serve_rule": "Local input for agents only. The API serves people and damage at cell level, never per building.",
        "built_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "inputs": {name: {"file": str(p).replace("\\", "/"), "sha256": sha256(p)}
                   for name, p in (("buildings_base", base_p), ("buildings_height", heights_p),
                                   ("damage_cells", damage_p), ("population", pop_p)) if p.exists()},
        "output": str(out_p).replace("\\", "/"), "output_sha256": sha256(out_p),
        "buildings": len(rows),
        "damage_class_counts": rows["damage_class"].value_counts().to_dict(),
        "evidence_label_counts": rows["evidence_label"].value_counts().to_dict(),
        "residential_buildings": int(rows["residential"].sum()),
        "second_sensor_agrees_buildings": int(rows["second_sensor_agrees"].fillna(False).sum()),
        "people": people,
        "limits": [
            "damage_class, evidence_label and second_sensor_agrees are H3 r9 cell results copied to each building.",
            "second_sensor_agrees is set only in candidate cells (Sentinel-1 confirms the candidate); empty elsewhere.",
            "Residents are a pre-displacement estimate spread by floor area, not people there now.",
            "Heights are ranges (U-02, calibrated in U-03); towers are underestimated.",
        ],
        "rebuild": "python -m pipelines.buildings.table",
    }
    manifest_p.parent.mkdir(parents=True, exist_ok=True)
    manifest_p.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", type=Path, default=Path("data/local/buildings_base.parquet"))
    ap.add_argument("--heights", type=Path, default=Path("data/local/buildings_height.parquet"))
    ap.add_argument("--damage", type=Path, default=Path("data/private/nisar/model/damage_cells.parquet"))
    ap.add_argument("--population", type=Path, default=Path("data/local/population.csv.gz"))
    ap.add_argument("--out", type=Path, default=Path("data/local/building_table.parquet"))
    ap.add_argument("--manifest", type=Path, default=Path("data/manifests/building_table.json"))
    args = ap.parse_args(argv)
    m = run(args.base, args.heights, args.damage, args.population, args.out, args.manifest)
    print(json.dumps({k: m[k] for k in ("buildings", "damage_class_counts", "evidence_label_counts",
                                        "residential_buildings", "people")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
