"""M1-02: terrain mask from NASADEM: radar layover, radar shadow and steep slopes -> Unknown.

Geometry per pixel, using the GCOV radarGrid (line-of-sight from target to sensor, ENU):
  alpha = slope angle rising toward the sensor (along the horizontal line of sight)
  layover  when alpha >  incidence
  shadow   when alpha < -(90 - incidence)
  steep    when the overall slope > STEEP_DEG

    python -m pipelines.radar.nisar.terrain
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.warp import Resampling, reproject
from scipy.interpolate import RegularGridInterpolator

DEM_DIR = Path("data/raw/nasadem")
OUT = Path("data/private/nisar/terrain_mask.tif")
STEEP_DEG = 25.0
LOS_HEIGHT_M = 500.0


def dem_on_grid(ref: str) -> np.ndarray:
    tiles = sorted(glob.glob(str(DEM_DIR / "NASADEM_HGT_*.zip")))
    if not tiles:
        raise SystemExit("No NASADEM tiles in data/raw/nasadem")
    srcs = [rasterio.open(f"/vsizip/{Path(t).as_posix()}/{Path(t).stem.split('_')[-1]}.hgt") for t in tiles]
    mosaic, mtrans = merge(srcs)
    with rasterio.open(ref) as r:
        out = np.full(r.shape, np.nan, dtype="float32")
        reproject(mosaic[0].astype("float32"), out, src_transform=mtrans, src_crs=srcs[0].crs,
                  dst_transform=r.transform, dst_crs=r.crs, resampling=Resampling.bilinear,
                  src_nodata=-32768, dst_nodata=np.nan)
    for s in srcs:
        s.close()
    return out


def los_on_grid(raw_h5: str, ref: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """East/north line-of-sight components and incidence angle (deg) on the crop grid."""
    with h5py.File(raw_h5) as h:
        rg = h["science/LSAR/GCOV/metadata/radarGrid"]
        k = int(np.argmin(np.abs(rg["heightAboveEllipsoid"][()] - LOS_HEIGHT_M)))
        x, y = rg["xCoordinates"][()], rg["yCoordinates"][()]
        layers = [rg[n][k] for n in ("losUnitVectorX", "losUnitVectorY", "incidenceAngle")]
    if y[0] > y[-1]:
        y = y[::-1]
        layers = [a[::-1] for a in layers]
    with rasterio.open(ref) as r:
        rows, cols = np.mgrid[0:r.height, 0:r.width]
        xs, ys = rasterio.transform.xy(r.transform, rows.ravel(), cols.ravel(), offset="center")
        pts = np.column_stack([ys, xs])
        shape = r.shape
    out = []
    for a in layers:
        f = RegularGridInterpolator((y, x), a, bounds_error=False, fill_value=np.nan)
        out.append(f(pts).reshape(shape).astype("float32"))
    return out[0], out[1], out[2]


def terrain_mask(raw_h5: str, ref: str) -> tuple[np.ndarray, dict[str, float]]:
    dem = dem_on_grid(ref)
    lx, ly, inc = los_on_grid(raw_h5, ref)
    with rasterio.open(ref) as r:
        px = abs(r.transform.a)
    return classify_terrain(dem, lx, ly, inc, px)


def classify_terrain(dem: np.ndarray, lx: np.ndarray, ly: np.ndarray, inc: np.ndarray,
                     px: float) -> tuple[np.ndarray, dict[str, float]]:
    """Mask from a north-up DEM (rows run south), line-of-sight east/north parts and incidence."""
    d_row, d_col = np.gradient(dem, px)
    gx, gy = d_col, -d_row  # east and north slope components (rows run south)
    hnorm = np.hypot(lx, ly)
    rise = (gx * lx + gy * ly) / hnorm  # slope component toward the sensor
    alpha = np.degrees(np.arctan(rise))
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    layover = alpha > inc
    shadow = alpha < -(90.0 - inc)
    steep = slope > STEEP_DEG
    mask = layover | shadow | steep | ~np.isfinite(dem)
    stats = {"layover": float(layover.mean()), "shadow": float(shadow.mean()),
             f"steep_gt_{STEEP_DEG:.0f}_deg": float(steep.mean()), "masked_total": float(mask.mean())}
    return mask, stats


def main() -> int:
    from .process import CROP_INDEX, tier_paths

    index = json.loads(CROP_INDEX.read_text(encoding="utf-8"))
    ref = tier_paths(index, "A-before", "HHHH")[0][2]
    raw = min(glob.glob("data/raw/nisar/*GCOV*.h5"))
    mask, stats = terrain_mask(raw, ref)
    with rasterio.open(ref) as r:
        profile = {"driver": "GTiff", "width": r.width, "height": r.height, "count": 1, "dtype": "uint8",
                   "crs": r.crs, "transform": r.transform, "compress": "deflate", "tiled": True}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(OUT, "w", **profile) as dst:
        dst.write(mask.astype("uint8"), 1)
    print(json.dumps({k: round(v, 4) for k, v in stats.items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
