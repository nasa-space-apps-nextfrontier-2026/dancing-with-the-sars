import csv
import gzip
from pathlib import Path

from backend.app.handlers import handler
from fastapi import Request

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "local"
FACILITIES_FILE = DATA_DIR / "facilities.csv"
POPULATION_FILE = DATA_DIR / "population.csv.gz"

EXCLUDED_FACILITY_TAGS = {
    "military", "police", "prison",
    "amenity=police", "amenity=prison", "military=*"
}

FACILITY_FIXTURES = [
    {
        "facility_id": "demo-facility-01",
        "type": "clinic",
        "operating_status": "Unknown",
        "damage_status": "No detected damage. Not confirmed open.",
        "label": "Unknown",
        "source": ["OpenStreetMap contributors"],
        "date": None,
        "geometry": None
    },
    {
        "facility_id": "demo-facility-02",
        "type": "hospital",
        "operating_status": "Unknown",
        "damage_status": "No detected damage. Not confirmed open.",
        "label": "Unknown",
        "source": ["OpenStreetMap contributors"],
        "date": None,
        "geometry": None
    }
]

PEOPLE_FIXTURE = {
    "synthetic": True,
    "value_id": "demo-value-people",
    "area_id": "demo-area-01",
    "metric": "residents_baseline",
    "low": 1200,
    "high": 1800,
    "unit": "people",
    "label": "Unknown",
    "source": ["demo-source-01"],
    "date": "2026-01-01",
    "safety_tag": "restricted_aggregate",
    "lineage_ids": ["demo-lineage-01"],
    "processing_run_id": "demo-run-01",
    "processing_version": "demo-v1",
    "confidence": None,
    "acquired_at": "2026-01-01T00:00:00Z",
    "processed_at": "2026-06-25T00:00:00Z",
    "release_at": "2026-06-27T00:00:00Z",
    "freshness": "Stale",
    "cached": True,
    "limitations": ["Synthetic range; no measured population."]
}


def _load_facilities() -> list[dict]:
    if not FACILITIES_FILE.exists():
        return FACILITY_FIXTURES
    facilities = []
    with open(FACILITIES_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            f_type = row.get("type", "").lower()
            if any(tag in f_type for tag in ["military", "police", "prison"]):
                continue
            facilities.append({
                "facility_id": row.get("facility_id"),
                "type": row.get("type"),
                "operating_status": row.get("status", "Unknown"),
                "damage_status": "No detected damage. Not confirmed open.",
                "label": "Unknown",
                "source": [row.get("source", "OpenStreetMap contributors")],
                "date": row.get("osm_timestamp"),
                "geometry": None
            })
    return facilities or FACILITY_FIXTURES


def _load_population(area_id: str) -> dict:
    if not POPULATION_FILE.exists():
        fixture = {**PEOPLE_FIXTURE, "area_id": area_id}
        return fixture
    pop_low = 0
    pop_high = 0
    with gzip.open(POPULATION_FILE, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("cell_id") and area_id in row.get("cell_id", ""):
                low = row.get("pop_low")
                high = row.get("pop_high")
                if low and low != "null":
                    pop_low += int(low)
                if high and high != "null":
                    pop_high += int(high)
    if pop_low == 0 and pop_high == 0:
        fixture = {**PEOPLE_FIXTURE, "area_id": area_id}
        return fixture
    return {
        "synthetic": True,
        "value_id": f"pop-{area_id}",
        "area_id": area_id,
        "metric": "residents_baseline",
        "low": pop_low,
        "high": pop_high,
        "unit": "people",
        "label": "Unknown",
        "source": ["WorldPop constrained/unconstrained"],
        "date": "2020",
        "safety_tag": "restricted_aggregate",
        "lineage_ids": [],
        "processing_run_id": "demo-run-01",
        "processing_version": "demo-v1",
        "confidence": None,
        "acquired_at": "2020-01-01T00:00:00Z",
        "processed_at": "2026-06-25T00:00:00Z",
        "release_at": "2026-06-27T00:00:00Z",
        "freshness": "Stale",
        "cached": True,
        "limitations": ["Aggregated from WorldPop rasters; range only."]
    }


def _error_404(request: Request):
    from backend.app.api.v1 import error
    return error("REQUEST_FAILED", "Allowed resource absent; do not leak forbidden IDs", 404, request)


@handler("GET", "/areas/{area_id}/people")
async def get_area_people(request: Request, path_params: dict) -> dict:
    area_id = path_params.get("area_id")
    areas = []
    if (DATA_DIR / "grid_r9.csv.gz").exists():
        import csv as _csv
        import gzip as _gzip
        with _gzip.open(DATA_DIR / "grid_r9.csv.gz", "rt", encoding="utf-8") as f:
            reader = _csv.DictReader(f)
            for row in reader:
                district = row.get("district_id")
                if district:
                    areas.append(district)
    areas = list(set(areas)) or ["demo-area-01"]
    if area_id not in areas:
        return _error_404(request)

    pop = _load_population(area_id)
    return {
        "synthetic": True,
        "items": [pop],
        "next_cursor": None
    }


@handler("GET", "/areas/{area_id}/services")
async def get_area_services(request: Request, path_params: dict) -> dict:
    area_id = path_params.get("area_id")
    areas = []
    if (DATA_DIR / "grid_r9.csv.gz").exists():
        import csv as _csv
        import gzip as _gzip
        with _gzip.open(DATA_DIR / "grid_r9.csv.gz", "rt", encoding="utf-8") as f:
            reader = _csv.DictReader(f)
            for row in reader:
                district = row.get("district_id")
                if district:
                    areas.append(district)
    areas = list(set(areas)) or ["demo-area-01"]
    if area_id not in areas:
        return _error_404(request)

    return {
        "synthetic": True,
        "items": [],
        "next_cursor": None,
        "message": "No service-loss data yet"
    }


@handler("GET", "/areas/{area_id}/facilities")
async def get_area_facilities(request: Request, path_params: dict) -> dict:
    area_id = path_params.get("area_id")
    areas = []
    if (DATA_DIR / "grid_r9.csv.gz").exists():
        import csv as _csv
        import gzip as _gzip
        with _gzip.open(DATA_DIR / "grid_r9.csv.gz", "rt", encoding="utf-8") as f:
            reader = _csv.DictReader(f)
            for row in reader:
                district = row.get("district_id")
                if district:
                    areas.append(district)
    areas = list(set(areas)) or ["demo-area-01"]
    if area_id not in areas:
        return _error_404(request)

    facility_type = request.query_params.get("type")
    cursor = request.query_params.get("cursor")
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    limit = int(request.query_params.get("limit", "20"))
    limit = max(1, min(limit, 100))

    facilities = _load_facilities()
    if facility_type:
        facilities = [f for f in facilities if f.get("type", "").lower() == facility_type.lower()]

    paginated = facilities[offset:offset + limit]
    next_cursor = str(offset + limit) if offset + limit < len(facilities) else None
    return {
        "synthetic": True,
        "items": paginated,
        "next_cursor": next_cursor
    }