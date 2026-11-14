"""Population-per-cell loader (Kisara K-04).

Sums WorldPop Lebanon 2020 rasters (constrained and unconstrained) inside each
H3 res-9 cell and returns a DataFrame with cell_id, pop_low, pop_high, pop_year.
pop_low = min(constrained, unconstrained), pop_high = max(constrained, unconstrained).
Never a single exact number: cells outside a raster get null, never 0.
"""

from __future__ import annotations

import csv
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask
from shapely.geometry import Polygon, mapping

import h3

from worker.loaders.config import (
    DEMO_AOI,
    DEMO_BBOX_WGS84,
    DATA_DIR,
    GRID_CSV_GZ,
    LOCAL_DIR,
    MANIFESTS_DIR,
    POPULATION_CSV_GZ,
    POPULATION_MANIFEST,
    ROOT,
)

CELL_ID = "cell_id"
POP_LOW = "pop_low"
POP_HIGH = "pop_high"
POP_YEAR = "pop_year"
COLUMNS = [CELL_ID, POP_LOW, POP_HIGH, POP_YEAR]

POP_YEAR_VALUE = 2020
RAW_DIR = DATA_DIR / "raw" / "worldpop"
CONSTRAINED_RASTER = RAW_DIR / "worldpop_lebanon_2020_constrained.tif"
UNCONSTRAINED_RASTER = RAW_DIR / "worldpop_lebanon_2020_unconstrained.tif"

CONSTRAINED_PRODUCT = "WorldPop Global Project Population Density 2020 (constrained)"
UNCONSTRAINED_PRODUCT = "WorldPop Global Project Population Density 2020 (unconstrained)"
POPULATION_LICENCE = "CC BY 4.0"


def _read_grid(grid_path):
    """Read cell_id, lat, lon from the K-02 grid CSV."""
    import gzip as _gzip
    path = Path(grid_path)
    cells = []
    with _gzip.open(path, "rt", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cells.append(
                {
                    "cell_id": row["cell_id"],
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                }
            )
    return cells


def _cell_polygon(cell_id):
    """H3 cell boundary as a shapely Polygon (lng, lat)."""
    boundary = h3.cell_to_boundary(cell_id)
    return Polygon([(lng, lat) for lat, lng in boundary])


def _bounds_intersect(geom_bounds, src_bounds):
    """True if geometry bounds overlap raster bounds."""
    return not (
        geom_bounds[2] < src_bounds[0]
        or geom_bounds[0] > src_bounds[2]
        or geom_bounds[3] < src_bounds[1]
        or geom_bounds[1] > src_bounds[3]
    )


def _zonal_sum(src, geom):
    """Sum raster band values inside a geometry. None if no overlap."""
    if not _bounds_intersect(geom.bounds, src.bounds):
        return None
    try:
        out_image, _ = mask(src, [mapping(geom)], crop=True, nodata=src.nodata)
    except (ValueError, rasterio.errors.RasterioIOError):
        return None
    band = out_image[0]
    if np.ma.is_masked(band):
        valid = band.compressed()
    else:
        valid = band[~np.isnan(band)] if src.nodata is None else band[band != src.nodata]
    if valid.size == 0:
        return None
    return float(np.nansum(valid))


def load_population(
    constrained_path=None,
    unconstrained_path=None,
    grid_path=None,
):
    """Load population per H3 res-9 cell as a DataFrame.

    Columns: cell_id, pop_low, pop_high, pop_year.
    pop_low = min(constrained, unconstrained); pop_high = max(...).
    Cells outside a raster get null (never 0).
    """
    if grid_path is None:
        grid_path = GRID_CSV_GZ
    if constrained_path is None:
        constrained_path = CONSTRAINED_RASTER
    if unconstrained_path is None:
        unconstrained_path = UNCONSTRAINED_RASTER

    cells = _read_grid(grid_path)

    with rasterio.open(constrained_path) as c_src, rasterio.open(
        unconstrained_path
    ) as u_src:
        rows = []
        for cell in cells:
            geom = _cell_polygon(cell["cell_id"])
            c_sum = _zonal_sum(c_src, geom)
            u_sum = _zonal_sum(u_src, geom)

            if c_sum is None and u_sum is None:
                pop_low = None
                pop_high = None
            elif c_sum is None:
                pop_low = u_sum
                pop_high = u_sum
            elif u_sum is None:
                pop_low = c_sum
                pop_high = c_sum
            else:
                pop_low = min(c_sum, u_sum)
                pop_high = max(c_sum, u_sum)

            rows.append(
                {
                    CELL_ID: cell["cell_id"],
                    POP_LOW: round(pop_low) if pop_low is not None else None,
                    POP_HIGH: round(pop_high) if pop_high is not None else None,
                    POP_YEAR: POP_YEAR_VALUE,
                }
            )

    return pd.DataFrame(rows, columns=COLUMNS)


def _write_csv_gz(df, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, compression="gzip")


def _write_manifest(df, path):
    west, south, east, north = DEMO_BBOX_WGS84
    total_low = df[POP_LOW].sum(skipna=True)
    total_high = df[POP_HIGH].sum(skipna=True)
    manifest = {
        "kind": "population_manifest",
        "aoi": DEMO_AOI,
        "bbox_wgs84": {"west": west, "south": south, "east": east, "north": north},
        "pop_year": POP_YEAR_VALUE,
        "products": [
            {"name": CONSTRAINED_PRODUCT, "path": str(CONSTRAINED_RASTER.relative_to(ROOT))},
            {"name": UNCONSTRAINED_PRODUCT, "path": str(UNCONSTRAINED_RASTER.relative_to(ROOT))},
        ],
        "licence": POPULATION_LICENCE,
        "generated_date": datetime.now(timezone.utc).date().isoformat(),
        "cell_count": int(len(df)),
        "cells_with_data": int(df[POP_LOW].notna().sum()),
        "total_low": round(float(total_low)) if pd.notna(total_low) else None,
        "total_high": round(float(total_high)) if pd.notna(total_high) else None,
        "columns": COLUMNS,
        "output": str(path.relative_to(ROOT)),
    }
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def load_population_file(
    constrained_path=None, unconstrained_path=None, grid_path=None, output=None, manifest_path=None
):
    """Load population and write data/local/population.csv.gz + manifest."""
    output = Path(output or POPULATION_CSV_GZ)
    manifest_path = Path(manifest_path or POPULATION_MANIFEST)
    df = load_population(
        constrained_path=constrained_path,
        unconstrained_path=unconstrained_path,
        grid_path=grid_path,
    )
    _write_csv_gz(df, output)
    _write_manifest(df, manifest_path)
    print(f"wrote {output} ({len(df)} cells)")
    print(f"wrote {manifest_path}")
    return df


if __name__ == "__main__":
    load_population_file()
