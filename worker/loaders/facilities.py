"""OpenStreetMap facilities loader (Kisara K-03).

Loads health, school, water and power sites in the south-Lebanon demo box
from the Overpass API (or a saved Overpass response for tests), maps OSM
tags to a facility type, joins each facility to its H3 res-9 cell, and
writes data/local/facilities.csv plus data/manifests/facilities.json.

Excluded tags (never loaded): military=*, amenity=police, amenity=prison
and any other military / police / prison / government-security tags.
"""

from __future__ import annotations

import csv
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import h3

from worker.loaders.config import (
    DEMO_AOI,
    DEMO_BBOX_WGS84,
    FACILITIES_CSV,
    FACILITIES_MANIFEST,
    LOCAL_DIR,
    MANIFESTS_DIR,
)

FACILITY_ID = "facility_id"
TYPE = "type"
NAME = "name"
LAT = "lat"
LON = "lon"
CELL_ID = "cell_id"
SOURCE = "source"
OSM_TIMESTAMP = "osm_timestamp"
STATUS = "status"
STATUS_SOURCE = "status_source"
COLUMNS = [
    FACILITY_ID,
    TYPE,
    NAME,
    LAT,
    LON,
    CELL_ID,
    SOURCE,
    OSM_TIMESTAMP,
    STATUS,
    STATUS_SOURCE,
]

SOURCE_CREDIT = "OpenStreetMap contributors"
LICENCE = "Open Data Commons Open Database License (ODbL)"
RESOLUTION = 9

# Overpass end-point used for the real run.
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Tag -> facility type. Only these five types are emitted.
_TAG_TO_TYPE = {
    "amenity=hospital": "hospital",
    "healthcare=hospital": "hospital",
    "amenity=clinic": "clinic",
    "healthcare=clinic": "clinic",
    "amenity=school": "school",
    "man_made=water_tower": "water",
    "man_made=water_well": "water",
    "power=substation": "power",
    "power=plant": "power",
}

# Excluded tag keys / values (never loaded).
_EXCLUDED_KEYS = ("military",)
_EXCLUDED_VALUES = {
    ("amenity", "police"),
    ("amenity", "prison"),
}


def _is_excluded(tags):
    """True if the OSM element carries an excluded tag."""
    for key in _EXCLUDED_KEYS:
        if key in tags:
            return True
    for k, v in _EXCLUDED_VALUES:
        if tags.get(k) == v:
            return True
    return False


def _type_from_tags(tags):
    """Return one of hospital/clinic/school/water/power, or None."""
    if _is_excluded(tags):
        return None
    for tag, ftype in _TAG_TO_TYPE.items():
        key, val = tag.split("=", 1)
        if tags.get(key) == val:
            return ftype
    return None


def _element_lat_lon(element):
    """Best-effort lat/lon for a node/way/relation element."""
    if "lat" in element and "lon" in element:
        return float(element["lat"]), float(element["lon"])
    center = element.get("center") or {}
    if "lat" in center and "lon" in center:
        return float(center["lat"]), float(center["lon"])
    return None, None


def _parse_elements(elements):
    """Convert Overpass elements into facility row dicts."""
    rows = []
    for element in elements:
        tags = element.get("tags") or {}
        ftype = _type_from_tags(tags)
        if ftype is None:
            continue
        lat, lon = _element_lat_lon(element)
        if lat is None or lon is None:
            continue
        osm_id = element.get("id")
        elem_type = element.get("type", "node")
        facility_id = f"osm:{ftype}{osm_id}"
        name = tags.get("name")
        timestamp = tags.get("timestamp") or element.get("timestamp")
        rows.append(
            {
                FACILITY_ID: facility_id,
                TYPE: ftype,
                NAME: name,
                LAT: lat,
                LON: lon,
                CELL_ID: h3.latlng_to_cell(lat, lon, RESOLUTION),
                SOURCE: SOURCE_CREDIT,
                OSM_TIMESTAMP: timestamp,
                STATUS: "Unknown",
                STATUS_SOURCE: None,
            }
        )
    return rows


def _overpass_query(west, south, east, north):
    """Build an Overpass QL query for the demo box."""
    filters = []
    for tag in _TAG_TO_TYPE:
        key, val = tag.split("=", 1)
        for kind in ("node", "way", "relation"):
            filters.append(f'{kind}["{key}"="{val}"]({south},{west},{north},{east});')
    body = "[out:json][timeout:25];(" + "".join(filters) + ");out center;"
    return body


def _fetch_overpass(west, south, east, north):
    """Query the Overpass API and return its parsed JSON response."""
    body = _overpass_query(west, south, east, north)
    req = urllib.request.Request(
        OVERPASS_URL,
        data=body.encode("utf-8"),
        headers={
            "User-Agent": "kilo-k03/1.0 (research)",
            "Content-Type": "application/octet-stream",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_facilities(source=None):
    """Load facilities as a list of dicts.

    ``source`` may be a path to a saved Overpass response JSON (used by tests)
    or None to query the Overpass API for the demo box (real run).
    """
    if source is None:
        west, south, east, north = DEMO_BBOX_WGS84
        data = _fetch_overpass(west, south, east, north)
    else:
        source = Path(source)
        data = json.loads(source.read_text(encoding="utf-8"))

    elements = data.get("elements", []) if isinstance(data, dict) else []
    rows = _parse_elements(elements)
    rows.sort(key=lambda r: r[FACILITY_ID])
    return rows


def _counts_by_type(rows):
    counts = {}
    for r in rows:
        counts[r[TYPE]] = counts.get(r[TYPE], 0) + 1
    return counts


def _write_csv(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_manifest(counts, total, path, query_note):
    west, south, east, north = DEMO_BBOX_WGS84
    manifest = {
        "kind": "facilities_manifest",
        "aoi": DEMO_AOI,
        "bbox_wgs84": {"west": west, "south": south, "east": east, "north": north},
        "query": query_note,
        "source": "OpenStreetMap (Overpass API)",
        "credit": SOURCE_CREDIT,
        "licence": LICENCE,
        "generated_date": datetime.now(timezone.utc).date().isoformat(),
        "count_per_type": counts,
        "total": total,
        "columns": COLUMNS,
        "output": str(path),
    }
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def load_facilities_file(source=None, output=None, manifest_path=None):
    """Load facilities and write data/local/facilities.csv + manifest."""
    output = Path(output or FACILITIES_CSV)
    manifest_path = Path(manifest_path or FACILITIES_MANIFEST)
    rows = load_facilities(source)
    _write_csv(rows, output)
    counts = _counts_by_type(rows)
    query_note = (
        f"Overpass API, demo box {DEMO_BBOX_WGS84}, tags: "
        + ", ".join(sorted(_TAG_TO_TYPE))
        + "; excluded: military=*, amenity=police, amenity=prison"
    )
    _write_manifest(counts, len(rows), manifest_path, query_note)
    print(f"wrote {output} ({len(rows)} facilities)")
    print(f"wrote {manifest_path}")
    return rows


if __name__ == "__main__":
    load_facilities_file()
