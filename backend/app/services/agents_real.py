"""U-06 real-data endpoints for the agents' output (PostGIS; loaded by scripts/load_agent_outputs.py).

Rules on every call: signed in (router), area scope, 72-hour hold (release_at), role-specific
recommendations (admin reads the coordinator version; admin is not a bypass for hold or scope).
Whole-demo-box insights are shown only to users whose scope covers the whole demo box. Buildings
never carry residents (doc 07) and their damage fields are the H3 r9 cell result.
"""

from __future__ import annotations

from typing import Any

from backend.app.core.security import Identity
from backend.app.policy.release import is_released
from backend.app.policy.scope import AOI_ID, area_in_scope

FIDELITY = "Reconstruction from satellite data, not footage"
REC_ROLE = {"analyst": "analyst", "officer": "officer", "coordinator": "coordinator", "admin": "coordinator"}
MAX_BBOX_DEG2 = 0.05          # about 5 km x 10 km at this latitude
MAX_BUILDINGS = 5000


class NotLoaded(Exception):
    """The agent outputs have not been loaded into PostGIS yet."""


def _run(conn: Any) -> Any:
    from sqlalchemy import text

    row = conn.execute(text("SELECT generated_at, counts FROM agent_runs ORDER BY loaded_at DESC LIMIT 1")).first()
    if row is None:
        raise NotLoaded
    return row


def _visible(identity: Identity, area_id: str, release_at: Any) -> bool:
    return is_released(release_at) and area_in_scope(area_id, identity.area_scopes)


def list_incidents(engine: Any, identity: Identity, area_id: str | None, limit: int, offset: int) -> dict:
    from sqlalchemy import text

    with engine.connect() as conn:
        run = _run(conn)
        rows = conn.execute(text("SELECT area_id, release_at, record FROM agent_incidents ORDER BY rank")).all()
    shown = [r for r in rows if _visible(identity, r.area_id, r.release_at)
             and (area_id is None or r.area_id == area_id or area_in_scope(r.area_id, (area_id,)))]
    items = []
    for n, r in enumerate(shown[offset:offset + limit], start=offset + 1):
        items.append(r.record | {"rank": n})  # rank within what this user may see
    weights = {k: v["weight"] for k, v in shown[0].record["parts"].items()} if shown else {}
    return {"synthetic": False, "generated_at": run.generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "weights": weights, "data_age": {}, "items": items,
            "next_cursor": str(offset + limit) if offset + limit < len(shown) else None}


def get_incident(engine: Any, identity: Identity, incident_id: str) -> dict | None:
    from sqlalchemy import text

    with engine.connect() as conn:
        _run(conn)
        row = conn.execute(text("SELECT area_id, release_at, record FROM agent_incidents WHERE incident_id = :i"),
                           {"i": incident_id}).first()
        if row is None or not _visible(identity, row.area_id, row.release_at):
            return None
        rec = conn.execute(text("SELECT record FROM agent_recommendations WHERE incident_id = :i AND role = :r"),
                           {"i": incident_id, "r": REC_ROLE.get(identity.role, "analyst")}).scalar()
        insights = [r[0] for r in conn.execute(text("SELECT record FROM agent_insights ORDER BY id")).all()] \
            if AOI_ID in identity.area_scopes else []
    if rec is None:
        return None
    return {"synthetic": False, "incident": row.record, "insights": insights, "recommendation": rec}


def area_budget(engine: Any, area_id: str) -> dict | None:
    """The router has already checked role and area scope for area_id."""
    from sqlalchemy import text

    with engine.connect() as conn:
        _run(conn)
        row = conn.execute(text("SELECT release_at, record FROM agent_budgets WHERE area_id = :a"),
                           {"a": area_id}).first()
    if row is None or not is_released(row.release_at):
        return None
    return row.record


def buildings(engine: Any, identity: Identity, bbox: tuple[float, float, float, float], limit: int) -> dict:
    from sqlalchemy import text

    w, s, e, n = bbox
    with engine.connect() as conn:
        _run(conn)
        rows = conn.execute(text(
            "SELECT h3_r8, release_at, ST_AsGeoJSON(geom, 6) AS g, properties FROM agent_buildings "
            "WHERE geom && ST_MakeEnvelope(:w, :s, :e, :n, 4326) "
            "AND ST_Intersects(geom, ST_MakeEnvelope(:w, :s, :e, :n, 4326)) ORDER BY building_id LIMIT :l"),
            {"w": w, "s": s, "e": e, "n": n, "l": MAX_BUILDINGS * 4}).all()
    import json

    shown = [r for r in rows if _visible(identity, r.h3_r8, r.release_at)]
    features = [{"type": "Feature", "geometry": json.loads(r.g) if r.g else None, "properties": r.properties}
                for r in shown[:limit]]
    return {"synthetic": False, "type": "FeatureCollection", "fidelity": FIDELITY,
            "truncated": len(shown) > limit or len(rows) >= MAX_BUILDINGS * 4, "features": features}
