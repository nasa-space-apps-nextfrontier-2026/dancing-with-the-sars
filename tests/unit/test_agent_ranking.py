"""Ranking agent on synthetic incidents (doc 25 U-05: reasons and unknowns shown; a part with no data is
unknown, not zero; no banned wording). All values are made up for the test."""

import json
from datetime import UTC, datetime

import pytest

from worker.agents import ranking
from worker.agents.inputs import AreaFacts

NOW = datetime(2026, 11, 14, 12, tzinfo=UTC)
OK = {"firms": {"id": "firms", "last_success_at": "2026-11-14T11:00:00Z", "failure": ""},
      "black-marble": {"id": "black-marble", "last_success_at": "2026-11-14T00:00:00Z", "failure": ""}}


def facts(area, *, people=None, cand=None, corroborated=0, assessed=5, mapped=None, hit=None):
    cand = cand or {}
    return AreaFacts(area_id=area, buildings=50,
                     residents_low=None if people is None else people[0],
                     residents_high=None if people is None else people[1],
                     candidate_cells={k: cand.get(k, 0) for k in ranking.CANDIDATES},
                     corroborated_cells=corroborated, assessed_cells=assessed, unknown_cells=0,
                     facilities_mapped=mapped or {}, facilities_hit=hit or {}, run_id="run-a")


def alert(aid, area, kind="fire_detected", n=1, detected="2026-11-14T00:00:00Z", review="unreviewed"):
    return {"alert_id": aid, "area_id": area, "type": kind, "independent_source_count": n,
            "detected_at": detected, "review_status": review}


def by_id(result):
    return {i["incident_id"]: i for i in result["items"]}


def test_unknown_is_not_zero_and_widens_the_range():
    r = ranking.rank([], {"a1": facts("a1", cand={"moderate_candidate": 1})}, OK, now=NOW)
    item = r["items"][0]
    assert item["parts"]["people"]["status"] == "unknown" and item["parts"]["people"]["points"] is None
    assert item["score_high"] - item["score_low"] >= 30 + 5  # people + access unknown
    assert any(u.startswith("people:") for u in item["unknowns"])


def test_damaged_area_without_alert_is_listed_and_nothing_hidden():
    fx = {"a1": facts("a1", cand={"possible_candidate": 2}), "a2": facts("a2"), "a3": facts("a3")}
    r = ranking.rank([alert("f1", "a3")], fx, OK, now=NOW)
    ids = {i["incident_id"] for i in r["items"]}
    assert ids == {"damage-a1", "f1"}            # a2 has neither damage nor alert
    assert [i["rank"] for i in r["items"]] == [1, 2]


def test_reasons_and_order():
    fx = {"a1": facts("a1", people=(900, 1500), cand={"destroyed_or_severe_candidate": 1}, corroborated=1,
                      mapped={"hospital": 1}, hit={"hospital": 1}),
          "a2": facts("a2", people=(50, 80), cand={"possible_candidate": 1})}
    r = ranking.rank([alert("f2", "a2")], fx, OK, now=NOW)
    first, second = r["items"]
    assert first["incident_id"] == "damage-a1" and second["incident_id"] == "f2"
    assert first["reasons"] == ["about 900-1,500 residents (pre-displacement estimate)",
                                "hospital building in a damage-candidate cell"]
    assert len(first["reasons"]) <= 2 and first["score_low"] <= first["score_mid"] <= first["score_high"]


def test_second_radar_counts_more_and_fire_feed_status_matters():
    one = ranking.rank([], {"a": facts("a", cand={"moderate_candidate": 1})}, OK, now=NOW)["items"][0]
    two = ranking.rank([], {"a": facts("a", cand={"moderate_candidate": 1}, corroborated=1)}, OK,
                       now=NOW)["items"][0]
    assert two["parts"]["damage"]["value"] > one["parts"]["damage"]["value"]
    assert one["parts"]["fire"] == {"status": "known", "value": 0.0, "detail": "no fire detected in the latest feed",
                                    "weight": 15, "points": 0.0}
    down = ranking.rank([], {"a": facts("a", cand={"moderate_candidate": 1})}, {}, now=NOW)["items"][0]
    assert down["parts"]["fire"]["status"] == "unknown" and down["parts"]["services"]["status"] == "unknown"


def test_unknowns_do_not_push_an_incident_up():
    fx = {"known": facts("known", people=(10, 20), cand={"destroyed_or_severe_candidate": 1}, corroborated=1,
                         mapped={"school": 1}),
          "blank": facts("blank", assessed=0)}
    r = ranking.rank([alert("f", "blank")], fx, {}, now=NOW)
    first, second = r["items"]
    assert first["incident_id"] == "damage-known" and first["score_low"] > second["score_low"]
    assert second["score_high"] > first["score_high"] and second["could_rank_higher"]


def test_time_rises_while_unreviewed():
    fx = {"a": facts("a")}
    fresh = ranking.rank([alert("x", "a", detected="2026-11-14T11:00:00Z")], fx, OK, now=NOW)["items"][0]
    old = ranking.rank([alert("x", "a", detected="2026-11-10T00:00:00Z")], fx, OK, now=NOW)["items"][0]
    done = ranking.rank([alert("x", "a", review="reviewed")], fx, OK, now=NOW)["items"][0]
    assert fresh["parts"]["time"]["value"] < old["parts"]["time"]["value"] == 1.0
    assert done["parts"]["time"]["value"] == 0.0


def test_weights_must_add_to_100(tmp_path):
    cfg = json.loads(ranking.CONFIG.read_text(encoding="utf-8"))
    cfg["weights"]["people"] = 31
    bad = tmp_path / "w.json"
    bad.write_text(json.dumps(cfg))
    with pytest.raises(ValueError):
        ranking.load_config(bad)


def test_no_banned_wording():
    fx = {"a1": facts("a1", people=(1, 2), cand={"destroyed_or_severe_candidate": 1}, corroborated=1,
                      mapped={"school": 1}, hit={"school": 1})}
    text = json.dumps(ranking.rank([alert("p", "a1", "possible_power_loss", 2)], fx, OK, now=NOW)).lower()
    assert "safe" not in text and "confirmed damage" not in text
