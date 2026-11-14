"""M1 stretch: independent Sentinel-1 cross-check of the NISAR damage candidates.

Sentinel-1 (Copernicus, C-band) processed by NASA OPERA as RTC-S1 (30 m gamma0, already
terrain-corrected). Track 21 descending covers the whole demo box. Same before/after windows
as NISAR. Bursts are put on the NISAR 20 m grid; per H3 r9 cell we compute the VV/VH change and
whether Sentinel-1 also shows a collapse-like drop. Candidates confirmed by both satellites
become "corroborated" (two independent sensors), the others stay "observed".

    python -m pipelines.radar.nisar.s1_check --download
    python -m pipelines.radar.nisar.s1_check --buildings data/raw/hotosm/lbn_buildings.parquet
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rasterio
from h3.api import basic_int as h3i
from rasterio.warp import Resampling, reproject

from .features import pixel_cells, to_db
from .process import (
    CROP_INDEX,
    OUT_DIR,
    built_mask,
    load_terrain_mask,
    tier_paths,
    water_mask,
)

COLLECTION = "C2777436413-ASF"  # OPERA_L2_RTC-S1_V1
TRACK = 21
BEFORE = ("2025-10-27T00:00:00Z", "2026-01-20T00:00:00Z")
AFTER = ("2026-06-20T00:00:00Z", "2026-07-20T00:00:00Z")
N_BEFORE_DATES = 6
RAW = Path("data/raw/s1")
MANIFEST = Path("data/manifests/s1_rtc.json")
NAME = re.compile(r"OPERA_L2_RTC-S1_T(\d+)-(\d+)-IW(\d)_(\d{8})T")
AGREE_Z = -2.0  # Sentinel-1 VV change at least 2 robust SDs below the typical cell


def search(window: tuple[str, str]) -> list[dict[str, Any]]:
    out, page = [], 1
    while True:
        q = urllib.parse.urlencode({
            "collection_concept_id": COLLECTION, "bounding_box": "35.0,33.0,36.0,33.6",
            "temporal": f"{window[0]},{window[1]}", "page_size": 2000, "page_num": page,
            "readable_granule_name": f"OPERA_L2_RTC-S1_T{TRACK:03d}-*",
            "options[readable_granule_name][pattern]": "true"})
        items = json.load(urllib.request.urlopen(
            "https://cmr.earthdata.nasa.gov/search/granules.umm_json?" + q, timeout=180))["items"]
        out += items
        if len(items) < 2000:
            return out
        page += 1


def granule_files(items: list[dict[str, Any]]) -> dict[str, list[str]]:
    """date -> list of VV/VH GeoTIFF URLs (HTTPS)."""
    by_date: dict[str, list[str]] = defaultdict(list)
    for it in items:
        m = NAME.match(it["umm"]["GranuleUR"])
        if not m:
            continue
        date = m.group(4)
        for u in it["umm"].get("RelatedUrls", []):
            url = u.get("URL", "")
            if url.startswith("https") and url.endswith(("_VV.tif", "_VH.tif")):
                by_date[date].append(url)
    return dict(by_date)


def plan() -> dict[str, Any]:
    before = granule_files(search(BEFORE))
    after = granule_files(search(AFTER))
    keep_before = sorted(before)[-N_BEFORE_DATES:]
    return {"schema_version": "0.1", "kind": "s1_rtc_manifest", "synthetic": False,
            "collection": COLLECTION, "track": TRACK, "direction": "DESCENDING",
            "before": {d: sorted(before[d]) for d in keep_before},
            "after": {d: sorted(after[d]) for d in sorted(after)},
            "licence": "Copernicus Sentinel data, processed by NASA OPERA (open)"}


def download(manifest: dict[str, Any]) -> None:
    import earthaccess

    from .download import login

    ea = login()
    assert ea is earthaccess
    for period in ("before", "after"):
        for date, urls in manifest[period].items():
            dest = RAW / date
            missing = [u for u in urls if not (dest / u.rsplit("/", 1)[-1]).exists()]
            if missing:
                dest.mkdir(parents=True, exist_ok=True)
                ea.download(missing, local_path=str(dest))
            print(f"{period} {date}: {len(urls)} files")


def date_mosaic(date: str, pol: str, ref: str) -> np.ndarray:
    """Mean of all bursts of one date and polarization, reprojected onto the NISAR crop grid."""
    with rasterio.open(ref) as r:
        shape, dst_t, dst_crs = r.shape, r.transform, r.crs
    total = np.zeros(shape, dtype="float64")
    count = np.zeros(shape, dtype="int16")
    for f in sorted((RAW / date).glob(f"*_{pol}.tif")):
        with rasterio.open(f) as s:
            out = np.full(shape, np.nan, dtype="float32")
            reproject(rasterio.band(s, 1), out, dst_transform=dst_t, dst_crs=dst_crs,
                      resampling=Resampling.bilinear, dst_nodata=np.nan)
        ok = np.isfinite(out) & (out > 0)
        total[ok] += out[ok]
        count[ok] += 1
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(count > 0, total / count, np.nan).astype("float32")


def period_mean(dates: list[str], pol: str, ref: str) -> np.ndarray:
    stack = np.stack([date_mosaic(d, pol, ref) for d in dates])
    with np.errstate(invalid="ignore"):
        return np.nanmean(stack, axis=0)  # mean linear power over dates


def robust_z(v: pd.Series) -> pd.Series:
    med = v.median()
    iqr = v.quantile(0.75) - v.quantile(0.25)
    return (v - med) / (iqr / 1.349 if iqr > 0 else 1.0)


def cross_check(buildings: Path) -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    index = json.loads(CROP_INDEX.read_text(encoding="utf-8"))
    ref = tier_paths(index, "A-before", "HHHH")[0][2]
    with rasterio.open(ref) as r:
        transform, shape, crs = r.transform, r.shape, r.crs
    land = ~water_mask(index) & ~load_terrain_mask(ref)
    built = built_mask(buildings, ref) & land

    change = {}
    for pol in ("VV", "VH"):
        b = to_db(period_mean(sorted(manifest["before"]), pol, ref))
        a = to_db(period_mean(sorted(manifest["after"]), pol, ref))
        change[pol] = a - b
    valid = built & np.isfinite(change["VV"]) & np.isfinite(change["VH"])
    cells = pixel_cells(transform, shape, crs, valid)
    sel = valid & (cells > 0)
    px = pd.DataFrame({"c": cells[sel], "vv": change["VV"][sel], "vh": change["VH"][sel]})
    px["drop"] = px["vv"] < -3.0
    agg = px.groupby("c").agg(s1_d_vv=("vv", "median"), s1_d_vh=("vh", "median"),
                              s1_drop_share=("drop", "mean"), s1_px=("vv", "size"))
    agg.index = [h3i.int_to_str(int(i)) for i in agg.index]

    path = OUT_DIR / "damage_cells.parquet"
    cells_df = pd.read_parquet(path)
    cells_df = cells_df.drop(columns=[c for c in cells_df.columns if c.startswith("s1_")] +
                             [c for c in ("evidence_label",) if c in cells_df.columns])
    cells_df = cells_df.join(agg, on="h3_r9")
    assessed = ~cells_df["sparse_cell"] & ~cells_df["low_coverage"] & cells_df["s1_d_vv"].notna()
    z = pd.Series(np.nan, index=cells_df.index)
    z[assessed] = robust_z(cells_df.loc[assessed, "s1_d_vv"])
    cells_df["s1_z_vv"] = z
    cells_df["s1_agrees"] = assessed & (z <= AGREE_Z)
    cand = cells_df["damage_class"].str.endswith("_candidate")
    cells_df["evidence_label"] = np.where(
        cand & cells_df["s1_agrees"], "corroborated",
        np.where(cand, "observed", np.where(cells_df["damage_class"] == "unknown", "unknown", "none")))
    cells_df.to_parquet(path, index=False)

    stats: dict[str, Any] = {"before_dates": sorted(manifest["before"]),
                             "after_dates": sorted(manifest["after"]),
                             "agree_rule": f"Sentinel-1 VV change robust z <= {AGREE_Z}",
                             "by_class": {}}
    a = cells_df[assessed]
    for cls, g in a.groupby("damage_class"):
        stats["by_class"][cls] = {"cells": len(g), "s1_agrees": int(g["s1_agrees"].sum()),
                                  "share": float(g["s1_agrees"].mean())}
    base = a[a["damage_class"] == "no_detected_change"]["s1_agrees"].mean()
    candm = a[a["damage_class"].str.endswith("_candidate")]["s1_agrees"].mean()
    stats["candidates_share"] = float(candm)
    stats["no_change_share"] = float(base)
    stats["ratio"] = float(candm / base) if base else None
    stats["corroborated_cells"] = int((cells_df["evidence_label"] == "corroborated").sum())
    (OUT_DIR / "s1_check.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--download", action="store_true", help="search and download the RTC-S1 files")
    ap.add_argument("--buildings", type=Path, help="run the cross-check with this buildings file")
    args = ap.parse_args(argv)
    if args.download:
        manifest = plan()
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print("before:", list(manifest["before"]), "after:", list(manifest["after"]))
        download(manifest)
    if args.buildings:
        s = cross_check(args.buildings)
        print(f"Sentinel-1 agrees: candidates {s['candidates_share']:.1%} vs no-change cells "
              f"{s['no_change_share']:.1%} (ratio {s['ratio']:.1f}x); corroborated cells: {s['corroborated_cells']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
