"""Decision assistant, rules only (doc 24 section 7, doc 25 U-05). "CIVISAR assistant".

    python -m worker.agents.assistant [--incident <id>] [--role analyst|officer|coordinator|admin]

For one ranked incident it gives a situation line, 2 or 3 options from fixed playbooks, trade-offs,
what we do not know, a checklist and when to look again. It proposes; the officer decides. It never
dispatches, never changes data, and only prints numbers that its inputs contain. Role limits match
the API: analysts get analysis only, officers also route options, coordinators also shelters.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from worker.agents.inputs import (
    AreaFacts,
    area_facts,
    as_json,
    load_published,
    load_table,
    parse_time,
)
from worker.agents.ranking import rank

NAME = "CIVISAR assistant"
ROLE_LEVEL = {"analyst": 1, "officer": 2, "coordinator": 3, "admin": 4}
FIRE_FEED_MINUTES = 30  # worker timer for the FIRMS feed

PLAYBOOKS = {
    "verification": {
        "title": "Hold and verify with a field check",
        "needs": ["field team with a checklist", "contact with local responders"],
        "gain": "decisions rest on what people on the ground report",
        "give_up": "time before any response starts",
        "risk": "the field team enters an area with unknown hazards",
    },
    "medical": {
        "title": "Prepare a medical team and supplies for the area",
        "needs": ["first-aid and trauma kits", "a medical team", "transport"],
        "gain": "care is ready if people are hurt",
        "give_up": "medical capacity held for other incidents",
        "risk": "the need may be smaller or elsewhere; radar results are candidates",
    },
    "power": {
        "title": "Plan generators and lights for essential sites",
        "needs": ["generators", "fuel", "lights"],
        "gain": "essential sites keep working",
        "give_up": "generators and fuel held for other areas",
        "risk": "the night-light signal can come from causes other than a power cut",
    },
    "water": {
        "title": "Check water supply and prepare bottled water",
        "needs": ["bottled water", "water testing kit"],
        "gain": "drinking water is covered while supply is checked",
        "give_up": "water stock held for other areas",
        "risk": "the water site may still be working",
    },
    "evacuation": {
        "title": "Prepare evacuation route options",
        "needs": ["route options from the routing screen", "transport"],
        "gain": "people can move quickly if needed",
        "give_up": "moving people has its own risks and costs",
        "risk": "road status is unknown: no road data is loaded",
        "min_role": "officer",
    },
}


def _date(t: datetime | None) -> str | None:
    return t.strftime("%Y-%m-%d %H:%M UTC") if t else None


def choose(item: dict, f: AreaFacts | None, alerts: list[dict], role: str) -> list[str]:
    """Playbooks in priority order, at most 3, verification always offered."""
    p = item["parts"]
    picks = []
    damage_v = p["damage"]["value"] or 0
    fire = any(a["type"] == "fire_detected" for a in alerts)
    if fire or damage_v >= 0.45 or (f and (f.facilities_hit.get("hospital") or f.facilities_hit.get("clinic"))):
        picks.append("medical")
    # Evacuation only for a current event (a fire detection), never for radar change alone: radar
    # results can be months old by the time they are released.
    if fire and ROLE_LEVEL.get(role, 0) >= ROLE_LEVEL["officer"]:
        picks.append("evacuation")
    if any(a["type"] == "possible_power_loss" for a in alerts) or (f and f.facilities_hit.get("power")):
        picks.append("power")
    if f and f.facilities_hit.get("water"):
        picks.append("water")
    return [*picks[:2], "verification"]


def situation(item: dict, alerts: list[dict], sources: dict) -> str:
    seen = "; ".join(item["reasons"]) if item["reasons"] else "no strong signal in the known data"
    times = [t for t in (parse_time(a.get("detected_at")) for a in alerts) if t]
    when = _date(max(times)) if times else (sources.get("nisar-damage") or {}).get("acquired_at", "date unknown")
    sure = ("much is unknown" if item["could_rank_higher"] else "most parts are known")
    return f"Data shows: {seen}. Latest data: {when}. How sure: {sure}."


def next_review(alerts: list[dict], sources: dict, now: datetime) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    fire_ok = parse_time((sources.get("firms") or {}).get("last_success_at"))
    if fire_ok:
        out["fire feed"] = _date(max(fire_ok + timedelta(minutes=FIRE_FEED_MINUTES), now))
    # The published radar date is a result date, not a pass date, so no pass date is computed here.
    out["radar"] = "after the next NISAR pass and its 72-hour hold"
    return out


def advise(item: dict, f: AreaFacts | None, alerts: list[dict], sources: dict, role: str,
           now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    area_alerts = [a for a in alerts if a["area_id"] == item["area_id"]]
    options = []
    for key in choose(item, f, area_alerts, role):
        pb = PLAYBOOKS[key]
        options.append({"playbook": key, "title": pb["title"], "why": item["reasons"] or ["field check needed"],
                        "needs": pb["needs"], "risks": [pb["risk"]],
                        "trade_off": f"Gain: {pb['gain']}. Give up: {pb['give_up']}."})
    unknown = [u.split(": ", 1)[1] for u in item["unknowns"]]
    if item["parts"]["damage"]["status"] == "known" and "one radar only" in item["parts"]["damage"]["detail"]:
        unknown.append("damage is seen by one radar only")
    checklist = [
        "Field check of the area before acting on radar candidates",
        "Protection and ordnance check before anyone enters damaged buildings",
        "Confirm road status; no closure reported does not mean a road is open",
    ]
    if ROLE_LEVEL.get(role, 0) >= ROLE_LEVEL["coordinator"]:
        checklist.append("Check shelter candidates and capacity ranges before planning moves")
    return {
        "assistant": NAME, "incident_id": item["incident_id"], "area_id": item["area_id"], "role": role,
        "situation": situation(item, area_alerts, sources),
        "score": {"low": item["score_low"], "high": item["score_high"], "rank": item["rank"]},
        "options": options, "we_do_not_know": unknown, "checklist": checklist,
        "next_review": next_review(area_alerts, sources, now),
        "note": "Options, not orders. The officer decides; choices are logged by the API.",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--published", type=Path, default=Path("data/published"))
    ap.add_argument("--table", type=Path, default=Path("data/local/building_table.parquet"))
    ap.add_argument("--incident", help="incident id; default: the top-ranked one")
    ap.add_argument("--role", default="officer", choices=list(ROLE_LEVEL))
    args = ap.parse_args(argv)
    alerts, sources = load_published(args.published)
    facts = area_facts(load_table(args.table))
    ranked = rank(alerts, facts, sources)
    item = next((i for i in ranked["items"] if i["incident_id"] == args.incident), ranked["items"][0])
    print(as_json(advise(item, facts.get(item["area_id"]), alerts, sources, args.role)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
