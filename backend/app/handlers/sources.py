import json
from pathlib import Path

from backend.app.handlers import handler
from backend.app.handlers.fixtures import load_fixture
from fastapi import Request

MANIFESTS_DIR = Path(__file__).resolve().parents[3] / "data" / "manifests"
SOURCES_MANIFEST = MANIFESTS_DIR / "sources.json"

# may have to apply offset and limit to the sources list if it is large
def _load_sources_list() -> list[dict]:
    if SOURCES_MANIFEST.exists():
        return json.loads(SOURCES_MANIFEST.read_text(encoding="utf-8"))
    return [load_fixture("SourceRecord")]


@handler("GET", "/status")
async def get_status(request: Request, path_params: dict) -> dict:
    sources_list = _load_sources_list()
    sources_status = []
    for src in sources_list:
        src_id = src.get("source_id") or src.get("dataset_id") or "unknown"
        accessed_at = src.get("accessed_at")
        is_synthetic = src.get("synthetic", True)

        if is_synthetic:
            freshness = "Stale"
            failure = "Not configured"

        else:
            freshness = "Fresh" if accessed_at else "Stale"
            failure = None
        
        sources_status.append({
            "id": src_id,
            "acquired_at": None,
            "processed_at": None,
            "last_success_at": accessed_at,
            "freshness": freshness,
            "cached": True,
            "failure": failure
        })
    return {
        "synthetic": True,
        "sources": sources_status
    }


@handler("GET", "/sources")
async def get_sources(request: Request, path_params: dict) -> dict:
    sources_list = _load_sources_list()
    cursor = request.query_params.get("cursor")
    offset = int(cursor) if cursor and cursor.isdigit() else 0
    limit = 20
    paginated = sources_list[offset:offset + limit]
    next_cursor = str(offset + limit) if offset + limit < len(sources_list) else None
    return {
        "synthetic": True,
        "items": paginated,
        "next_cursor": next_cursor
    }


@handler("GET", "/sources/{source_id}")
async def get_source(request: Request, path_params: dict) -> dict:
    source_id = path_params.get("source_id")
    sources_list = _load_sources_list()
    for src in sources_list:
        if src.get("source_id") == source_id:
            return {**src, "synthetic": True}
    from backend.app.api.v1 import error
    return error("REQUEST_FAILED", "Allowed resource absent; do not leak forbidden IDs", 404, request)