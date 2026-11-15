"""Insights agent (doc 24 section 6.2): short template sentences built only from computed values.

    python -m worker.agents.insights

Every insight carries the values it was built from, its sources and the date of the data. If a value
cannot be computed the insight says what is unknown instead; no number is generated.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from worker.agents.inputs import (
    AreaFacts,
    area_facts,
    as_json,
    load_published,
    load_table,
)
from worker.agents.ranking import rank

TOP = 5


def _insight(text: str, values: dict, sources: list[str], date: str | None) -> dict[str, Any]:
    return {"text": text, "values": values, "sources": sources, "date": date}


def insights(ranking: dict, facts: dict[str, AreaFacts], alerts: list[dict], sources: dict) -> list[dict]:
    out: list[dict] = []
    radar_date = (sources.get("nisar-damage") or {}).get("acquired_at")
    fire_date = (sources.get("firms") or {}).get("last_success_at")
    light_date = (sources.get("black-marble") or {}).get("last_success_at")
    items = ranking["items"]

    damaged = [f for f in facts.values() if sum(f.candidate_cells.values())]
    both = [f for f in damaged if f.corroborated_cells]
    if damaged:
        out.append(_insight(
            f"A second radar agrees in {len(both)} of {len(damaged)} neighbourhoods with radar damage candidates.",
            {"agreeing": len(both), "with_candidates": len(damaged)}, ["NISAR", "Sentinel-1"], radar_date))

    top = items[:TOP]
    if top:
        with_facility = [i for i in top if (i["parts"]["facility"]["value"] or 0) > 0]
        out.append(_insight(
            f"{len(with_facility)} of the {len(top)} highest-ranked incidents have a mapped facility "
            "in a damage-candidate cell.",
            {"with_facility": len(with_facility), "top": len(top)}, ["OpenStreetMap", "NISAR"], radar_date))
        wide = [i for i in items if i["could_rank_higher"]]
        if wide:
            out.append(_insight(
                f"{len(wide)} of {len(items)} incidents could rank higher once missing data arrives.",
                {"could_rank_higher": len(wide), "incidents": len(items)}, ["CIVISAR ranking"],
                ranking["generated_at"][:10]))

    if all(f.residents_high is None for f in facts.values()):
        out.append(_insight("People are unknown for every incident: the population estimate is not loaded yet.",
                            {}, ["WorldPop (not loaded)"], None))

    fires = [a for a in alerts if a["type"] == "fire_detected"]
    if fires:
        in_damage = {a["area_id"] for a in fires} & {f.area_id for f in damaged}
        multi = sum(1 for a in fires if a.get("independent_source_count", 1) >= 2)
        out.append(_insight(
            f"{len(fires)} fire detection{'s' if len(fires) != 1 else ''} in the latest feed; "
            f"{len(in_damage)} in a neighbourhood with radar damage candidates; {multi} seen by two satellites.",
            {"fires": len(fires), "in_damage_areas": len(in_damage), "two_satellites": multi},
            ["NASA FIRMS"], fire_date))
    elif fire_date:
        out.append(_insight("No fire detected in the demo box in the latest feed.", {"fires": 0}, ["NASA FIRMS"],
                            fire_date))

    power = [a for a in alerts if a["type"] == "possible_power_loss"]
    if power:
        two = sum(1 for a in power if a.get("independent_source_count", 1) >= 2)
        out.append(_insight(f"Both satellites agree on {two} of {len(power)} possible power loss alerts.",
                            {"both": two, "alerts": len(power)}, ["NASA Black Marble"], light_date))
    elif not light_date:
        out.append(_insight("Power status is unknown: night-light data is not loaded.", {}, ["NASA Black Marble"],
                            None))

    cells = sum(f.assessed_cells + f.unknown_cells for f in facts.values())
    unknown = sum(f.unknown_cells for f in facts.values())
    if cells:
        out.append(_insight(
            f"The radar could not assess {unknown} of {cells} cells ({unknown / cells:.0%}); "
            "no result there does not mean no damage.",
            {"unknown_cells": unknown, "cells": cells, "unknown_percent": round(100 * unknown / cells)},
            ["NISAR"], radar_date))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--published", type=Path, default=Path("data/published"))
    ap.add_argument("--table", type=Path, default=Path("data/local/building_table.parquet"))
    ap.add_argument("--out", type=Path, default=Path("data/local/agents/insights.json"))
    args = ap.parse_args(argv)
    alerts, sources = load_published(args.published)
    facts = area_facts(load_table(args.table))
    result = {"items": insights(rank(alerts, facts, sources), facts, alerts, sources)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(as_json(result), encoding="utf-8")
    print(as_json([i["text"] for i in result["items"]]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
