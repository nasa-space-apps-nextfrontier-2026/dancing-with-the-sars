"""Real-data alerts and source status (DEMO_SYNTHETIC=false).

Alerts come from the worker (worker/jobs.py). Visibility: the 72-hour/release rule (admins see
everything for review) and the user's area scopes. /status is public, so it never shows error
text, file paths or hostnames: a failed fetch is reported only as "fetch failed".
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from backend.app.core.security import Identity
from backend.app.policy.release import is_released, now_utc
from backend.app.policy.scope import area_in_scope

FRESH = dt.timedelta(minutes=45)   # docs/05: FIRMS/IODA polling thresholds
AGING = dt.timedelta(hours=2)
RADAR_FRESH = dt.timedelta(days=12)  # one NISAR repeat cycle
RADAR_AGING = dt.timedelta(days=24)


def iso(t: dt.datetime | None) -> str | None:
    return t.astimezone(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if t else None


def freshness(last: dt.datetime | None, fresh: dt.timedelta, aging: dt.timedelta,
              now: dt.datetime | None = None) -> str:
    if last is None:
        return "Stale"
    age = (now or now_utc()) - last
    return "Fresh" if age <= fresh else "Aging" if age <= aging else "Stale"


def _visible(row: Any, identity: Identity | None) -> bool:
    if identity is None:
        return False
    if identity.role == "admin":
        return True
    return is_released(row.release_at) and area_in_scope(row.area_id, identity.area_scopes)


def _status_rows(conn: Any) -> dict[str, Any]:
    from sqlalchemy import text

    return {r.id: r for r in conn.execute(text("SELECT * FROM source_status")).all()}


def to_detail(row: Any, status: Any | None) -> dict[str, Any]:
    last = status.last_success_at if status else None
    return {
        "synthetic": False, "alert_id": row.alert_id, "area_id": row.area_id, "type": row.type,
        "title": row.title, "detected_at": iso(row.detected_at), "processed_at": iso(row.processed_at),
        "satellite": row.satellite, "product": row.product, "label": row.label,
        "source": list(row.source), "lineage_ids": list(row.lineage_ids),
        "independent_source_count": row.independent_source_count,
        "freshness": freshness(last, FRESH, AGING),
        "cached": bool(status and status.failure), "release_at": iso(row.release_at),
        "safety_tag": row.safety_tag, "rings": [], "facilities": [], "services": [],
        "route_options_url": "/api/v1/routes", "review_status": row.review_status,
        "cause": "Unknown", "warning": row.detail.get("warning", "CIVISAR does not determine a cause."),
    }


def list_alerts(engine: Any, identity: Identity | None, *, area_id: str | None, kind: str | None,
                since: dt.datetime | None, limit: int, offset: int) -> dict[str, Any]:
    from sqlalchemy import text

    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT * FROM alerts WHERE (CAST(:kind AS text) IS NULL OR type = :kind) "
            "AND (CAST(:since AS timestamptz) IS NULL OR detected_at >= :since) "
            "ORDER BY detected_at DESC, alert_id"), {"kind": kind, "since": since}).all()
        status = _status_rows(conn)
    if area_id:
        rows = [r for r in rows if r.area_id == area_id or area_in_scope(r.area_id, (area_id,))]
    rows = [r for r in rows if _visible(r, identity)]
    page = rows[offset:offset + limit]
    nxt = str(offset + limit) if offset + limit < len(rows) else None
    items = [to_detail(r, status.get(r.source[0] if r.source else "")) for r in page]
    return {"synthetic": False, "items": items, "next_cursor": nxt}


def get_alert(engine: Any, identity: Identity | None, alert_id: str) -> dict[str, Any] | None:
    from sqlalchemy import text

    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM alerts WHERE alert_id = :a"), {"a": alert_id}).first()
        status = _status_rows(conn)
    if row is None or not _visible(row, identity):
        return None
    return to_detail(row, status.get(row.source[0] if row.source else ""))


def status(engine: Any) -> dict[str, Any]:
    from sqlalchemy import text

    out = []
    with engine.connect() as conn:
        for r in _status_rows(conn).values():
            out.append({"id": r.id, "acquired_at": iso(r.acquired_at), "processed_at": iso(r.processed_at),
                        "last_success_at": iso(r.last_success_at),
                        "freshness": freshness(r.last_success_at, FRESH, AGING),
                        "cached": bool(r.failure), "failure": "fetch failed" if r.failure else ""})
        radar = conn.execute(text("SELECT max(after_acquired_at) AS acq FROM radar_artifacts")).first()
    if radar and radar.acq:
        out.append({"id": "nisar-gcov-151d72", "acquired_at": iso(radar.acq), "processed_at": None,
                    "last_success_at": iso(radar.acq),
                    "freshness": freshness(radar.acq, RADAR_FRESH, RADAR_AGING), "cached": True,
                    "failure": ""})
    return {"synthetic": False, "sources": sorted(out, key=lambda s: s["id"])}
