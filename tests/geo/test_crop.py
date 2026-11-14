"""M1-01 crop tests on a small synthetic GCOV-like HDF5 file (no real scene)."""

import pytest

pytest.importorskip("h5py")
pytest.importorskip("rasterio")
pytest.importorskip("pyproj")

import h5py
import numpy as np
import rasterio
from pyproj import Transformer

from pipelines.radar.nisar.crop import crop_file

BBOX = {"west": 35.2, "south": 33.2, "east": 35.4, "north": 33.4}


def make_gcov(path, epsg=32636, spacing=200.0):
    tr = Transformer.from_crs(4326, epsg, always_xy=True)
    x0, y0 = tr.transform(35.0, 33.6)
    x1, y1 = tr.transform(35.6, 33.0)
    x = np.arange(x0, x1, spacing)
    y = np.arange(y0, y1, -spacing)
    hh = np.full((y.size, x.size), 0.1, dtype="float32")
    hh[0, 0] = -1.0  # invalid power
    hh[1, 1] = np.nan
    with h5py.File(path, "w") as f:
        g = f.create_group("science/LSAR/GCOV/grids/frequencyA")
        g["xCoordinates"] = x
        g["yCoordinates"] = y
        g["HHHH"] = hh
        g["HVHV"] = hh * 0.1
        proj = g.create_dataset("projection", data=np.uint32(epsg))
        proj.attrs["epsg_code"] = epsg
    return x, y


def test_crop_window_and_georeference(tmp_path):
    src = tmp_path / "scene.h5"
    make_gcov(src)
    s = crop_file(src, tmp_path / "out", "scene", BBOX)
    assert s["epsg"] == 32636
    assert s["pixel_spacing_m"] == [200.0, 200.0]
    terms = {o["term"] for o in s["outputs"]}
    assert terms == {"HHHH", "HVHV"}
    with rasterio.open(tmp_path / "out" / "scene_HHHH.tif") as r:
        assert r.crs.to_epsg() == 32636
        tr = Transformer.from_crs(4326, 32636, always_xy=True)
        cx, cy = tr.transform(35.3, 33.3)
        left, bottom, right, top = r.bounds
        assert left <= cx <= right and bottom <= cy <= top
        assert np.isfinite(r.read(1)).all()


def test_invalid_power_becomes_nodata(tmp_path):
    src = tmp_path / "scene.h5"
    make_gcov(src)
    s = crop_file(src, tmp_path / "out", "scene", {"west": 35.0, "south": 33.0, "east": 36.0, "north": 33.6})
    with rasterio.open(tmp_path / "out" / "scene_HHHH.tif") as r:
        a = r.read(1)
    assert np.isnan(a[0, 0]) and np.isnan(a[1, 1])
    hh = next(o for o in s["outputs"] if o["term"] == "HHHH")
    assert 0 < hh["valid_fraction"] < 1


def test_no_overlap_raises(tmp_path):
    src = tmp_path / "scene.h5"
    make_gcov(src)
    with pytest.raises(ValueError):
        crop_file(src, tmp_path / "out", "scene", {"west": 10, "south": 10, "east": 11, "north": 11})
