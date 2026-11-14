"""Lebanon administrative boundaries loader 

Reads the OCHA COD-AB download, keeps admin levels 1 (governorate) and 2
(district), clips to the south-Lebanon demo box, and writes a small
GeoJSON plus a manifest. The raw download is read locally and is never
committed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from worker.loaders.config import (
    ADMIN1_FILENAME,
    ADMIN2_FILENAME,
    BOUNDARIES_GEOJSON,
    BOUNDARIES_MANIFEST,
    DEMO_AOI,
    DEMO_BBOX_WGS84,
    HDX_DATASET_ID,
    HDX_DATASET_NAME,
    LICENCE,
    LICENCE_URL,
    LOCAL_DIR,
    MANIFESTS_DIR,
    MAX_OUTPUT_BYTES,
    RAW_DIR,
    SOURCE_URL,
)

ADMIN_ID = "admin_id"
NAME_EN = "name_en"
NAME_AR = "name_ar"
LEVEL = "level"
PARENT_ID = "parent_id"
KEEP_COLUMNS = [ADMIN_ID, NAME_EN, NAME_AR, LEVEL, PARENT_ID, "geometry"]

# OCHA COD-AB source columns -> standard output columns, per admin level.
_LEVEL_2_SOURCE = {
    ADMIN_ID: "adm2_pcode",
    NAME_EN: "adm2_name",
    NAME_AR: "adm2_name1",
    PARENT_ID: "adm1_pcode",
}
_LEVEL_1_SOURCE = {
    ADMIN_ID: "adm1_pcode",
    NAME_EN: "adm1_name",
    NAME_AR: "adm1_name1",
    PARENT_ID: "adm0_pcode",
}


def _clean(value) -> str | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return text or None


def _detect_level(row: pd.Series) -> int | None:
    if pd.notna(row.get("adm2_pcode")):
        return 2
    if pd.notna(row.get("adm1_pcode")):
        return 1
    if pd.notna(row.get("level")):
        try:
            return int(row["level"])  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
    return None


def _standardize(frame: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    rows = []
    for _, row in frame.iterrows():
        level = _detect_level(row)
        if level not in (1, 2):
            continue
        src = _LEVEL_2_SOURCE if level == 2 else _LEVEL_1_SOURCE
        admin_id = row.get(src[ADMIN_ID])
        if pd.isna(admin_id) or str(admin_id).strip() == "":
            continue
        geom = row.get("geometry")
        if geom is None or geom.is_empty:
            continue
        parent = row.get(src[PARENT_ID])
        rows.append(
            {
                ADMIN_ID: str(admin_id),
                NAME_EN: _clean(row.get(src[NAME_EN])),
                NAME_AR: _clean(row.get(src[NAME_AR])),
                LEVEL: level,
                PARENT_ID: _clean(parent),
                "geometry": geom,
            }
        )
    return gpd.GeoDataFrame(rows, columns=KEEP_COLUMNS, crs="EPSG:4326")


def _read_source(source: Path | None = None) -> gpd.GeoDataFrame:
    if source is None:
        source = RAW_DIR
    source = Path(source)
    if source.is_dir():
        files = [source / ADMIN1_FILENAME, source / ADMIN2_FILENAME]
        files = [p for p in files if p.exists()]
        if not files:
            files = sorted(source.glob("*.geojson"))
    elif source.is_file():
        files = [source]
    else:
        raise FileNotFoundError(f"boundaries source not found: {source}")
    frames = [gpd.read_file(f) for f in files]
    crs = frames[0].crs or "EPSG:4326"
    combined = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=crs)
    return combined


def _clip_to_demo(frame: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    west, south, east, north = DEMO_BBOX_WGS84
    demo = gpd.GeoDataFrame(geometry=[box(west, south, east, north)], crs="EPSG:4326")
    return gpd.clip(frame, demo)


def _simplify_to_limit(frame: gpd.GeoDataFrame, max_bytes: int) -> gpd.GeoDataFrame:
    tolerance = 0.00005
    result = frame
    for _ in range(25):
        trial = result.copy()
        trial["geometry"] = trial.geometry.simplify(tolerance, preserve_topology=True)
        trial = trial[~trial.geometry.is_empty].copy()
        size = len(trial.to_json().encode("utf-8"))
        if size <= max_bytes:
            return trial
        tolerance *= 2
        result = trial
    return result


def _write_manifest(row_count: int) -> None:
    west, south, east, north = DEMO_BBOX_WGS84
    manifest = {
        "kind": "boundaries_manifest",
        "aoi": DEMO_AOI,
        "bbox_wgs84": {"west": west, "south": south, "east": east, "north": north},
        "source_url": SOURCE_URL,
        "dataset": HDX_DATASET_NAME,
        "dataset_id": HDX_DATASET_ID,
        "download_date": datetime.now(timezone.utc).date().isoformat(),
        "licence": LICENCE,
        "licence_url": LICENCE_URL,
        "row_count": row_count,
        "admin_levels": [1, 2],
        "fields": KEEP_COLUMNS,
        "output": str(BOUNDARIES_GEOJSON),
    }
    BOUNDARIES_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def load_boundaries(
    source: str | Path | None = None,
    write_outputs: bool = True,
) -> gpd.GeoDataFrame:
    """Load Lebanon governorate/district boundaries clipped to the demo box.

    Reads the OCHA COD-AB download (admin levels 0-3), keeps levels 1 and 2,
    clips to the south-Lebanon demo box, simplifies geometry to under 1 MB,
    and (by default) writes data/local/boundaries.geojson plus
    data/manifests/boundaries.json. The raw download is read locally and is
    never committed.
    """
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

    frame = _read_source(source)
    frame = _standardize(frame)
    frame = _clip_to_demo(frame)
    frame = frame[~frame.geometry.is_empty].copy()
    frame = frame[KEEP_COLUMNS].reset_index(drop=True)

    frame = _simplify_to_limit(frame, MAX_OUTPUT_BYTES)
    if write_outputs:
        frame.to_file(BOUNDARIES_GEOJSON, driver="GeoJSON")
        _write_manifest(len(frame))
        print(f"wrote {BOUNDARIES_GEOJSON} ({len(frame)} rows)")
        print(f"wrote {BOUNDARIES_MANIFEST}")
    return frame


if __name__ == "__main__":
    load_boundaries()
