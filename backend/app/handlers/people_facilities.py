from backend.app.handlers import handler
from fastapi import Request

SYNTHETIC_AREAS = {"demo-area-01"}

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
    """Synthetic mode serves the sample records only: never the real K-03 file stamped synthetic.
    Real facilities come from PostGIS in real-data mode (backend/app/services/facilities_real.py)."""
    return [dict(f) for f in FACILITY_FIXTURES]


def _load_population(area_id: str) -> dict:
    """Synthetic mode serves the sample range only: never the real K-04 file stamped synthetic.
    Real people ranges come from PostGIS in real-data mode (backend/app/services/areas_real.py)."""
    return {**PEOPLE_FIXTURE, "area_id": area_id}


def _error_404(request: Request):
    from backend.app.api.v1 import error
    return error("REQUEST_FAILED", "Allowed resource absent; do not leak forbidden IDs", 404, request)


@handler("GET", "/areas/{area_id}/people")
async def get_area_people(request: Request, path_params: dict) -> dict:
    area_id = path_params.get("area_id")
    if area_id not in SYNTHETIC_AREAS:
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
    if area_id not in SYNTHETIC_AREAS:
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
    if area_id not in SYNTHETIC_AREAS:
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