"""Real-data radar routes (DEMO_SYNTHETIC=false). Called by v1.py after its access check.

Returns None for paths it does not handle, so v1.py falls through to its own behaviour.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from functools import lru_cache
from typing import Any

from backend.app.core.security import Identity
from backend.app.services import radar_real
from fastapi import Request
from fastapi.responses import Response

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RADAR_PATHS = {
    "/layers",
    "/layers/{layer_id}",
    "/layers/{layer_id}/tiles/{z}/{x}/{y}",
    "/layers/{layer_id}/files/{file_id}",
    "/layers/{layer_id}/timeseries",
    "/areas/{area_id}/damage",
    "/values/{value_id}/trace",
}
LIVE_PATHS = {"/alerts", "/alerts/{alert_id}", "/status"}
AREA_PATHS = {
    "/areas",
    "/areas/{area_id}/values",
    "/areas/{area_id}/people",
    "/areas/{area_id}/services",
    "/areas/{area_id}/validation",
    "/areas/{area_id}/facilities",
    "/sources",
    "/sources/{source_id}",
}
ADMIN_PATHS = {
    "/admin/audit",
    "/admin/users/{user_id}/roles",
    "/admin/jobs/{job_id}/retry",
    "/alerts/{alert_id}/reviews",
}
BRIEF_PATHS = {
    "/areas/{area_id}/summary",
    "/briefs",
    "/briefs/{report_id}",
    "/briefs/{report_id}/print",
}
AGENT_PATHS = {"/incidents", "/incidents/{incident_id}", "/areas/{area_id}/budget", "/buildings"}
UNAVAILABLE_PATHS = {
    "/routes",
    "/routes/{route_id}",
    "/routes/{route_id}/status",
    "/closures",
    "/closures/{closure_id}/review",
    "/shelters",
    "/shelters/capacity",
    "/shelters/{candidate_id}/field-checks",
}


@lru_cache(maxsize=1)
def engine() -> Any:
    from backend.app.db.base import make_engine

    return make_engine()


async def handle(
    request: Request,
    path: str,
    identity: Identity | None,
    error: Callable[[str, str, int, Request], Response],
) -> Any:
    if path == "/public/map":
        from backend.app.services import public_map_real

        raw_bbox = request.query_params.get("bbox")
        if raw_bbox:
            try:
                west, south, east, north = (float(value) for value in raw_bbox.split(","))
            except ValueError:
                return error("INVALID_REQUEST", "bbox must be minLon,minLat,maxLon,maxLat.",
                             422, request)
            if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
                return error("INVALID_REQUEST", "bbox must be minLon,minLat,maxLon,maxLat.",
                             422, request)
        return public_map_real.public_map()
    if path in UNAVAILABLE_PATHS:
        dependency = "road and closure" if path.startswith(("/routes", "/closures")) else "shelter"
        return error("UNAVAILABLE", f"Validated {dependency} data is not loaded.", 503, request)
    if path in AGENT_PATHS:
        return handle_agents(request, path, identity, error)
    if path in BRIEF_PATHS:
        return await handle_briefs(request, path, identity, error)
    if path in AREA_PATHS:
        return handle_areas(request, path, identity, error)
    if path in ADMIN_PATHS:
        return await handle_admin(request, path, identity, error)
    if path in LIVE_PATHS:
        return handle_live(request, path, identity, error)
    if path not in RADAR_PATHS:
        return None
    p, q = request.path_params, request.query_params

    if path == "/values/{value_id}/trace":
        found = radar_real.trace(engine(), p["value_id"], identity)
        return found if found is not None else error("NOT_FOUND", "Value not found.", 404, request)

    if path == "/layers":
        return {"synthetic": False, "items": radar_real.list_layers(identity), "next_cursor": None}

    if path == "/layers/{layer_id}":
        layer = radar_real.get_layer(p["layer_id"], identity)
        return layer if layer is not None else error("NOT_FOUND", "Layer not found.", 404, request)

    if path == "/layers/{layer_id}/tiles/{z}/{x}/{y}":
        try:
            z, x, y = int(p["z"]), int(p["x"]), int(p["y"].removesuffix(".png"))
        except ValueError:
            return error("INVALID_REQUEST", "Tile coordinates must be integers.", 422, request)
        from backend.app.services import tiles

        if not tiles.valid_tile(z, x, y):
            return error("INVALID_REQUEST", "Tile coordinates out of range.", 422, request)
        found = radar_real.layer_file(p["layer_id"], identity)
        if found is None:
            return error("NOT_FOUND", "Layer not found.", 404, request)
        png = tiles.render(found[0], z, x, y, found[1])
        if png is None:
            return error("NOT_FOUND", "Tile outside the layer.", 404, request)
        return Response(png, media_type="image/png", headers={"Cache-Control": "private, no-store"})

    if path == "/layers/{layer_id}/files/{file_id}":
        from fastapi.responses import FileResponse

        found = radar_real.downloadable_file(p["layer_id"], p["file_id"], identity)
        if found is None:
            return error("NOT_FOUND", "File not found.", 404, request)
        # Starlette FileResponse implements single-range requests and returns 206/416.
        return FileResponse(
            found,
            media_type="application/octet-stream",
            filename=p["file_id"],
            headers={"Cache-Control": "private, no-store"},
        )

    if path == "/layers/{layer_id}/timeseries":
        area = q.get("area_id")
        if not area:
            return error("INVALID_REQUEST", "area_id is required.", 422, request)
        for name in ("from", "to"):
            if q.get(name) and not DATE.match(q[name]):
                return error("INVALID_REQUEST", f"'{name}' must be YYYY-MM-DD.", 422, request)
        series = radar_real.series(
            engine(), p["layer_id"], area, q.get("from"), q.get("to"), identity
        )
        return (
            series if series is not None else error("NOT_FOUND", "Layer not found.", 404, request)
        )

    # /areas/{area_id}/damage
    pass_id = q.get("pass_id")
    if pass_id not in (None, "A") and not DATE.match(pass_id):
        return error("INVALID_REQUEST", "pass_id must be 'A' or YYYY-MM-DD.", 422, request)
    return radar_real.damage(engine(), p["area_id"], pass_id, identity)


def handle_live(
    request: Request,
    path: str,
    identity: Identity | None,
    error: Callable[[str, str, int, Request], Response],
) -> Any:
    import datetime as dt

    from backend.app.services import live_real

    if path == "/status":
        return live_real.status(engine())
    if path == "/alerts/{alert_id}":
        alert = live_real.get_alert(engine(), identity, request.path_params["alert_id"])
        return alert if alert is not None else error("NOT_FOUND", "Alert not found.", 404, request)
    q = request.query_params
    since = None
    if q.get("since"):
        try:
            since = dt.datetime.fromisoformat(q["since"])
        except ValueError:
            return error("INVALID_REQUEST", "'since' must be an ISO date or time.", 422, request)
        if since.tzinfo is None:
            since = since.replace(tzinfo=dt.UTC)
    try:
        limit = int(q.get("limit", "50"))
        offset = int(q.get("cursor", "0"))
    except ValueError:
        return error("INVALID_REQUEST", "limit and cursor must be integers.", 422, request)
    if not 1 <= limit <= 100 or offset < 0:
        return error(
            "INVALID_REQUEST", "limit must be 1-100 and cursor not negative.", 422, request
        )
    kind = q.get("type")
    if kind not in (None, "fire_detected", "possible_power_loss"):
        return error("INVALID_REQUEST", "Unknown alert type.", 422, request)
    return live_real.list_alerts(
        engine(),
        identity,
        area_id=q.get("area_id"),
        kind=kind,
        since=since,
        limit=limit,
        offset=offset,
    )


async def handle_briefs(
    request: Request,
    path: str,
    identity: Identity | None,
    error: Callable[[str, str, int, Request], Response],
) -> Any:
    import datetime as dt
    import json

    from backend.app.services import briefs_real, summary_real
    from fastapi.responses import HTMLResponse

    p = request.path_params
    try:
        if path == "/areas/{area_id}/summary":
            as_of = _iso(request.query_params.get("as_of"))
            if as_of is False:
                return error("INVALID_REQUEST", "'as_of' must be an ISO date or time.", 422, request)
            found = summary_real.area_summary(engine(), p["area_id"], identity, as_of=as_of)
            return (
                found if found is not None else error("NOT_FOUND", "Area not found.", 404, request)
            )
        if path == "/briefs":
            try:
                body = await request.json()
            except (ValueError, json.JSONDecodeError):
                body = None
            if (
                not isinstance(body, dict)
                or set(body) != {"area_id", "as_of"}
                or not all(isinstance(v, str) for v in body.values())
            ):
                return error("INVALID_REQUEST", "Body must be {area_id, as_of}.", 422, request)
            try:
                as_of = dt.datetime.fromisoformat(body["as_of"])
            except ValueError:
                return error(
                    "INVALID_REQUEST", "'as_of' must be an ISO date or time.", 422, request
                )
            if as_of.tzinfo is None:
                as_of = as_of.replace(tzinfo=dt.UTC)
            if as_of > dt.datetime.now(dt.UTC):
                return error("INVALID_REQUEST", "'as_of' cannot be in the future.", 422, request)
            from backend.app.services import admin_real

            try:
                brief = briefs_real.create(engine(), identity, body["area_id"], as_of)
            except PermissionError:
                return error("FORBIDDEN", "Your role cannot access this resource.", 403, request)
            admin_real.audit(
                engine(),
                identity.user_id,
                "brief_create",
                "brief",
                "success" if brief else "not_found",
                request.state.request_id,
            )
            return (
                brief if brief is not None else error("NOT_FOUND", "Area not found.", 404, request)
            )
    except summary_real.Unavailable:
        return error(
            "UNAVAILABLE",
            "Required evidence is unavailable for the requested time.",
            503,
            request,
        )
    brief = briefs_real.read(engine(), identity, p["report_id"])
    if brief is None:
        return error("NOT_FOUND", "Brief not found or expired.", 404, request)
    if path == "/briefs/{report_id}/print":
        return HTMLResponse(
            briefs_real.to_html(brief),
            headers={
                "Cache-Control": "private, no-store",
                "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
            },
        )
    return brief


def _page(q: Any, default: int, maximum: int) -> tuple[int, int] | None:
    try:
        limit, offset = int(q.get("limit", str(default))), int(q.get("cursor", "0"))
    except ValueError:
        return None
    return (limit, offset) if 1 <= limit <= maximum and offset >= 0 else None


def _iso(value: str | None) -> Any:
    """None when absent; False when not an ISO date/time; otherwise an aware datetime."""
    import datetime as dt

    if not value:
        return None
    try:
        t = dt.datetime.fromisoformat(value)
    except ValueError:
        return False
    return t if t.tzinfo else t.replace(tzinfo=dt.UTC)


def handle_areas(
    request: Request,
    path: str,
    identity: Identity | None,
    error: Callable[[str, str, int, Request], Response],
) -> Any:
    import json

    from backend.app.services import areas_real, summary_real

    p, q = request.path_params, request.query_params
    if path in ("/sources", "/sources/{source_id}"):
        f = radar_real.data_root() / "local" / "radar_contract" / "sources.json"
        if not f.exists():
            return error("UNAVAILABLE", "No approved source catalogue is loaded.", 503, request)
        records = json.loads(f.read_text(encoding="utf-8"))
        if path == "/sources/{source_id}":
            found = next((r for r in records if r["source_id"] == p["source_id"]), None)
            return (
                found
                if found is not None
                else error("NOT_FOUND", "Source not found.", 404, request)
            )
        page = _page(q, 50, 100)
        if page is None:
            return error("INVALID_REQUEST", "Bad cursor.", 422, request)
        limit, offset = page
        return {
            "synthetic": False,
            "items": records[offset : offset + limit],
            "next_cursor": str(offset + limit) if offset + limit < len(records) else None,
        }
    if path == "/areas/{area_id}/facilities":
        return error("UNAVAILABLE", "Facility data is not loaded yet.", 503, request)
    if path == "/areas":
        page = _page(q, 100, 500)
        if page is None:
            return error(
                "INVALID_REQUEST", "limit must be 1-500 and cursor not negative.", 422, request
            )
        bbox = None
        if q.get("bbox"):
            try:
                w, s, e, n = (float(x) for x in q["bbox"].split(","))
            except ValueError:
                return error(
                    "INVALID_REQUEST", "bbox must be minLon,minLat,maxLon,maxLat.", 422, request
                )
            if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
                return error(
                    "INVALID_REQUEST", "bbox must be minLon,minLat,maxLon,maxLat.", 422, request
                )
            bbox = (w, s, e, n)
        return areas_real.list_areas(engine(), identity, bbox, *page)
    area = p["area_id"]
    if path == "/areas/{area_id}/values":
        page = _page(q, 100, 100)
        as_of = _iso(q.get("as_of"))
        if page is None or as_of is False:
            return error("INVALID_REQUEST", "Bad cursor or as_of.", 422, request)
        found = areas_real.values(engine(), area, q.get("metric"), as_of, *page)
    elif path == "/areas/{area_id}/people":
        as_of = _iso(q.get("as_of"))
        if as_of is False:
            return error("INVALID_REQUEST", "'as_of' must be an ISO date or time.", 422, request)
        try:
            found = areas_real.people(engine(), area, identity, as_of)
        except summary_real.Unavailable:
            return error(
                "UNAVAILABLE",
                "Required evidence is unavailable for the requested time.",
                503,
                request,
            )
    elif path == "/areas/{area_id}/services":
        as_of = _iso(q.get("as_of"))
        if as_of is False:
            return error("INVALID_REQUEST", "'as_of' must be an ISO date or time.", 422, request)
        found = areas_real.services(engine(), area, as_of)
    else:
        found = areas_real.validation(engine(), area)
    return found if found is not None else error("NOT_FOUND", "Area not found.", 404, request)


async def _body(request: Request, keys: set[str]) -> dict | None:
    import json

    try:
        body = await request.json()
    except (ValueError, json.JSONDecodeError):
        return None
    return body if isinstance(body, dict) and set(body) == keys else None


async def handle_admin(
    request: Request,
    path: str,
    identity: Identity | None,
    error: Callable[[str, str, int, Request], Response],
) -> Any:
    from backend.app.core.permissions import ROLE_LEVEL
    from backend.app.services import admin_real

    p, rid = request.path_params, request.state.request_id
    if path == "/admin/audit":
        page = _page(request.query_params, 100, 100)
        start, end = _iso(request.query_params.get("from")), _iso(request.query_params.get("to"))
        if page is None or start is False or end is False:
            return error("INVALID_REQUEST", "Bad cursor, from or to.", 422, request)
        return admin_real.list_audit(engine(), start, end, *page)

    if path == "/alerts/{alert_id}/reviews":
        body = await _body(request, {"status", "note"})
        if (
            body is None
            or body["status"] not in admin_real.REVIEW_STATUSES
            or not isinstance(body["note"], str)
            or len(body["note"]) > 1000
        ):
            return error(
                "INVALID_REQUEST",
                "Body must be {status, note}; status one of "
                + ", ".join(admin_real.REVIEW_STATUSES)
                + "; note up to 1000 characters.",
                422,
                request,
            )
        try:
            review = admin_real.review_alert(
                engine(), identity, p["alert_id"], body["status"], body["note"], rid
            )
        except admin_real.StoreError:
            return error("UNAVAILABLE", "Review could not be recorded safely.", 503, request)
        if review is None:
            admin_real.audit(engine(), identity.user_id, "alert_review", "alert", "not_found", rid)
        return (
            review if review is not None else error("NOT_FOUND", "Alert not found.", 404, request)
        )

    if path == "/admin/users/{user_id}/roles":
        body = await _body(request, {"role", "area_scopes", "reason"})
        if (
            body is None
            or body["role"] not in ROLE_LEVEL
            or not isinstance(body["area_scopes"], list)
            or not all(isinstance(x, str) and x for x in body["area_scopes"])
            or not isinstance(body["reason"], str)
            or not body["reason"].strip()
            or len(body["reason"]) > 500
        ):
            return error(
                "INVALID_REQUEST", "Body must be {role, area_scopes, reason}.", 422, request
            )
        try:
            out = admin_real.set_access(
                engine(),
                identity,
                p["user_id"],
                body["role"],
                body["area_scopes"],
                body["reason"].strip(),
                rid,
            )
        except admin_real.Conflict as exc:
            return error("CONFLICT", str(exc), 409, request)
        except admin_real.StoreError:
            return error("UNAVAILABLE", "Role change could not be audited safely.", 503, request)
        if out is None:
            admin_real.audit(engine(), identity.user_id, "role_change", "user", "not_found", rid)
        return out if out is not None else error("NOT_FOUND", "User not found.", 404, request)

    # /admin/jobs/{job_id}/retry
    body = await _body(request, {"idempotency_key"})
    key = body["idempotency_key"] if body else None
    if not isinstance(key, str) or not 1 <= len(key) <= 100:
        return error(
            "INVALID_REQUEST", "Body must be {idempotency_key} (1-100 characters).", 422, request
        )
    if p["job_id"] not in admin_real.JOB_IDS:
        return error("NOT_FOUND", "Job not found.", 404, request)
    try:
        job = admin_real.retry_job(engine(), identity, p["job_id"], key, request_id=rid)
    except admin_real.Conflict as exc:
        return error("CONFLICT", str(exc), 409, request)
    except admin_real.StoreError:
        return error("UNAVAILABLE", "Job retry could not be recorded safely.", 503, request)
    return job


def handle_agents(request: Request, path: str, identity: Identity | None,
                  error: Callable[[str, str, int, Request], Response]) -> Any:
    """U-06: incidents, incident detail, area budget and buildings from PostGIS (agents_real)."""
    from backend.app.services import agents_real

    p, q = request.path_params, request.query_params
    try:
        if path == "/incidents":
            page = _page(q, 50, 100)
            if page is None:
                return error("INVALID_REQUEST", "limit must be 1-100 and cursor not negative.", 422, request)
            return agents_real.list_incidents(engine(), identity, q.get("area_id"), *page)
        if path == "/incidents/{incident_id}":
            found = agents_real.get_incident(engine(), identity, p["incident_id"])
            return found if found is not None else error("NOT_FOUND", "Incident not found.", 404, request)
        if path == "/areas/{area_id}/budget":
            found = agents_real.area_budget(engine(), p["area_id"])
            return found if found is not None else error("NOT_FOUND", "No budget for this area.", 404, request)
        # /buildings
        raw = q.get("bbox")
        try:
            w, s, e, n = (float(v) for v in (raw or "").split(","))
        except ValueError:
            return error("INVALID_REQUEST", "bbox must be minLon,minLat,maxLon,maxLat.", 422, request)
        if not (-180 <= w < e <= 180 and -90 <= s < n <= 90):
            return error("INVALID_REQUEST", "bbox must be minLon,minLat,maxLon,maxLat.", 422, request)
        if (e - w) * (n - s) > agents_real.MAX_BBOX_DEG2:
            return error("INVALID_REQUEST", "bbox is too large; zoom in.", 422, request)
        try:
            limit = int(q.get("limit", "2000"))
        except ValueError:
            limit = 0
        if not 1 <= limit <= agents_real.MAX_BUILDINGS:
            return error("INVALID_REQUEST", f"limit must be 1-{agents_real.MAX_BUILDINGS}.", 422, request)
        return agents_real.buildings(engine(), identity, (w, s, e, n), limit)
    except agents_real.NotLoaded:
        return error("UNAVAILABLE", "Agent outputs are not loaded yet.", 503, request)
