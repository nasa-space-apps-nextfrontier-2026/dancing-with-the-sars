"""Area briefs (M3-03): a frozen area summary plus source footnotes, printable as plain HTML.

Briefs expire after 8 hours and never contain records still on the 72-hour hold. Every read
re-checks the reader (every role, admin included): signed in, area in scope, brief not expired; sections above the reader's role are removed again at read time.
The print page escapes every value and loads nothing from outside.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import uuid
from typing import Any

from backend.app.core.permissions import ROLE_LEVEL
from backend.app.core.security import Identity
from backend.app.policy.release import now_utc
from backend.app.policy.scope import area_in_scope
from backend.app.services import summary_real
from backend.app.services.live_real import iso
from backend.app.services.radar_real import data_root

LIFETIME = dt.timedelta(hours=8)
SECTIONS = ["people", "services", "what_to_bring", "facilities", "hazards", "evidence"]


def _footnotes(source_ids: set[str]) -> list[dict[str, Any]]:
    path = data_root() / "local" / "radar_contract" / "sources.json"
    records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    return [r for r in records if r["source_id"] in source_ids]


def _filter_for(payload: dict[str, Any], identity: Identity) -> dict[str, Any]:
    """Remove sections above the reader's role (re-run on every read)."""
    lvl = ROLE_LEVEL.get(identity.role, 0)
    summary = dict(payload["area_summary"])
    omitted = list(payload["omitted_sections"])
    for key, perm, role in (("route_options", "routes", "officer"),
                            ("shelter_candidates", "shelters", "coordinator")):
        allowed = lvl >= ROLE_LEVEL[role]
        summary["permissions"] = summary["permissions"] | {perm: allowed}
        if not allowed:
            summary[key] = []
            note = f"{key}: needs {role} role"
            if note not in omitted:
                omitted.append(note)
    return payload | {"area_summary": summary, "omitted_sections": omitted}


def create(engine: Any, identity: Identity, area_id: str) -> dict[str, Any] | None:
    from sqlalchemy import text

    if not area_in_scope(area_id, identity.area_scopes):
        raise PermissionError(area_id)
    summary = summary_real.area_summary(engine, area_id, identity)
    if summary is None:
        return None
    sources = {s for v in summary["evidence"] for s in v["source"]}
    created = now_utc()
    payload = {
        "synthetic": False, "report_id": uuid.uuid4().hex, "area_summary": summary,
        "included_sections": SECTIONS,
        "omitted_sections": ["route_options: no road data loaded yet",
                             "shelter_candidates: no shelter data loaded yet"],
        "source_footnotes": _footnotes(sources), "live_view_path": f"/areas/{area_id}",
        "expires_at": iso(created + LIFETIME),
    }
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO briefs (report_id, owner, owner_role, area_id, created_at, expires_at, payload) "
            "VALUES (:id, :o, :r, :a, :c, :e, CAST(:p AS jsonb))"),
            {"id": payload["report_id"], "o": identity.user_id, "r": identity.role, "a": area_id,
             "c": created, "e": created + LIFETIME, "p": json.dumps(payload)})
    return _filter_for(payload, identity)


def read(engine: Any, identity: Identity | None, report_id: str) -> dict[str, Any] | None:
    from sqlalchemy import text

    if identity is None:
        return None
    with engine.connect() as conn:
        row = conn.execute(text("SELECT area_id, expires_at, payload FROM briefs WHERE report_id = :i"),
                           {"i": report_id}).first()
    if row is None:
        return None
    if row.expires_at < now_utc() or not area_in_scope(row.area_id, identity.area_scopes):
        return None
    return _filter_for(row.payload, identity)


def to_html(brief: dict[str, Any]) -> str:
    e = html.escape
    s = brief["area_summary"]
    p = s["people"]

    def rng(v: dict[str, Any]) -> str:
        return f"{v['low']:,}–{v['high']:,} ({e(v['label'])})"

    rows = "".join(f"<tr><td>{e(k.replace('_', ' '))}</td><td>{rng(v)}</td></tr>" for k, v in p.items())
    services = "".join(f"<li>{e(x['type'])}: {e(x['status'])} ({e(x['label'])})</li>" for x in s["services"])
    bring = "".join(f"<li>{e(x['item'])}</li>" for x in s["what_to_bring"])
    hazards = "".join(f"<li>{e(h['type'].replace('_', ' '))}</li>" for h in s["hazards"]) or "<li>None recorded</li>"
    notes = "".join(f"<li>{e(f['name'])} — {e(f['provider'])}. {e(f['licence'])}</li>"
                    for f in brief["source_footnotes"])
    omitted = "".join(f"<li>{e(o)}</li>" for o in brief["omitted_sections"])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>CIVISAR brief</title><style>body{{font:14px/1.4 sans-serif;color:#000;background:#fff;margin:24px}}
table{{border-collapse:collapse}}td{{border:1px solid #999;padding:4px 8px}}.r{{border:2px solid #000;padding:6px}}</style>
</head><body><p class="r"><strong>RESTRICTED.</strong> For authorised responders only. Do not share publicly.</p>
<h1>{e(s['name'])}</h1><p>As of {e(s['as_of'])}. Expires {e(str(brief['expires_at']))}.</p>
<p>{e(s['warning'])}</p><h2>People (ranges)</h2><table>{rows}</table>
<h2>Services</h2><ul>{services}</ul><h2>What to bring</h2><ul>{bring}</ul>
<h2>Hazards</h2><ul>{hazards}</ul><h2>Not included</h2><ul>{omitted}</ul>
<h2>Sources</h2><ol>{notes}</ol></body></html>"""
