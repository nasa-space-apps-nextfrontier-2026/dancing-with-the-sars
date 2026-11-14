"""Worker jobs (M3-04): call Thanoban's M1-04 functions and store alerts and source status.

Each job is idempotent (same event -> same alert id) and never deletes the last good data when a
source fails: the failure is recorded in source_status and the API shows the old alerts as Cached.
Alerts keep only the H3 r8 neighbourhood of a detection, never its exact coordinates.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from collections.abc import Callable
from typing import Any

import h3

FIRE_SOURCE = "firms-viirs-nrt"
LIGHTS_SOURCE = "blackmarble-nrt"
FIRE_PRODUCT = "VIIRS 375 m active fire NRT (VJ114IMGTDL_NRT, VJ214IMGTDL_NRT)"
FIRE_WARNING = "Satellite heat signal. CIVISAR does not determine a cause."
POWER_WARNING = "Possible power loss from night lights. Not proof of a cause; not a blackout claim."


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def fire_release_delay() -> dt.timedelta:
    """Hours between detection and release to signed-in roles (team decision; default 0)."""
    return dt.timedelta(hours=float(os.environ.get("FIRE_RELEASE_DELAY_HOURS", "0")))


def alert_id(kind: str, area: str, start: str) -> str:
    return hashlib.sha256(f"{kind}|{area}|{start}".encode()).hexdigest()[:32]


def fire_alert(event: Any, processed_at: dt.datetime, snapshot_id: str) -> dict[str, Any]:
    """Alert row from a FireEvent (worker.services.fires). Neighbourhood level only."""
    area = h3.latlng_to_cell(event.lat, event.lon, 8)
    detected = dt.datetime.fromisoformat(event.start)
    return {
        "alert_id": alert_id("fire_detected", area, event.start), "area_id": area,
        "type": "fire_detected", "title": "Fire detected", "detected_at": detected,
        "processed_at": processed_at, "satellite": ", ".join(event.satellites),
        "product": FIRE_PRODUCT, "label": "Observed", "confidence": event.confidence,
        "source": [FIRE_SOURCE], "lineage_ids": [snapshot_id], "independent_source_count": 1,
        "release_at": dt.datetime.fromisoformat(event.end) + fire_release_delay(),
        "safety_tag": "restricted_alert",
        "detail": {"points": event.points, "end": event.end, "warning": FIRE_WARNING},
    }


def power_alert(event: dict[str, Any], processed_at: dt.datetime, snapshot_id: str) -> dict[str, Any] | None:
    """Alert row from a power_loss_events() item; cells are H3 ids (r8 parent is published)."""
    cell = event["area"]
    try:
        area = h3.cell_to_parent(cell, 8) if h3.get_resolution(cell) > 8 else cell
    except (ValueError, TypeError):
        return None
    day = dt.datetime.fromisoformat(f"{event['time'][:10]}T00:00:00+00:00")
    return {
        "alert_id": alert_id("possible_power_loss", area, event["time"]), "area_id": area,
        "type": "possible_power_loss", "title": "Possible power loss", "detected_at": day,
        "processed_at": processed_at, "satellite": ", ".join(event.get("satellites") or []) or "NOAA-20/21",
        "product": event["source"], "label": "Corroborated" if event.get("corroborated") else "Observed",
        "confidence": event["confidence"], "source": [LIGHTS_SOURCE], "lineage_ids": [snapshot_id],
        "independent_source_count": 2 if event.get("corroborated") else 1,
        "release_at": day, "safety_tag": "restricted_alert",
        "detail": {"reasons": event.get("reasons", []), "warning": POWER_WARNING},
    }


def store(engine: Any, source_id: str, alerts: list[dict[str, Any]], acquired_at: dt.datetime | None,
          detail: dict[str, Any]) -> None:
    from sqlalchemy import text

    t = now_utc()
    with engine.begin() as conn:
        for a in alerts:
            conn.execute(text(
                "INSERT INTO alerts (alert_id, area_id, type, title, detected_at, processed_at, satellite, "
                "product, label, confidence, source, lineage_ids, independent_source_count, release_at, "
                "safety_tag, detail) VALUES (:alert_id, :area_id, :type, :title, :detected_at, :processed_at, "
                ":satellite, :product, :label, :confidence, CAST(:source AS jsonb), CAST(:lineage_ids AS jsonb), "
                ":independent_source_count, :release_at, :safety_tag, CAST(:detail AS jsonb)) "
                "ON CONFLICT (alert_id) DO UPDATE SET processed_at = EXCLUDED.processed_at, "
                "detail = EXCLUDED.detail"),
                a | {"source": json.dumps(a["source"]), "lineage_ids": json.dumps(a["lineage_ids"]),
                     "detail": json.dumps(a["detail"])})
        conn.execute(text(
            "INSERT INTO source_status (id, acquired_at, processed_at, last_success_at, last_attempt_at, "
            "failure, detail) VALUES (:id, :acq, :t, :t, :t, '', CAST(:d AS jsonb)) ON CONFLICT (id) DO UPDATE "
            "SET acquired_at = EXCLUDED.acquired_at, processed_at = EXCLUDED.processed_at, "
            "last_success_at = EXCLUDED.last_success_at, last_attempt_at = EXCLUDED.last_attempt_at, "
            "failure = '', detail = EXCLUDED.detail"),
            {"id": source_id, "acq": acquired_at, "t": t, "d": json.dumps(detail)})


def record_failure(engine: Any, source_id: str, error: Exception) -> None:
    """Keep the last good alerts; only note the failed attempt (shown as Cached by the API)."""
    from sqlalchemy import text

    message = f"{type(error).__name__}: {str(error)[:200]}"
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO source_status (id, last_attempt_at, failure, detail) VALUES (:id, :t, :f, '{}') "
            "ON CONFLICT (id) DO UPDATE SET last_attempt_at = EXCLUDED.last_attempt_at, failure = EXCLUDED.failure"),
            {"id": source_id, "t": now_utc(), "f": message})


def run_fires(engine: Any, current_events: Callable[[], tuple[list[Any], dict]] | None = None) -> dict:
    if current_events is None:
        from worker.services.firms_feed import current_events
    try:
        events, info = current_events()
    except Exception as exc:  # network or feed failure: keep last good data  # noqa: BLE001
        record_failure(engine, FIRE_SOURCE, exc)
        return {"source": FIRE_SOURCE, "status": "failed", "error": str(exc)[:200]}
    t = now_utc()
    snapshot = f"{FIRE_SOURCE}:{t.strftime('%Y%m%dT%H%M%SZ')}"
    alerts = [fire_alert(e, t, snapshot) for e in events]
    latest = max((dt.datetime.fromisoformat(e.end) for e in events), default=None)
    store(engine, FIRE_SOURCE, alerts, latest, info)
    return {"source": FIRE_SOURCE, "status": "ok", "alerts": len(alerts), **info}


def run_power_loss(engine: Any, history_path: str | None) -> dict:
    """Night-light alerts from Thanoban's per-cell history file (NIGHTLIGHT_HISTORY)."""
    if not history_path or not os.path.exists(history_path):
        return {"source": LIGHTS_SOURCE, "status": "unavailable",
                "note": "set NIGHTLIGHT_HISTORY to the per-cell night-light history file"}
    try:
        from worker.services.evaluate_nightlights import load
        from worker.services.power_loss import power_loss_events

        events = power_loss_events(load(history_path))
    except Exception as exc:  # noqa: BLE001
        record_failure(engine, LIGHTS_SOURCE, exc)
        return {"source": LIGHTS_SOURCE, "status": "failed", "error": str(exc)[:200]}
    t = now_utc()
    snapshot = f"{LIGHTS_SOURCE}:{t.strftime('%Y%m%dT%H%M%SZ')}"
    alerts = [a for a in (power_alert(e, t, snapshot) for e in events) if a]
    latest = max((a["detected_at"] for a in alerts), default=None)
    store(engine, LIGHTS_SOURCE, alerts, latest, {"cells_flagged": len(alerts)})
    return {"source": LIGHTS_SOURCE, "status": "ok", "alerts": len(alerts)}
