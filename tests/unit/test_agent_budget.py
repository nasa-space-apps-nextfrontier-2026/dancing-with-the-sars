"""Budget estimator (doc 25 U-05: returns a range and lists its assumptions; no banned wording).
Floor areas here are made up for the test."""

import json

import pytest

from worker.agents import budget

A = budget.load_assumptions()


def areas(res_low=0.0, res_high=0.0, cls="destroyed_or_severe_candidate"):
    out = {c: {"residential": {"low": 0.0, "high": 0.0}, "non_residential": {"low": 0.0, "high": 0.0}}
           for c in budget.CANDIDATES}
    out[cls]["residential"] = {"low": res_low, "high": res_high}
    return out


def test_worked_example():
    r = budget.estimate(areas(1000.0, 2000.0), A)
    assert r["cost_usd"] == {"low": 450_000, "high": 1_800_000}     # 1000 x 100% x 450; 2000 x 100% x 900
    assert r["work_floor_area_m2"] == {"low": 1000, "high": 2000}
    assert r["duration_months"]["low"] == pytest.approx(3 + 1000 / (800 * 300), abs=0.05)
    assert r["duration_months"]["high"] == pytest.approx(9 + 2000 / (200 * 150), abs=0.05)
    hood = budget.estimate(areas(1000.0, 2000.0), A, "per_neighbourhood")
    assert hood["duration_months"]["high"] == pytest.approx(9 + 2000 / (10 * 150), abs=0.05)
    assert hood["cost_usd"] == r["cost_usd"]                         # crews change time, not cost


def test_shares_and_ranges():
    possible = budget.estimate(areas(1000.0, 1000.0, "possible_candidate"), A)
    assert possible["work_floor_area_m2"]["low"] == 200            # possible: 20%
    for r in (possible, budget.estimate(areas(10.0, 50.0, "moderate_candidate"), A)):
        assert r["cost_usd"]["low"] <= r["cost_usd"]["high"]
        assert r["duration_months"]["low"] <= r["duration_months"]["high"]
    nothing = budget.estimate(areas(), A)
    assert nothing["cost_usd"] == {"low": 0, "high": 0}


def test_label_assumptions_and_sources():
    r = budget.estimate(areas(100.0, 200.0), A)
    assert r["label"] == "Planning indication only" and r["limits"]
    assert set(r["assumptions"]) >= {"cost_per_m2", "damage_share", "crews", "m2_per_crew_month"}
    for key in ("crews", "m2_per_crew_month", "start_delay_months"):
        assert A[key]["status"] in ("assumption", "sourced", "sourced_with_adjustment")
    assert "worldbank.org" in A["cost_per_m2"]["residential"]["source"]


def test_missing_source_is_refused(tmp_path):
    bad = json.loads(budget.ASSUMPTIONS.read_text(encoding="utf-8"))
    bad["crews"]["source"] = ""
    f = tmp_path / "a.json"
    f.write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        budget.load_assumptions(f)


def test_no_banned_wording():
    text = json.dumps(budget.estimate(areas(100.0, 200.0), A)).lower()
    assert "safe" not in text and "confirmed damage" not in text and "quote" not in text.replace("never a quote", "")


def test_floor_areas_from_table():
    pd = pytest.importorskip("pandas")
    t = pd.DataFrame({"damage_class": ["moderate_candidate", "moderate_candidate", "no_detected_change"],
                      "residential": [True, False, True], "footprint_m2": [100.0, 50.0, 999.0],
                      "floors_low": [1, 2, 5], "floors_high": [3, 4, 5], "h3_r8": ["a", "a", "a"]})
    fa = budget.floor_areas(t)
    assert fa["moderate_candidate"]["residential"] == {"low": 100.0, "high": 300.0}
    assert fa["moderate_candidate"]["non_residential"] == {"low": 100.0, "high": 200.0}
    r = budget.area_budget(t, "a", A)
    assert r["buildings_in_candidate_cells"] == 2
