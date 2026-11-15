"""Render 256 px web-map tiles (EPSG:3857) from the private change COGs.

Values are stored as int16 = dB x 100 with nodata -32768 (see data/manifests/nisar_change_index.json).
Change layers use a diverging blue-white-red ramp (-6..+6 dB; red = drop); mean layers use grey
(-25..0 dB). Nodata is transparent. Returns None when the tile does not touch the layer.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import rasterio
import rasterio.errors
from rasterio.enums import Resampling
from rasterio.io import MemoryFile
from rasterio.transform import from_bounds as transform_from_bounds
from rasterio.warp import reproject, transform_bounds

SIZE = 256
NODATA = -32768
ORIGIN = 20037508.342789244


def tile_bounds(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    span = 2 * ORIGIN / (2 ** z)
    left = -ORIGIN + x * span
    top = ORIGIN - y * span
    return left, top - span, left + span, top


def colorize(db: np.ndarray, valid: np.ndarray, kind: str) -> np.ndarray:
    rgba = np.zeros((4, *db.shape), dtype="uint8")
    if kind == "mean":
        g = np.clip((db + 25.0) / 25.0, 0, 1) * 255
        rgba[0] = rgba[1] = rgba[2] = g.astype("uint8")
    else:
        t = np.clip(db / 6.0, -1, 1)  # -1 strong drop (red) .. +1 strong rise (blue)
        down, up = np.clip(-t, 0, 1), np.clip(t, 0, 1)
        rgba[0] = (255 - up * 200).astype("uint8")
        rgba[1] = (255 - (down + up) * 200).astype("uint8")
        rgba[2] = (255 - down * 200).astype("uint8")
    rgba[3] = np.where(valid, 230, 0).astype("uint8")
    return rgba


def render(cog_path: str, z: int, x: int, y: int, kind: str) -> bytes | None:
    bounds = tile_bounds(z, x, y)
    with rasterio.open(cog_path) as src:
        layer = transform_bounds(src.crs, "EPSG:3857", *src.bounds)
        if bounds[0] > layer[2] or bounds[2] < layer[0] or bounds[1] > layer[3] or bounds[3] < layer[1]:
            return None
        data = np.full((SIZE, SIZE), NODATA, dtype="int16")
        reproject(rasterio.band(src, 1), data, src_nodata=NODATA,
                  dst_transform=transform_from_bounds(*bounds, SIZE, SIZE), dst_crs="EPSG:3857",
                  dst_nodata=NODATA, resampling=Resampling.bilinear)
    valid = data != NODATA
    rgba = colorize(data.astype("float32") / 100.0, valid, kind)
    with MemoryFile() as mem, warnings.catch_warnings():
        warnings.simplefilter("ignore", rasterio.errors.NotGeoreferencedWarning)
        with mem.open(driver="PNG", width=SIZE, height=SIZE, count=4, dtype="uint8") as dst:
            dst.write(rgba)
        return mem.read()


def valid_tile(z: int, x: int, y: int) -> bool:
    return 0 <= z <= 18 and 0 <= x < 2 ** z and 0 <= y < 2 ** z and not math.isnan(z)
