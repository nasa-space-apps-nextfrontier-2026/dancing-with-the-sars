"""Ranking agent (doc 24 section 6.1): orders incidents by a transparent 0-100 score.

    python -m worker.agents.ranking [--published data/published] [--table data/local/building_table.parquet]

Incidents: every published alert, plus every neighbourhood (H3 r8) with radar damage candidates
and no alert, so a damaged area is never left out. Each incident gets seven named parts with
weights from ranking_weights.json. A part without data is UNKNOWN, never zero: the score is a range,
low = unknown parts count 0, high = unknown parts count in full. Rank by what is known (the low
end), then the high end, then people, then area id: an unknown never pushes an incident up as if it
were evidence. Incidents whose range is wide are flagged "could rank higher". Ranking only orders;
it never hides an incident.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from worker.agents.inputs import (
    CANDIDATES,
    AreaFacts,
    area_facts,
    as_json,
    load_published,
    load_table,
    parse_time,
    source_ok,
)

CONFIG = Path(__file__).with_name("ranking_weights.json")
LEVEL_WORDS = {"destroyed_or_severe_candidate": "destroyed or severe", "moderate_candidate": "moderate",
               "possible_candidate": "possible"}


def load_config(path: Path = CONFIG) -> dict:
    import json

    cfg = json.loads(path.read_text(encoding="utf-8"))
    if sum(cfg["weights"].values()) != 100:
        raise ValueError("ranking weights must add up to 100")
    return cfg


def part(status: str, value: float = 0.0, detail: str = "") -> dict:
    """status: known, unknown or not_applicable; value 0-1 when known."""
    return {"status": status, "value": round(value, 3) if status == "known" else None, "detail": detail}


def incidents(alerts: list[dict], facts: dict[str, AreaFacts]) -> list[dict]:
    out = [{"incident_id": a["alert_id"], "area_id": a["area_id"], "kind": a["type"], "alerts": [a]}
           for a in alerts]
    alerted = {a["area_id"] for a in alerts}
    for area, f in sorted(facts.items()):
        if area not in alerted and sum(f.candidate_cells.values()) > 0:
            out.append({"incident_id": f"damage-{area}", "area_id": area, "kind": "damage_candidate_area",
                        "alerts": []})
    return out


def score_parts(inc: dict, f: AreaFacts | None, area_alerts: list[dict], sources: dict, cfg: dict,
                now: datetime) -> dict[str, dict]:
    p: dict[str, dict] = {}
    # People: residents of the area (pre-displacement estimate)
    if f is None or f.residents_high is None:
        p["people"] = part("unknown", detail="population not loaded")
    else:
        p["people"] = part("known", min(1.0, f.residents_high / cfg["people_reference_high"]),
                           f"about {f.residents_low:,}-{f.residents_high:,} residents (pre-displacement estimate)")
    # Facilities in damage-candidate cells (OSM-tagged only)
    if f is None or sum(f.facilities_mapped.values()) == 0:
        p["facility"] = part("unknown", detail="no facilities mapped in OSM here")
    else:
        hit = {u: n for u, n in f.facilities_hit.items() if n}
        if hit:
            best = max(hit, key=lambda u: cfg["facility_value"][u])
            p["facility"] = part("known", cfg["facility_value"][best],
                                 f"{best} building in a damage-candidate cell")
        else:
            p["facility"] = part("known", 0.0, "mapped facilities are outside damage-candidate cells")
    # Damage level and evidence strength
    if f is None or f.assessed_cells == 0:
        p["damage"] = part("unknown", detail="radar could not assess this area")
    elif sum(f.candidate_cells.values()) == 0:
        p["damage"] = part("known", 0.0, "no damage candidate detected by radar")
    else:
        top = next(k for k in CANDIDATES if f.candidate_cells[k])
        factor = 1.0 if f.corroborated_cells else cfg["single_sensor_factor"]
        agree = "; a second radar agrees" if f.corroborated_cells else "; one radar only"
        p["damage"] = part("known", cfg["damage_class_value"][top] * factor,
                           f"radar damage candidate ({LEVEL_WORDS[top]}){agree}")
    # Fire
    fires = [a for a in area_alerts if a["type"] == "fire_detected"]
    if fires:
        best = max(a.get("independent_source_count", 1) for a in fires)
        p["fire"] = part("known", 1.0 if best >= 2 else 0.7,
                         f"fire detected ({best} satellite{'s' if best != 1 else ''})")
    elif source_ok(sources, "firms"):
        p["fire"] = part("known", 0.0, "no fire detected in the latest feed")
    else:
        p["fire"] = part("unknown", detail="fire feed not available")
    # Services (power from night lights; water and internet have no data yet)
    power = [a for a in area_alerts if a["type"] == "possible_power_loss"]
    if power:
        both = any(a.get("independent_source_count", 1) >= 2 for a in power)
        p["services"] = part("known", 1.0 if both else 0.5,
                             "possible power loss" + (" (both satellites)" if both else " (one satellite)"))
    elif source_ok(sources, "black-marble"):
        p["services"] = part("known", 0.0, "no power loss signal; water and internet unknown")
    else:
        p["services"] = part("unknown", detail="night-light data not available; water and internet unknown")
    # Time since detection (older and unreviewed rises slowly)
    open_alerts = [a for a in inc["alerts"] if a.get("review_status", "unreviewed") == "unreviewed"]
    times = [t for t in (parse_time(a.get("detected_at")) for a in open_alerts) if t]
    if not inc["alerts"]:
        p["time"] = part("not_applicable", detail="radar result, not a timed event")
    elif not times:
        p["time"] = part("known", 0.0, "reviewed")
    else:
        hours = max(0.0, (now - min(times)).total_seconds() / 3600)
        p["time"] = part("known", min(1.0, hours / cfg["time_full_after_hours"]),
                         f"unreviewed for {hours:.0f} hours")
    # Access: no road data yet
    p["access"] = part("unknown", detail="no road data loaded")
    return p


def rank(alerts: list[dict], facts: dict[str, AreaFacts], sources: dict, cfg: dict | None = None,
         now: datetime | None = None) -> dict[str, Any]:
    cfg = cfg or load_config()
    now = now or datetime.now(UTC)
    w = cfg["weights"]
    items = []
    for inc in incidents(alerts, facts):
        f = facts.get(inc["area_id"])
        area_alerts = [a for a in alerts if a["area_id"] == inc["area_id"]]
        parts = score_parts(inc, f, area_alerts, sources, cfg, now)
        for name, pt in parts.items():
            pt["weight"] = w[name]
            pt["points"] = round(w[name] * pt["value"], 1) if pt["status"] == "known" else None
        low = sum(pt["points"] for pt in parts.values() if pt["status"] == "known")
        high = low + sum(w[n] for n, pt in parts.items() if pt["status"] == "unknown")
        reasons = sorted((pt for pt in parts.values() if pt["status"] == "known" and pt["points"]),
                         key=lambda pt: -pt["points"])[:2]
        unknown_points = high - low
        items.append({
            "incident_id": inc["incident_id"], "area_id": inc["area_id"], "kind": inc["kind"],
            "score_low": round(low, 1), "score_high": round(high, 1), "score_mid": round((low + high) / 2, 1),
            "parts": parts, "reasons": [r["detail"] for r in reasons],
            "unknowns": [f"{n}: {pt['detail']}" for n, pt in parts.items() if pt["status"] == "unknown"],
            "people_high": f.residents_high if f else None,
            "could_rank_higher": unknown_points >= cfg.get("wide_range_points", 40),
        })
    items.sort(key=lambda i: (-i["score_low"], -i["score_high"], -(i["people_high"] or -1), i["area_id"]))
    for n, item in enumerate(items, 1):
        item["rank"] = n
    ages = {name: s.get("last_success_at") for name, s in sources.items()}
    return {"generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "weights": w, "data_age": ages,
            "radar_run": next((f.run_id for f in facts.values() if f.run_id), None),
            "note": ("Order by what is known (score_low). Every incident stays listed. Unknown parts widen the "
                     "range; could_rank_higher marks incidents with much unknown."),
            "items": items}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--published", type=Path, default=Path("data/published"))
    ap.add_argument("--table", type=Path, default=Path("data/local/building_table.parquet"))
    ap.add_argument("--out", type=Path, default=Path("data/local/agents/ranking.json"))
    args = ap.parse_args(argv)
    alerts, sources = load_published(args.published)
    result = rank(alerts, area_facts(load_table(args.table)), sources)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(as_json(result), encoding="utf-8")
    top = [(i["rank"], i["kind"], i["score_low"], i["score_high"], i["reasons"]) for i in result["items"][:5]]
    print(as_json({"incidents": len(result["items"]), "top5": top}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
