"""M1-02 (stretch): HH coherence on the 20 m GCOV crop grid.

  coh_event   GSLC 19 Jan 2026 (BETA) x 24 Jun 2026 (PROVISIONAL), across the escalation.
              GSLC phase is already flattened, so the two files multiply directly
              (NISAR user guide). 4 x 2 GSLC pixels (5 m x 10 m) sum into each 20 m pixel,
              then a 3 x 3 boxcar: 72 looks.
  coh_before  GUNW 7 -> 19 Jan 2026 wrapped-interferogram coherence (already 20 m), 3 x 3 mean.

Both grids are checked to nest exactly in the GCOV crop grid; nothing is resampled.

    python -m pipelines.radar.nisar.coherence
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import rasterio
from scipy.ndimage import uniform_filter

from .process import CROP_INDEX, tier_paths

RAW = Path("data/raw/nisar")
OUT_DIR = Path("data/private/nisar/coherence")
GSLC_GRID = "science/LSAR/GSLC/grids/frequencyA"
GUNW_GRID = "science/LSAR/GUNW/grids/frequencyA/wrappedInterferogram"
BOX = 3
ROW_BLOCK = 256  # output rows per chunk


def window_in(x: np.ndarray, y: np.ndarray, transform: rasterio.Affine, shape: tuple[int, int],
              fy: int, fx: int) -> tuple[slice, slice]:
    """Rows/cols of a finer grid (fy x fx pixels per 20 m pixel) covering the crop exactly."""
    dx, dy = x[1] - x[0], y[1] - y[0]
    col0 = (transform.c - (x[0] - dx / 2)) / dx
    row0 = (transform.f - (y[0] - dy / 2)) / dy
    if abs(col0 - round(col0)) > 1e-6 or abs(row0 - round(row0)) > 1e-6:
        raise ValueError("Grid does not nest in the GCOV crop grid")
    c0, r0 = round(col0), round(row0)
    return slice(r0, r0 + shape[0] * fy), slice(c0, c0 + shape[1] * fx)


def valid_mask(m: np.ndarray) -> np.ndarray:
    return (m > 0) & (m < 255)


def event_coherence(f1: str, f2: str, transform: rasterio.Affine, shape: tuple[int, int]) -> np.ndarray:
    num = np.zeros(shape, dtype="complex64")
    p1 = np.zeros(shape, dtype="float32")
    p2 = np.zeros(shape, dtype="float32")
    with h5py.File(f1) as h1, h5py.File(f2) as h2:
        g1, g2 = h1[GSLC_GRID], h2[GSLC_GRID]
        x, y = g1["xCoordinates"][()], g1["yCoordinates"][()]
        if not (np.array_equal(x, g2["xCoordinates"][()]) and np.array_equal(y, g2["yCoordinates"][()])):
            raise ValueError("The two GSLC grids differ")
        fy, fx = round(20 / abs(y[1] - y[0])), round(20 / abs(x[1] - x[0]))
        rs, cs = window_in(x, y, transform, shape, fy, fx)
        for r in range(0, shape[0], ROW_BLOCK):
            n = min(ROW_BLOCK, shape[0] - r)
            sl = (slice(rs.start + r * fy, rs.start + (r + n) * fy), cs)
            a, b = g1["HH"][sl], g2["HH"][sl]
            ok = valid_mask(g1["mask"][sl]) & valid_mask(g2["mask"][sl]) & np.isfinite(a) & np.isfinite(b)
            a, b = np.where(ok, a, 0), np.where(ok, b, 0)

            def block(v: np.ndarray, n: int = n) -> np.ndarray:
                return v.reshape(n, fy, shape[1], fx).sum(axis=(1, 3))

            num[r:r + n] = block(a * np.conj(b))
            p1[r:r + n] = block(np.abs(a) ** 2)
            p2[r:r + n] = block(np.abs(b) ** 2)
            print(f"  rows {r + n}/{shape[0]}", end="\r")
    re = uniform_filter(num.real, BOX)
    im = uniform_filter(num.imag, BOX)
    den = np.sqrt(uniform_filter(p1, BOX) * uniform_filter(p2, BOX))
    with np.errstate(invalid="ignore", divide="ignore"):
        coh = np.where(den > 0, np.hypot(re, im) / den, np.nan)
    return coh.astype("float32")


def before_coherence(f: str, transform: rasterio.Affine, shape: tuple[int, int]) -> np.ndarray:
    with h5py.File(f) as h:
        g = h[GUNW_GRID]
        x, y = g["xCoordinates"][()], g["yCoordinates"][()]
        rs, cs = window_in(x, y, transform, shape, 1, 1)
        coh = g["HH/coherenceMagnitude"][rs, cs].astype("float32")
        ok = valid_mask(g["mask"][rs, cs]) & np.isfinite(coh)
    filled = np.where(ok, coh, 0)
    weight = uniform_filter(ok.astype("float32"), BOX)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where(weight > 0.5, uniform_filter(filled, BOX) / weight, np.nan)
    return out.astype("float32")


def write(path: Path, arr: np.ndarray, ref: str) -> None:
    with rasterio.open(ref) as r:
        profile = {"driver": "GTiff", "width": r.width, "height": r.height, "count": 1,
                   "dtype": "float32", "crs": r.crs, "transform": r.transform, "nodata": np.nan,
                   "compress": "deflate", "tiled": True}
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr, 1)


def main() -> int:
    index = json.loads(CROP_INDEX.read_text(encoding="utf-8"))
    ref = tier_paths(index, "A-before", "HHHH")[0][2]
    with rasterio.open(ref) as r:
        transform, shape = r.transform, r.shape
    g_before = glob.glob(str(RAW / "*GSLC*20260119T*.h5"))[0]
    g_after = glob.glob(str(RAW / "*GSLC*20260624T*.h5"))[0]
    gunw = glob.glob(str(RAW / "*GUNW*20260107T*20260119T*.h5"))[0]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("coh_event: GSLC 2026-01-19 x 2026-06-24")
    ev = event_coherence(g_before, g_after, transform, shape)
    write(OUT_DIR / "coh_event_HH.tif", ev, ref)
    print("\ncoh_before: GUNW 2026-01-07 -> 2026-01-19")
    bf = before_coherence(gunw, transform, shape)
    write(OUT_DIR / "coh_before_HH.tif", bf, ref)
    for name, a in (("coh_event", ev), ("coh_before", bf)):
        v = a[np.isfinite(a)]
        print(f"{name}: valid {v.size / a.size:.1%}, p10/p50/p90 = {np.percentile(v, [10, 50, 90]).round(3)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
