"""Real-data facilities for an area (PostGIS; loaded by scripts/load_facilities.py).

Doc 07 rules on every call: signed in and area scope (router, then again per facility here).
Analysts get the need-to-know subset (type, operating status, damage status) with no location;
officer, coordinator and admin get the point. Operating status is always Unknown: no source says
whether a site is open. Damage status is the H3 r9 radar result of the facility's cell, released
and scoped like /areas/{id}/damage; no detected change is never reported as undamaged.
"""

from __future__ import annotations

from typing import Any

import h3
from backend.app.core.security import Identity
from backend.app.policy.scope import AOI_ID, area_in_scope

SOURCE = "OpenStreetMap contributors (ODbL), via K-03"
LOCATION_ROLES = {"officer", "coordinator", "admin"}
NO_CHANGE = "No radar change detected in this cell. Not confirmed undamaged or open."


class NotLoaded(Exception):
    """The facility file has not been loaded into PostGIS yet."""


def loaded(engine: Any) -> bool:
    from sqlalchemy import text

    with engine.connect() as conn:
        return conn.execute(text("SELECT run_id FROM facility_runs LIMIT 1")).first() is not None


def _cell_damage(engine: Any, area_r8: str, identity: Identity) -> dict[str, str]:
    """r9 cell -> damage status text, from the released radar results of one r8 area."""
    from backend.app.services import radar_real

    out = {}
    for item in radar_real.damage(engine, area_r8, None, identity)["items"]:
        level = next((c.split(":", 1)[1] for c in item["reason_codes"] if c.startswith("level:")), None)
        if item["candidate_class"] == "candidate_change":
            out[item["area_id"]] = (f"Radar damage candidate in this cell ({level or 'unclassed'}). "
                                    "Not confirmed; field check needed.")
        elif item["candidate_class"] == "other_change":
            out[item["area_id"]] = "Radar change in this cell, not classed as damage. Not confirmed."
        else:
            out[item["area_id"]] = "Radar could not assess this cell. Unknown."
    return out


def all_in_scope(engine: Any, identity: Identity) -> list[Any]:
    """Every loaded facility in the identity's scope, in one query (used by /map/context)."""
    from sqlalchemy import text

    with engine.connect() as conn:
        if conn.execute(text("SELECT run_id FROM facility_runs LIMIT 1")).first() is None:
            raise NotLoaded
        rows = conn.execute(text(
            "SELECT facility_id, type, h3_r9, h3_r8, osm_timestamp, ST_X(geom) AS lon, ST_Y(geom) AS lat "
            "FROM facilities ORDER BY facility_id")).all()
    return [r for r in rows if area_in_scope(r.h3_r9, identity.area_scopes)]


def damage_status(item: dict[str, Any] | None) -> str:
    """Damage text for one released r9 radar item (None: no detected change in this cell)."""
    if item is None:
        return NO_CHANGE
    level = next((c.split(":", 1)[1] for c in item["reason_codes"] if c.startswith("level:")), None)
    if item["candidate_class"] == "candidate_change":
        return (f"Radar damage candidate in this cell ({level or 'unclassed'}). "
                "Not confirmed; field check needed.")
    if item["candidate_class"] == "other_change":
        return "Radar change in this cell, not classed as damage. Not confirmed."
    return "Radar could not assess this cell. Unknown."


def list_facilities(engine: Any, identity: Identity, area_id: str, kind: str | None,
                    limit: int, offset: int) -> dict | None:
    """None when the area id is not an H3 r8/r9 cell or the demo box (router answers 404)."""
    from sqlalchemy import text

    if area_id == AOI_ID:
        where, params = "", {}
    else:
        try:
            res = h3.get_resolution(area_id) if h3.is_valid_cell(area_id) else None
        except (TypeError, ValueError):
            res = None
        if res not in (8, 9):
            return None
        where, params = f"WHERE h3_r{res} = :a", {"a": area_id}
    if kind:
        where += (" AND " if where else "WHERE ") + "type = :t"
        params["t"] = kind.lower()
    with engine.connect() as conn:
        if conn.execute(text("SELECT run_id FROM facility_runs LIMIT 1")).first() is None:
            raise NotLoaded
        rows = conn.execute(text(
            "SELECT facility_id, type, h3_r9, h3_r8, osm_timestamp, ST_X(geom) AS lon, ST_Y(geom) AS lat "
            f"FROM facilities {where} ORDER BY facility_id"), params).all()
    rows = [r for r in rows if area_in_scope(r.h3_r9, identity.area_scopes)]
    page = rows[offset:offset + limit]
    damage: dict[str, dict[str, str]] = {}
    for r8 in sorted({r.h3_r8 for r in page}):
        damage[r8] = _cell_damage(engine, r8, identity)
    show_point = identity.role in LOCATION_ROLES
    items = [{
        "facility_id": r.facility_id,
        "type": r.type,
        "operating_status": "Unknown",
        "damage_status": damage[r.h3_r8].get(r.h3_r9, NO_CHANGE),
        "label": "Reported",
        "source": [SOURCE],
        "date": r.osm_timestamp.isoformat() if r.osm_timestamp else None,
        "geometry": {"type": "Point", "coordinates": [round(r.lon, 6), round(r.lat, 6)]} if show_point else None,
    } for r in page]
    nxt = str(offset + limit) if offset + limit < len(rows) else None
    return {"synthetic": False, "items": items, "next_cursor": nxt}
