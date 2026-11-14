"""H3 resolution-9 grid builder (Kisara K-02).

Builds one row per H3 res-9 cell whose centre is inside the south-Lebanon demo
box, and joins each cell to its district/governorate by point-in-polygon against
the K-01 boundaries file (data/local/boundaries.geojson) when present.
"""

from __future__ import annotations

import csv
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path

import h3
from shapely.geometry import Point, shape

from worker.loaders.config import (
    BOUNDARIES_GEOJSON,
    DEMO_AOI,
    DEMO_BBOX_WGS84,
    GRID_CSV_GZ,
    GRID_MANIFEST,
    LOCAL_DIR,
    MANIFESTS_DIR,
)

CELL_ID = "cell_id"
PARENT_R8 = "parent_r8"
LAT = "lat"
LON = "lon"
DISTRICT_ID = "district_id"
GOVERNORATE_ID = "governorate_id"
COLUMNS = [CELL_ID, PARENT_R8, LAT, LON, DISTRICT_ID, GOVERNORATE_ID]

RESOLUTION = 9
PARENT_RESOLUTION = 8


def _load_boundary_polygons(path):
    """Return list of dicts with admin_id, name_en, level, shapely geometry."""
    path = Path(path)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for feature in data.get("features", []):
        props = feature.get("properties") or {}
        geom = feature.get("geometry")
        if geom is None:
            continue
        try:
            shapely_geom = shape(geom)
        except Exception:
            continue
        if shapely_geom.is_empty:
            continue
        out.append(
            {
                "admin_id": props.get("admin_id"),
                "name_en": props.get("name_en"),
                "level": props.get("level"),
                "geometry": shapely_geom,
            }
        )
    return out


def _cells_in_box(west, south, east, north, resolution):
    """H3 cells whose centre falls inside the WGS84 box (lng, lat)."""
    poly = h3.LatLngPoly([(south, west), (south, east), (north, east), (north, west)])
    cell_ids = h3.polygon_to_cells(poly, resolution)
    cells = []
    for cell_id in cell_ids:
        lat, lng = h3.cell_to_latlng(cell_id)
        if west <= lng <= east and south <= lat <= north:
            cells.append((cell_id, lat, lng))
    return cells


def build_grid(boundaries_path=None, box=None, resolution=RESOLUTION):
    """Build the res-9 grid for the demo box.

    Returns a list of row dicts with columns cell_id, parent_r8, lat, lon,
    district_id, governorate_id. Cells outside every district keep
    district_id = None (never a guess).
    """
    if box is None:
        west, south, east, north = DEMO_BBOX_WGS84
    else:
        west, south, east, north = box

    boundaries = _load_boundary_polygons(boundaries_path or BOUNDARIES_GEOJSON)
    districts = [b for b in boundaries if b["level"] == 2]
    governorates = [b for b in boundaries if b["level"] == 1]

    rows = []
    for cell_id, lat, lng in _cells_in_box(west, south, east, north, resolution):
        point = Point(lng, lat)
        district_id = None
        governorate_id = None
        for d in districts:
            if d["geometry"].covers(point):
                district_id = d["admin_id"]
                break
        for g in governorates:
            if g["geometry"].covers(point):
                governorate_id = g["admin_id"]
                break
        rows.append(
            {
                CELL_ID: cell_id,
                PARENT_R8: h3.cell_to_parent(cell_id, PARENT_RESOLUTION),
                LAT: lat,
                LON: lng,
                DISTRICT_ID: district_id,
                GOVERNORATE_ID: governorate_id,
            }
        )
    rows.sort(key=lambda r: r[CELL_ID])
    return rows


def _write_csv_gz(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_manifest(cell_count, path):
    west, south, east, north = DEMO_BBOX_WGS84
    manifest = {
        "kind": "grid_manifest",
        "aoi": DEMO_AOI,
        "bbox_wgs84": {"west": west, "south": south, "east": east, "north": north},
        "resolution": RESOLUTION,
        "cell_count": cell_count,
        "h3_version": h3.__version__,
        "columns": COLUMNS,
        "generated_date": datetime.now(timezone.utc).date().isoformat(),
        "output": str(path),
    }
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_grid_file(boundaries_path=None, output=None, manifest_path=None):
    """Build grid and write data/local/grid_r9.csv.gz + data/manifests/grid.json."""
    output = Path(output or GRID_CSV_GZ)
    manifest_path = Path(manifest_path or GRID_MANIFEST)
    rows = build_grid(boundaries_path=boundaries_path)
    _write_csv_gz(rows, output)
    _write_manifest(len(rows), manifest_path)
    print(f"wrote {output} ({len(rows)} cells)")
    print(f"wrote {manifest_path}")
    return rows


if __name__ == "__main__":
    build_grid_file()
