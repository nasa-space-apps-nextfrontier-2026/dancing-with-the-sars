"""M1-02: map-ready change images (Cloud-Optimized GeoTIFF) for the NISAR layer and time slider.

Layers (dB, stored as int16 = dB x 100, nodata -32768, water and invalid pixels masked):
  before_mean_{HH,HV}      mean of the 6 BETA dates (27 Oct 2025 - 19 Jan 2026)
  after_mean_{HH,HV}       mean of the 3 June-July dates (the baseline for later passes)
  change_A_{HH,HV}         after minus before, destriped
  pass_<date>_{HH,HV}      each later pass
  change_<date>_{HH,HV}    that pass minus the June-July baseline, destriped

20 m change can show single buildings, so every layer is tagged restricted; the API decides
who sees what (safety rules: public results only at neighbourhood level, 72 h delay).

    python -m pipelines.radar.nisar.change_images
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

from .crop import sha256
from .features import destripe, mean_power, read_grid, to_db
from .process import CROP_INDEX, load_terrain_mask, tier_paths, validity, water_mask

OUT_DIR = Path("data/private/nisar/change")
INDEX = Path("data/manifests/nisar_change_index.json")
SCALE = 100
NODATA = -32768
FLAGGED_PASSES = {"2026-08-23": "HV about 2 dB brighter than neighbouring passes (14 Nov QA)"}


def write_cog(path: Path, db: np.ndarray, mask: np.ndarray, ref: str) -> None:
    data = np.where(mask & np.isfinite(db), np.round(db * SCALE), NODATA)
    data = np.clip(data, -32767, 32767).astype("int16")
    data[~(mask & np.isfinite(db))] = NODATA
    with rasterio.open(ref) as r:
        profile = {"driver": "COG", "width": r.width, "height": r.height, "count": 1,
                   "dtype": "int16", "crs": r.crs, "transform": r.transform, "nodata": NODATA,
                   "compress": "DEFLATE", "predictor": 2, "blocksize": 512}
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data, 1)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--buildings", type=Path, default=None, help="unused (kept for older commands)")
    ap.parse_args(argv)

    index = json.loads(CROP_INDEX.read_text(encoding="utf-8"))
    pols = {"HH": "HHHH", "HV": "HVHV"}
    before = {p: tier_paths(index, "A-before", t) for p, t in pols.items()}
    after = {p: tier_paths(index, "A-after", t) for p, t in pols.items()}
    later = {p: tier_paths(index, "B", t) for p, t in pols.items()}
    ref = before["HH"][0][2]
    with rasterio.open(ref) as r:
        epsg, bounds = r.crs.to_epsg(), list(r.bounds)

    scenes = [s for _, s, _ in before["HH"] + after["HH"] + later["HH"]]
    land = validity(index, scenes, read_grid(ref)[0].shape) & ~water_mask(index) & ~load_terrain_mask(ref)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    layers: list[dict[str, Any]] = []

    def emit(name: str, db: np.ndarray, kind: str, pol: str, dates: list[str]) -> None:
        path = OUT_DIR / f"{name}.tif"
        write_cog(path, db, land, ref)
        flags = [FLAGGED_PASSES[d] for d in dates if d in FLAGGED_PASSES and pol == "HV"]
        layers.append({"name": name, "kind": kind, "polarization": pol, "dates": dates,
                       "path": path.as_posix(), "sha256": sha256(path), "flags": flags})
        print(f"wrote {name}")

    baseline = {}
    for pol in pols:
        b_db = to_db(mean_power([p for _, _, p in before[pol]])[0])
        a_db = to_db(mean_power([p for _, _, p in after[pol]])[0])
        baseline[pol] = a_db
        b_dates = [d for d, _, _ in before[pol]]
        a_dates = [d for d, _, _ in after[pol]]
        emit(f"before_mean_{pol}", b_db, "mean", pol, b_dates)
        emit(f"after_mean_{pol}", a_db, "mean", pol, a_dates)
        change, _ = destripe(a_db - b_db, land)
        emit(f"change_A_{pol}", change, "change", pol, [b_dates[0], b_dates[-1], a_dates[0], a_dates[-1]])

    for pol in pols:
        for date, _, path in later[pol]:
            p_db = to_db(read_grid(path)[0])
            emit(f"pass_{date}_{pol}", p_db, "pass", pol, [date])
            change, _ = destripe(p_db - baseline[pol], land)
            emit(f"change_{date}_{pol}", change, "change_vs_june_baseline", pol, [date])

    out = {
        "schema_version": "0.1", "kind": "nisar_change_index", "synthetic": False,
        "created_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "crs_epsg": epsg, "bounds": bounds, "pixel_m": 20, "units": "dB",
        "storage": {"dtype": "int16", "scale": 1 / SCALE, "nodata": NODATA, "format": "COG"},
        "safety_tag": "restricted",
        "release_rule": "public only as neighbourhood (H3 r8) results, 72 h after the pass",
        "notes": ["change_A mixes BETA (before) and PROVISIONAL (after) products",
                  "change layers are destriped (smooth column/row trends removed)",
                  "water, invalid, layover, shadow and steep-slope (>25 deg) pixels are nodata"],
        "layers": layers,
    }
    INDEX.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"{len(layers)} layers -> {INDEX}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
