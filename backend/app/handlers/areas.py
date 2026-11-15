import csv
import gzip
from pathlib import Path

from backend.app.handlers import handler
from backend.app.handlers.fixtures import load_fixture
from fastapi import Request

DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "local"
GRID_FILE = DATA_DIR / "grid_r9.csv.gz"


def _load_areas_from_grid() -> list[dict]:
    if not GRID_FILE.exists():
        return [{"area_id": "demo-area-01", "h3_id": None, "cadaster_code": None}]
    areas = []
    seen = set()
    with gzip.open(GRID_FILE, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            district = row.get("district_id")
            if district and district not in seen:
                seen.add(district)
                areas.append({
                    "area_id": district,
                    "h3_id": None,
                    "cadaster_code": None
                })
    return areas or [{"area_id": "demo-area-01", "h3_id": None, "cadaster_code": None}]


def _error_404(request: Request):
    from backend.app.api.v1 import error
    return error("REQUEST_FAILED", "Allowed resource absent; do not leak forbidden IDs", 404, request)


@handler("GET", "/areas")
async def get_areas(request: Request, path_params: dict) -> dict:
    cursor = request.query_params.get("cursor")
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    limit = int(request.query_params.get("limit", "20"))
    limit = max(1, min(limit, 100))

    areas = _load_areas_from_grid()
    paginated = areas[offset:offset + limit]
    next_cursor = str(offset + limit) if offset + limit < len(areas) else None
    return {
        "synthetic": True,
        "items": paginated,
        "next_cursor": next_cursor
    }


@handler("GET", "/areas/{area_id}/summary")
async def get_area_summary(request: Request, path_params: dict) -> dict:
    area_id = path_params.get("area_id")
    areas = _load_areas_from_grid()
    if not any(a["area_id"] == area_id for a in areas):
        return _error_404(request)
    summary = load_fixture("AreaSummary")
    summary = {**summary, "area_id": area_id, "synthetic": True}
    return summary


@handler("GET", "/areas/{area_id}/values")
async def get_area_values(request: Request, path_params: dict) -> dict:
    area_id = path_params.get("area_id")
    areas = _load_areas_from_grid()
    if not any(a["area_id"] == area_id for a in areas):
        return _error_404(request)

    metric_filter = request.query_params.get("metric")
    cursor = request.query_params.get("cursor")
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    limit = int(request.query_params.get("limit", "20"))
    limit = max(1, min(limit, 100))

    values = [load_fixture("MetricValue")]
    if metric_filter:
        values = [v for v in values if v.get("metric") == metric_filter]

    paginated = values[offset:offset + limit]
    next_cursor = str(offset + limit) if offset + limit < len(values) else None
    return {
        "synthetic": True,
        "items": paginated,
        "next_cursor": next_cursor
    }