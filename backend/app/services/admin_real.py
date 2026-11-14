"""Audit log, alert reviews, role changes and manual job runs (DEMO_SYNTHETIC=false).

Audit rows keep only actor, action, coarse resource type, outcome, time and request id (doc 05):
never coordinates, tokens, passwords or request bodies. A failed login is recorded as
"anonymous" because people sometimes type a password into the username box.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import uuid
from collections.abc import Callable
from typing import Any

from backend.app.core.config import get_settings
from backend.app.core.permissions import capabilities
from backend.app.core.security import Identity, revoke_user
from backend.app.policy.release import now_utc
from backend.app.services import live_real
from backend.app.services.live_real import iso

log = logging.getLogger("civisar.audit")
AUDIT_DAYS = 30
REVIEW_STATUSES = ("reviewed", "needs_follow_up", "not_relevant")
JOB_STATUS = {"ok": "succeeded", "failed": "failed", "unavailable": "unavailable"}


class StoreError(Exception):
    """The database could not be reached."""


class Conflict(Exception):
    """The request clashes with stored state."""


def audit(engine: Any, actor: str, action: str, resource_type: str, outcome: str,
          request_id: str | None) -> None:
    """Append one audit row. Never blocks the request: a failed write is logged (without detail)."""
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError

    try:
        with engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO audit_events (actor_id, action, resource_type, outcome, at, request_id) "
                "VALUES (:a, :ac, :r, :o, :t, :q)"),
                {"a": actor[:100], "ac": action, "r": resource_type[:40], "o": outcome, "t": now_utc(),
                 "q": request_id})
    except SQLAlchemyError:
        log.warning("audit write failed for action %s", action)


def list_audit(engine: Any, date_from: dt.datetime | None, date_to: dt.datetime | None,
               limit: int, offset: int) -> dict[str, Any]:
    from sqlalchemy import text

    floor = now_utc() - dt.timedelta(days=AUDIT_DAYS)
    start = max(date_from, floor) if date_from else floor
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT actor_id, action, resource_type, outcome, at FROM audit_events WHERE at >= :f "
            "AND (CAST(:t AS timestamptz) IS NULL OR at <= :t) ORDER BY at DESC, id DESC "
            "LIMIT :l OFFSET :o"), {"f": start, "t": date_to, "l": limit + 1, "o": offset}).all()
    items = [{"actor_id": r.actor_id, "action": r.action, "resource_type": r.resource_type,
              "outcome": r.outcome, "at": iso(r.at)} for r in rows[:limit]]
    return {"synthetic": False, "items": items,
            "next_cursor": str(offset + limit) if len(rows) > limit else None}


def apply_access(engine: Any, identity: Identity) -> Identity:
    """Role and scopes set by an admin replace the ones in the env file. Fails closed."""
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError

    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT role, area_scopes FROM user_access WHERE user_id = :u"),
                               {"u": identity.user_id}).first()
    except SQLAlchemyError as exc:
        raise StoreError from exc
    return Identity(identity.user_id, row.role, tuple(row.area_scopes)) if row else identity


def known_user(user_id: str) -> bool:
    try:
        return user_id in json.loads(get_settings().civisar_demo_users_json)
    except (ValueError, TypeError):
        return False


def set_access(engine: Any, admin: Identity, user_id: str, role: str, scopes: list[str],
               reason: str) -> dict[str, Any] | None:
    from sqlalchemy import text

    if not known_user(user_id):
        return None
    if user_id == admin.user_id and role != "admin":
        raise Conflict("Admins cannot remove their own admin role.")
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO user_access (user_id, role, area_scopes, reason, changed_by, changed_at) "
            "VALUES (:u, :r, CAST(:s AS jsonb), :why, :by, :t) ON CONFLICT (user_id) DO UPDATE SET "
            "role = EXCLUDED.role, area_scopes = EXCLUDED.area_scopes, reason = EXCLUDED.reason, "
            "changed_by = EXCLUDED.changed_by, changed_at = EXCLUDED.changed_at"),
            {"u": user_id, "r": role, "s": json.dumps(scopes), "why": reason, "by": admin.user_id,
             "t": now_utc()})
    revoke_user(user_id)  # old sessions must not keep the old role (doc 07)
    return {"synthetic": False, "role": role, "capabilities": capabilities(role), "area_scopes": scopes}


def review_alert(engine: Any, identity: Identity, alert_id: str, status: str, note: str) -> dict | None:
    from sqlalchemy import text

    if live_real.get_alert(engine, identity, alert_id) is None:  # scope + release checked here
        return None
    review = {"synthetic": False, "review_id": uuid.uuid4().hex, "status": status,
              "actor_id": identity.user_id, "created_at": iso(now_utc())}
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO alert_reviews (review_id, alert_id, status, note, actor_id, created_at) "
            "VALUES (:id, :a, :s, :n, :u, :t)"),
            {"id": review["review_id"], "a": alert_id, "s": status, "n": note, "u": identity.user_id,
             "t": now_utc()})
        conn.execute(text("UPDATE alerts SET review_status = :s WHERE alert_id = :a"),
                     {"s": status, "a": alert_id})
    return review


def _jobs() -> dict[str, Callable[[Any], dict]]:
    from worker.jobs import run_fires, run_power_loss

    return {"fires": run_fires,
            "night_lights": lambda e: run_power_loss(e, os.environ.get("NIGHTLIGHT_HISTORY"))}


JOB_IDS = ("fires", "night_lights")


def retry_job(engine: Any, identity: Identity, job_id: str, key: str,
              jobs: dict[str, Callable[[Any], dict]] | None = None) -> dict[str, Any]:
    """Run one worker job now. The same idempotency key never runs a job twice."""
    from sqlalchemy import text

    with engine.begin() as conn:
        inserted = conn.execute(text(
            "INSERT INTO job_runs (idempotency_key, job_id, status, actor_id, started_at) "
            "VALUES (:k, :j, 'running', :u, :t) ON CONFLICT (idempotency_key) DO NOTHING"),
            {"k": key, "j": job_id, "u": identity.user_id, "t": now_utc()}).rowcount
        if not inserted:
            row = conn.execute(text("SELECT job_id, status FROM job_runs WHERE idempotency_key = :k"),
                               {"k": key}).first()
            if row.job_id != job_id:
                raise Conflict("This idempotency key was used for another job.")
            return {"synthetic": False, "job_id": job_id, "status": row.status, "idempotency_key": key}
    result = (jobs or _jobs())[job_id](engine)
    status = JOB_STATUS.get(result.get("status"), "failed")
    with engine.begin() as conn:
        conn.execute(text("UPDATE job_runs SET status = :s, finished_at = :t WHERE idempotency_key = :k"),
                     {"s": status, "t": now_utc(), "k": key})
    return {"synthetic": False, "job_id": job_id, "status": status, "idempotency_key": key}
