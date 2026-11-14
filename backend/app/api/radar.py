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
               "/layers/{layer_id}/timeseries", "/areas/{area_id}/damage"}


@lru_cache(maxsize=1)
def engine() -> Any:
    from backend.app.db.base import make_engine

    return make_engine()


def handle(request: Request, path: str, identity: Identity | None,
           error: Callable[[str, str, int, Request], Response]) -> Any:
    if path not in RADAR_PATHS:
        return None
    p, q = request.path_params, request.query_params

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
