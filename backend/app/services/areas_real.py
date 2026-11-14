"""Area routes beyond the summary (DEMO_SYNTHETIC=false): area list, values, people, services,
validation. The router has already checked role and, for /areas/{area_id}/..., the area scope.

Only H3 r8 neighbourhoods are listed (the published resolution). Held records are hidden for
every role. There is no independent damage assessment for this area yet, so validation is
reported as unavailable rather than as an empty "all clear".
"""

from __future__ import annotations

from typing import Any

import h3
from backend.app.core.security import Identity
from backend.app.policy.release import is_released
from backend.app.policy.scope import area_in_scope
from backend.app.services import summary_real

VALIDATION_NOTE = ("unavailable: no independent damage assessment covers this area yet; "
                   "radar results are candidates, not confirmed damage")


def _exists(conn: Any, area_id: str) -> bool:
    from sqlalchemy import text

    return conn.execute(text("SELECT 1 FROM areas WHERE area_id = :a"), {"a": area_id}).first() is not None


def list_areas(engine: Any, identity: Identity, bbox: tuple[float, float, float, float] | None,
               limit: int, offset: int) -> dict[str, Any]:
    from sqlalchemy import text

    with engine.connect() as conn:
        ids = [r[0] for r in conn.execute(text(
            "SELECT area_id FROM areas WHERE resolution = 8 ORDER BY area_id")).all()]
    ids = [a for a in ids if area_in_scope(a, identity.area_scopes)]
    if bbox:
        w, s, e, n = bbox
        ids = [a for a in ids if s <= h3.cell_to_latlng(a)[0] <= n and w <= h3.cell_to_latlng(a)[1] <= e]
    page = ids[offset:offset + limit]
    return {"synthetic": False, "items": [{"area_id": a, "h3_id": a, "cadaster_code": None} for a in page],
            "next_cursor": str(offset + limit) if offset + limit < len(ids) else None}


def values(engine: Any, area_id: str, metric: str | None, as_of: str | None, limit: int,
           offset: int) -> dict[str, Any] | None:
    from sqlalchemy import text

    with engine.connect() as conn:
        if not _exists(conn, area_id):
            return None
        rows = conn.execute(text(
            "SELECT record FROM metric_values WHERE area_id = :a ORDER BY observed_at, value_id"),
            {"a": area_id}).all()
    recs = [r[0] for r in rows if is_released(r[0]["release_at"])]
    if metric:
        recs = [r for r in recs if r["metric"] == metric]
    if as_of:
        recs = [r for r in recs if r["date"] <= as_of[:10]]
    page = recs[offset:offset + limit]
    return {"synthetic": False, "items": page,
            "next_cursor": str(offset + limit) if offset + limit < len(recs) else None}


def people(engine: Any, area_id: str, identity: Identity) -> dict[str, Any] | None:
    summary = summary_real.area_summary(engine, area_id, identity)  # raises Unavailable without K-04
    if summary is None:
        return None
    return {"synthetic": False, "items": list(summary["people"].values()), "next_cursor": None}


def services(engine: Any, area_id: str) -> dict[str, Any] | None:
    from sqlalchemy import text

    with engine.connect() as conn:
        if not _exists(conn, area_id):
            return None
        alerts = conn.execute(text(
            "SELECT alert_id, type, label, release_at, source, detected_at FROM alerts "
            "WHERE area_id = :a ORDER BY detected_at DESC"), {"a": area_id}).all()
    shown = [a for a in alerts if is_released(a.release_at)]
    return {"synthetic": False, "items": summary_real.services_from(shown), "next_cursor": None}


def validation(engine: Any, area_id: str) -> dict[str, Any] | None:
    with engine.connect() as conn:
        if not _exists(conn, area_id):
            return None
    return {"synthetic": False, "items": [], "availability": VALIDATION_NOTE, "next_cursor": None}
