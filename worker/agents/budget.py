"""Rebuild budget and duration estimator (doc 24 section 9, doc 25 U-05). Planning indication only.

    python -m worker.agents.budget [--table data/local/building_table.parquet] [--area <H3 r8>]

Cost range = affected floor area x damage share x cost per m2, with the low end using the low floor
count and low cost, the high end the high floor count and high cost. Residential and non-residential
floor area use their own cost ranges. Duration range = start delay + work volume / (crews x m2 per
crew per month): the low end uses the short delay and the most capacity, the high end the opposite.

Every input comes from budget_assumptions.json with its source or the word "assumption".
Never a single number, never a quote. Restricted output: analyst and coordinator roles only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from worker.agents.inputs import CANDIDATES, as_json, load_table

ASSUMPTIONS = Path(__file__).with_name("budget_assumptions.json")
LABEL = "Planning indication only"
LIMITS = [
    ("Radar misses some damage and flags some change that is not damage; damage classes are 0.1 km2 cell "
     "results, applied to every building in the cell."),
    "Floor area uses estimated heights (ranges; towers are underestimated).",
    "Costs are anchored to a World Bank assessment for Syria and adjusted; Lebanese costs are not yet checked.",
    "Crew numbers, crew output and start delays are editable assumptions, not sourced figures.",
]


def load_assumptions(path: Path = ASSUMPTIONS) -> dict:
    a = json.loads(path.read_text(encoding="utf-8"))
    for key in ("cost_per_m2", "crews", "m2_per_crew_month", "start_delay_months"):
        block = a[key] if key != "cost_per_m2" else a[key]["residential"]
        if not block.get("source"):
            raise ValueError(f"{key} has no source or 'assumption' note")
    return a


def floor_areas(table: Any) -> dict[str, dict[str, dict[str, float]]]:
    """{class: {"residential"/"non_residential": {"low": m2, "high": m2}}} for candidate cells."""
    cand = table[table["damage_class"].isin(CANDIDATES)]
    out: dict[str, dict[str, dict[str, float]]] = {}
    for cls in CANDIDATES:
        g = cand[cand["damage_class"] == cls]
        out[cls] = {}
        for kind, sel in (("residential", g["residential"]), ("non_residential", ~g["residential"])):
            sub = g[sel]
            out[cls][kind] = {"low": float((sub["footprint_m2"] * sub["floors_low"]).sum()),
                              "high": float((sub["footprint_m2"] * sub["floors_high"]).sum())}
    return out


def estimate(areas: dict[str, dict[str, dict[str, float]]], a: dict, scope: str = "whole_demo_box") -> dict[str, Any]:
    """scope: "per_neighbourhood" or "whole_demo_box" (selects the crew numbers)."""
    share = a["damage_share"]
    cost_low = cost_high = work_low = work_high = 0.0
    by_class = {}
    for cls in CANDIDATES:
        c_lo = c_hi = w_lo = w_hi = 0.0
        for kind in ("residential", "non_residential"):
            fl = areas.get(cls, {}).get(kind, {"low": 0.0, "high": 0.0})
            unit = a["cost_per_m2"][kind]
            w_lo += fl["low"] * share[cls]
            w_hi += fl["high"] * share[cls]
            c_lo += fl["low"] * share[cls] * unit["low"]
            c_hi += fl["high"] * share[cls] * unit["high"]
        by_class[cls] = {"work_m2_low": round(w_lo), "work_m2_high": round(w_hi),
                         "cost_usd_low": round(c_lo, -3), "cost_usd_high": round(c_hi, -3)}
        cost_low, cost_high, work_low, work_high = cost_low + c_lo, cost_high + c_hi, work_low + w_lo, work_high + w_hi
    crews = a["crews"][scope]
    fast = crews["high"] * a["m2_per_crew_month"]["high"]
    slow = crews["low"] * a["m2_per_crew_month"]["low"]
    months_low = a["start_delay_months"]["low"] + work_low / fast
    months_high = a["start_delay_months"]["high"] + work_high / slow
    return {
        "label": LABEL,
        "cost_usd": {"low": round(cost_low, -3), "high": round(cost_high, -3)},
        "duration_months": {"low": round(months_low, 1), "high": round(months_high, 1)},
        "work_floor_area_m2": {"low": round(work_low), "high": round(work_high)},
        "crew_scale": scope,
        "by_damage_class": by_class,
        "assumptions": {k: a[k] for k in ("currency", "cost_per_m2", "damage_share", "crews", "m2_per_crew_month",
                                          "start_delay_months")},
        "limits": LIMITS,
    }


def area_budget(table: Any, area_id: str | None = None, assumptions: dict | None = None) -> dict[str, Any]:
    a = assumptions or load_assumptions()
    sub = table if area_id is None else table[table["h3_r8"] == area_id]
    result = estimate(floor_areas(sub), a, "whole_demo_box" if area_id is None else "per_neighbourhood")
    result["area_id"] = area_id or "south-lebanon-demo"
    result["buildings_in_candidate_cells"] = int(sub["damage_class"].isin(CANDIDATES).sum())
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", type=Path, default=Path("data/local/building_table.parquet"))
    ap.add_argument("--area", help="H3 r8 neighbourhood; default: the whole demo box")
    ap.add_argument("--out", type=Path, default=Path("data/local/agents/budget.json"))
    args = ap.parse_args(argv)
    result = area_budget(load_table(args.table), args.area)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(as_json(result), encoding="utf-8")
    print(as_json({k: result[k] for k in ("area_id", "label", "cost_usd", "duration_months", "work_floor_area_m2",
                                          "buildings_in_candidate_cells")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
