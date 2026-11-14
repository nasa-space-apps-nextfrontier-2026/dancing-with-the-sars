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
RADAR_PATHS = {"/layers", "/layers/{layer_id}", "/layers/{layer_id}/tiles/{z}/{x}/{y}",
               "/layers/{layer_id}/timeseries", "/areas/{area_id}/damage",
               "/values/{value_id}/trace"}
LIVE_PATHS = {"/alerts", "/alerts/{alert_id}", "/status"}
BRIEF_PATHS = {"/areas/{area_id}/summary", "/briefs", "/briefs/{report_id}", "/briefs/{report_id}/print"}


@lru_cache(maxsize=1)
def engine() -> Any:
    from backend.app.db.base import make_engine

    return make_engine()


async def handle(request: Request, path: str, identity: Identity | None,
                 error: Callable[[str, str, int, Request], Response]) -> Any:
    if path in BRIEF_PATHS:
        return await handle_briefs(request, path, identity, error)
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

    if path == "/layers/{layer_id}/timeseries":
        area = q.get("area_id")
        if not area:
            return error("INVALID_REQUEST", "area_id is required.", 422, request)
        for name in ("from", "to"):
            if q.get(name) and not DATE.match(q[name]):
                return error("INVALID_REQUEST", f"'{name}' must be YYYY-MM-DD.", 422, request)
        series = radar_real.series(engine(), p["layer_id"], area, q.get("from"), q.get("to"), identity)
        return series if series is not None else error("NOT_FOUND", "Layer not found.", 404, request)

    # /areas/{area_id}/damage
    pass_id = q.get("pass_id")
    if pass_id not in (None, "A") and not DATE.match(pass_id):
        return error("INVALID_REQUEST", "pass_id must be 'A' or YYYY-MM-DD.", 422, request)
    return radar_real.damage(engine(), p["area_id"], pass_id, identity)


def handle_live(request: Request, path: str, identity: Identity | None,
                error: Callable[[str, str, int, Request], Response]) -> Any:
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
        return error("INVALID_REQUEST", "limit must be 1-100 and cursor not negative.", 422, request)
    kind = q.get("type")
    if kind not in (None, "fire_detected", "possible_power_loss"):
        return error("INVALID_REQUEST", "Unknown alert type.", 422, request)
    return live_real.list_alerts(engine(), identity, area_id=q.get("area_id"), kind=kind,
                                 since=since, limit=limit, offset=offset)


async def handle_briefs(request: Request, path: str, identity: Identity | None,
                        error: Callable[[str, str, int, Request], Response]) -> Any:
    import datetime as dt
    import json

    from backend.app.services import briefs_real, summary_real
    from fastapi.responses import HTMLResponse

    p = request.path_params
    try:
        if path == "/areas/{area_id}/summary":
            found = summary_real.area_summary(engine(), p["area_id"], identity)
            return found if found is not None else error("NOT_FOUND", "Area not found.", 404, request)
        if path == "/briefs":
            try:
                body = await request.json()
            except (ValueError, json.JSONDecodeError):
                body = None
            if (not isinstance(body, dict) or set(body) != {"area_id", "as_of"}
                    or not all(isinstance(v, str) for v in body.values())):
                return error("INVALID_REQUEST", "Body must be {area_id, as_of}.", 422, request)
            try:
                dt.datetime.fromisoformat(body["as_of"])
            except ValueError:
                return error("INVALID_REQUEST", "'as_of' must be an ISO date or time.", 422, request)
            try:
                brief = briefs_real.create(engine(), identity, body["area_id"])
            except PermissionError:
                return error("FORBIDDEN", "Your role cannot access this resource.", 403, request)
            return brief if brief is not None else error("NOT_FOUND", "Area not found.", 404, request)
    except summary_real.Unavailable:
        return error("UNAVAILABLE", "Population data is not loaded; people ranges are unavailable.", 503, request)
    brief = briefs_real.read(engine(), identity, p["report_id"])
    if brief is None:
        return error("NOT_FOUND", "Brief not found or expired.", 404, request)
    if path == "/briefs/{report_id}/print":
        return HTMLResponse(briefs_real.to_html(brief), headers={
            "Cache-Control": "private, no-store",
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'"})
    return brief
