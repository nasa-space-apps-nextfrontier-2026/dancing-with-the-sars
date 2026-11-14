"""M1-01: crop a NISAR GCOV file to the demo box and write one GeoTIFF per term.

Reads only the AOI window from the HDF5 file (h5py slicing), so it also works on a
remote file object opened with earthaccess. Values stay in the product's linear
power units; dB conversion happens later (mean linear power first, then dB).

    python -m pipelines.radar.nisar.crop <file.h5> --out data/private/nisar/crops
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, BinaryIO

import h5py
import numpy as np
import rasterio
from pyproj import CRS, Transformer
from rasterio.transform import from_origin

from .discover import CONFIG_PATH, load_config

TERMS = ("HHHH", "HVHV")
OPTIONAL = ("mask", "numberOfLooks")


def find_grid_group(h5: h5py.File, frequency: str = "frequencyA") -> h5py.Group:
    """The GCOV grid group holding x/y coordinates and covariance terms."""
    found: list[str] = []

    def visit(name: str, obj: Any) -> None:
        is_grid = isinstance(obj, h5py.Group) and "xCoordinates" in obj and "yCoordinates" in obj
        if is_grid and any(t in obj for t in TERMS):
            found.append(name)

    h5.visititems(visit)
    preferred = [n for n in found if n.endswith(frequency)]
    if not (preferred or found):
        raise ValueError("No GCOV grid with xCoordinates/yCoordinates and HHHH/HVHV found")
    return h5[(preferred or found)[0]]


def epsg_of(grid: h5py.Group) -> int:
    if "projection" in grid:
        attrs = grid["projection"].attrs
        for key in ("epsg_code", "epsg", "EPSG"):
            if key in attrs:
                return int(np.asarray(attrs[key]).ravel()[0])
        value = np.asarray(grid["projection"][()]).ravel()
        if value.size == 1 and np.issubdtype(value.dtype, np.integer):
            return int(value[0])
    raise ValueError("EPSG code not found in the grid's projection dataset")


def aoi_window(x: np.ndarray, y: np.ndarray, bbox: dict[str, float], epsg: int) -> tuple[slice, slice]:
    """Row/column slices covering the WGS84 box in the product grid (edges densified)."""
    tr = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(epsg), always_xy=True)
    lons = np.concatenate([np.linspace(bbox["west"], bbox["east"], 50)] * 2 + [[bbox["west"]] * 50, [bbox["east"]] * 50])
    lats = np.concatenate([[bbox["south"]] * 50, [bbox["north"]] * 50] + [np.linspace(bbox["south"], bbox["north"], 50)] * 2)
    px, py = tr.transform(lons, lats)
    xmin, xmax, ymin, ymax = px.min(), px.max(), py.min(), py.max()

    cols = np.where((x >= xmin) & (x <= xmax))[0]
    rows = np.where((y >= ymin) & (y <= ymax))[0]
    if cols.size == 0 or rows.size == 0:
        raise ValueError("The demo box does not overlap this product")
    return slice(rows.min(), rows.max() + 1), slice(cols.min(), cols.max() + 1)


def crop_file(src: str | Path | BinaryIO, out_dir: Path, scene: str, bbox: dict[str, float]) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    with h5py.File(src, "r") as h5:
        grid = find_grid_group(h5)
        epsg = epsg_of(grid)
        x = grid["xCoordinates"][()]
        y = grid["yCoordinates"][()]
        rs, cs = aoi_window(x, y, bbox, epsg)
        xs, ys = x[cs], y[rs]
        dx = float(np.median(np.diff(x)))
        dy = float(np.median(np.diff(y)))
        if dy > 0:
            raise ValueError("Expected north-up grid (y decreasing)")
        transform = from_origin(xs[0] - dx / 2, ys[0] - dy / 2, dx, -dy)

        outputs = []
        for term in TERMS + OPTIONAL:
            if term not in grid:
                continue
            arr = grid[term][rs, cs]
            if term in TERMS:
                arr = np.asarray(arr, dtype="float32")
                arr[~np.isfinite(arr) | (arr <= 0)] = np.nan
                nodata: float | int | None = np.nan
            else:
                nodata = None
            path = out_dir / f"{scene}_{term}.tif"
            profile = {
                "driver": "GTiff", "height": arr.shape[0], "width": arr.shape[1], "count": 1,
                "dtype": arr.dtype.name, "crs": CRS.from_epsg(epsg).to_wkt(), "transform": transform,
                "nodata": nodata, "compress": "deflate", "tiled": True, "blockxsize": 256, "blockysize": 256,
            }
            with rasterio.open(path, "w", **profile) as dst:
                dst.write(arr, 1)
            valid = float(np.isfinite(arr).mean()) if term in TERMS else None
            outputs.append({
                "term": term, "path": path.as_posix(), "sha256": sha256(path),
                "valid_fraction": valid, "units": "linear power" if term in TERMS else None,
            })

    summary = {
        "scene": scene, "epsg": epsg, "pixel_spacing_m": [abs(dx), abs(dy)],
        "shape": [int(rs.stop - rs.start), int(cs.stop - cs.start)],
        "bounds": [float(xs[0] - dx / 2), float(ys[-1] + dy / 2), float(xs[-1] + dx / 2), float(ys[0] - dy / 2)],
        "outputs": outputs,
    }
    (out_dir / f"{scene}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("h5", type=Path)
    ap.add_argument("--out", type=Path, default=Path("data/private/nisar/crops"))
    ap.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    summary = crop_file(args.h5, args.out, args.h5.stem, cfg["bbox_wgs84"])
    print(json.dumps({k: v for k, v in summary.items() if k != "outputs"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
