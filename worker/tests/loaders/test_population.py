
import h3
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_bounds

from worker.loaders.population import (
    COLUMNS,
    POP_HIGH,
    POP_LOW,
    POP_YEAR,
    load_population,
)

# Small synthetic raster: 5x5 pixels, value 100 each, covering (35.0,33.0)-(35.05,33.05)
RASTER_BOUNDS = (35.0, 33.0, 35.05, 33.05)
RASTER_VALUE = 100.0
RASTER_TOTAL = 25 * RASTER_VALUE  # 25 pixels * 100


def _write_synthetic_raster(path):
    transform = from_bounds(*RASTER_BOUNDS, 5, 5)
    data = np.full((5, 5), RASTER_VALUE, dtype=np.float32)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=5,
        width=5,
        count=1,
        dtype=np.float32,
        crs="EPSG:4326",
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(data, 1)


def _write_grid_csv(path, cell_ids):
    import gzip as _gzip

    with _gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        f.write("cell_id,lat,lon\n")
        for cid in cell_ids:
            lat, lng = h3.cell_to_latlng(cid)
            f.write(f"{cid},{lat},{lng}\n")


@pytest.fixture
def raster_paths(tmp_path):
    c = tmp_path / "constrained.tif"
    u = tmp_path / "unconstrained.tif"
    _write_synthetic_raster(c)
    _write_synthetic_raster(u)
    return str(c), str(u)


@pytest.fixture
def grid_path(tmp_path, raster_paths):
    # Box fully containing the raster plus some outside area
    box = (34.98, 32.98, 35.07, 33.07)
    poly = h3.LatLngPoly(
        [(box[1], box[0]), (box[1], box[2]), (box[3], box[2]), (box[3], box[0])]
    )
    cell_ids = h3.polygon_to_cells(poly, 9)
    path = tmp_path / "grid.csv.gz"
    _write_grid_csv(path, cell_ids)
    return str(path)


def test_columns_and_year(raster_paths, grid_path):
    df = load_population(raster_paths[0], raster_paths[1], grid_path)
    assert list(df.columns) == COLUMNS
    assert (df[POP_YEAR] == 2020).all()


def test_low_not_above_high(raster_paths, grid_path):
    df = load_population(raster_paths[0], raster_paths[1], grid_path)
    both = df[df[POP_LOW].notna() & df[POP_HIGH].notna()]
    assert (both[POP_LOW] <= both[POP_HIGH]).all()


def test_outside_cell_is_null_not_zero(raster_paths, grid_path):
    df = load_population(raster_paths[0], raster_paths[1], grid_path)
    outside = df[df[POP_LOW].isna()]
    assert len(outside) > 0, "expected at least one cell fully outside the raster"
    assert (outside[POP_HIGH].isna()).all()
    assert not ((outside[POP_LOW] == 0) | (outside[POP_HIGH] == 0)).any()


def test_total_matches_raster_total(raster_paths, grid_path):
    df = load_population(raster_paths[0], raster_paths[1], grid_path)
    total_low = df[POP_LOW].sum(skipna=True)
    total_high = df[POP_HIGH].sum(skipna=True)
    # Constrained == unconstrained == same raster, so low == high
    assert abs(total_low - RASTER_TOTAL) / RASTER_TOTAL <= 0.01
    assert abs(total_high - RASTER_TOTAL) / RASTER_TOTAL <= 0.01
