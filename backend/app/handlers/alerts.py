import json
from datetime import UTC, datetime

from backend.app.handlers import handler
from backend.app.handlers.fixtures import load_fixture
from fastapi import Request

ALERT_FIXTURE = load_fixture("AlertDetail")


def _make_alert(alert_id: str, alert_type: str, title: str, area_id: str = "demo-area-01") -> dict:
    base = json.loads(json.dumps(ALERT_FIXTURE))
    base["alert_id"] = alert_id
    base["area_id"] = area_id
    base["type"] = alert_type
    base["title"] = title
    base["detected_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    base["processed_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    base["release_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    base["cause"] = "Unknown"
    base["warning"] = "Synthetic signal; CIVISAR does not determine a cause."
    if alert_type == "fire_detected":
        base["label"] = "Reported"
        base["satellite"] = "NOAA-20"
        base["product"] = "VJ114IMGTDL_NRT"
    elif alert_type == "possible_power_loss":
        base["label"] = "Corroborated"
        base["satellite"] = "Suomi-NPP"
        base["product"] = "VNP46A1"
    else:
        base["label"] = "Unknown"
        base["satellite"] = "Unknown"
        base["product"] = "Unknown"
    return base


ALERTS = [
    _make_alert("demo-alert-01", "fire_detected", "Fire detected (synthetic demonstration)"),
    _make_alert("demo-alert-02", "possible_power_loss", "Possible power loss (synthetic demonstration)"),
    _make_alert("demo-alert-03", "fire_detected", "Fire detected (synthetic demonstration)"),
]


def _parse_since(since_str: str | None) -> datetime | None:
    if not since_str:
        return None
    try:
        if since_str.endswith("Z"):
            since_str = since_str[:-1] + "+00:00"
        return datetime.fromisoformat(since_str)
    except ValueError:
        return None


def _filter_alerts(
    area_id: str | None,
    alert_type: str | None,
    since: str | None,
) -> list[dict]:
    since_dt = _parse_since(since)
    result = []
    for alert in ALERTS:
        if area_id and alert.get("area_id") != area_id:
            continue
        if alert_type and alert.get("type") != alert_type:
            continue
        if since_dt:
            detected_at = alert.get("detected_at")
            if detected_at:
                try:
                    if detected_at.endswith("Z"):
                        detected_at = detected_at[:-1] + "+00:00"
                    alert_dt = datetime.fromisoformat(detected_at)
                    if alert_dt < since_dt:
                        continue
                except ValueError:
                    pass
        result.append(alert)
    return result


def _error_404(request: Request):
    from backend.app.api.v1 import error
    return error("REQUEST_FAILED", "Allowed resource absent; do not leak forbidden IDs", 404, request)


def _error_422(request: Request, message: str):
    from backend.app.api.v1 import error
    return error("REQUEST_FAILED", message, 422, request)


@handler("GET", "/alerts")
async def get_alerts(request: Request, path_params: dict) -> dict:
    area_id = request.query_params.get("area_id")
    alert_type = request.query_params.get("type")
    since = request.query_params.get("since")
    cursor = request.query_params.get("cursor")
    limit_str = request.query_params.get("limit", "20")

    try:
        limit = int(limit_str)
        limit = max(1, min(limit, 100))
    except ValueError:
        return _error_422(request, "Invalid limit parameter")

    if _parse_since(since) is None and since:
        return _error_422(request, "Invalid since parameter; use ISO 8601 format")

    filtered = _filter_alerts(area_id, alert_type, since)

    offset = 0
    if cursor and cursor.isdigit():
        offset = int(cursor)

    paginated = filtered[offset:offset + limit]
    next_cursor = str(offset + limit) if offset + limit < len(filtered) else None

    return {
        "synthetic": True,
        "items": paginated,
        "next_cursor": next_cursor,
    }


@handler("GET", "/alerts/{alert_id}")
async def get_alert(request: Request, path_params: dict) -> dict:
    alert_id = path_params.get("alert_id")
    for alert in ALERTS:
        if alert.get("alert_id") == alert_id:
            return alert
    return _error_404(request)