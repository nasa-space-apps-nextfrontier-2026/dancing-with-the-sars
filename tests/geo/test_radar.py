"""M1-02 feature tests on small synthetic rasters (no real scenes)."""

import pytest

pytest.importorskip("rasterio")
pytest.importorskip("pyproj")
pytest.importorskip("h3")

import numpy as np
import rasterio
from pyproj import CRS
from rasterio.transform import from_origin

from pipelines.radar.nisar.features import (
    cell_table,
    mean_power,
    pixel_cells,
    pixel_features,
    to_db,
)

CRS_UTM = CRS.from_epsg(32632)  # synthetic location, not the study area
TRANSFORM = from_origin(500_000, 1_110_000, 20, 20)


def write(path, arr, transform=TRANSFORM):
    with rasterio.open(path, "w", driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1,
                       dtype="float32", crs=CRS_UTM.to_wkt(), transform=transform, nodata=np.nan) as d:
        d.write(arr.astype("float32"), 1)
    return path


def test_mean_of_linear_power_then_db(tmp_path):
    a = write(tmp_path / "a.tif", np.full((4, 4), 0.1))
    b = write(tmp_path / "b.tif", np.full((4, 4), 0.3))
    mean, count = mean_power([a, b])
    assert np.allclose(mean, 0.2)
    assert (count == 2).all()
    assert np.allclose(to_db(mean), 10 * np.log10(0.2))  # not the mean of the dB values


def test_invalid_dates_are_counted_out(tmp_path):
    x = np.full((2, 2), 0.1)
    y = x.copy()
    y[0, 0] = np.nan
    y[0, 1] = -1
    mean, count = mean_power([write(tmp_path / "x.tif", x), write(tmp_path / "y.tif", y)])
    assert count[0, 0] == 1 and count[0, 1] == 1 and count[1, 1] == 2
    assert np.allclose(mean, 0.1)


def test_grid_mismatch_rejected(tmp_path):
    a = write(tmp_path / "a.tif", np.ones((4, 4)))
    b = write(tmp_path / "b.tif", np.ones((4, 4)), transform=from_origin(500_020, 1_110_000, 20, 20))
    with pytest.raises(ValueError):
        mean_power([a, b])


def test_features_and_cell_table():
    shape = (60, 60)
    before = np.full(shape, 0.2, dtype="float32")
    after = before.copy()
    after[:20, :20] = 0.02  # -10 dB drop in one corner
    f = pixel_features(before, before * 0.1, after, before * 0.1)
    assert np.isclose(f["d_hh"][0, 0], -10, atol=1e-4)
    assert np.isclose(f["d_hh"][59, 59], 0, atol=1e-4)

    built = np.ones(shape, dtype=bool)
    cells = pixel_cells(TRANSFORM, shape, CRS_UTM, built)
    table = cell_table(cells, built, f, pixel_area_m2=400)
    assert table["h3_r9"].str.len().eq(15).all()
    assert table["strong_drop_share"].between(0, 1).all()
    corner = table.loc[table["d_hh"] < -5]
    assert not corner.empty and (corner["strong_drop_share"] > 0.5).all()
    assert (table["h3_r8"].str.len() == 15).all()


def test_destripe_removes_column_ramp_but_keeps_local_change():
    from pipelines.radar.nisar.features import destripe

    rows, cols = 300, 400
    ramp = np.tile(np.linspace(-2, 2, cols), (rows, 1)).astype("float32")
    change = ramp.copy()
    change[140:160, 190:210] -= 8.0  # local strong drop
    sample = np.ones((rows, cols), dtype=bool)
    out, info = destripe(change, sample, window=51)
    assert info["column_trend_range_db"] > 3.5
    background = np.delete(out, np.s_[130:170], axis=0)
    assert np.abs(np.nanmedian(background, axis=0)).max() < 0.2
    assert out[150, 200] < -7.0
