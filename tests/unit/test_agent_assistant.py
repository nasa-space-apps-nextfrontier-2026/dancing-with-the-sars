"""Decision assistant (doc 24 section 7, doc 25 U-05): options not orders, role limits, unknowns listed,
no number that the inputs do not contain, no banned wording. Synthetic inputs."""

import json
import re
from datetime import UTC, datetime

from worker.agents import assistant, ranking
from worker.agents.inputs import AreaFacts

NOW = datetime(2026, 11, 14, 12, tzinfo=UTC)
SOURCES = {"nisar-damage": {"id": "nisar-damage", "acquired_at": "2026-07-21T00:00:00Z",
                            "last_success_at": "2026-11-14T00:00:00Z", "failure": ""},
           "firms": {"id": "firms", "last_success_at": "2026-11-14T11:00:00Z", "failure": ""}}


def setup(fire=True, hit=None, corroborated=0):
    f = AreaFacts(area_id="a", buildings=10, residents_low=None, residents_high=None,
                  candidate_cells={"destroyed_or_severe_candidate": 1, "moderate_candidate": 0, "possible_candidate": 0},
                  corroborated_cells=corroborated, assessed_cells=3, unknown_cells=0,
                  facilities_mapped={"hospital": 1, "water": 1}, facilities_hit=hit or {}, run_id="run-a")
    alerts = ([{"alert_id": "f1", "area_id": "a", "type": "fire_detected", "independent_source_count": 2,
                "detected_at": "2026-11-14T10:00:00Z", "review_status": "unreviewed"}] if fire else [])
    item = ranking.rank(alerts, {"a": f}, SOURCES, now=NOW)["items"][0]
    return item, f, alerts


def test_options_and_role_limits():
    item, f, alerts = setup(hit={"hospital": 1, "water": 1})
    officer = assistant.advise(item, f, alerts, SOURCES, "officer", NOW)
    analyst = assistant.advise(item, f, alerts, SOURCES, "analyst", NOW)
    assert officer["assistant"] == "CIVISAR assistant" and 2 <= len(officer["options"]) <= 3
    assert officer["options"][-1]["playbook"] == "verification"
    assert "evacuation" not in [o["playbook"] for o in analyst["options"]]       # routes: officer and above
    assert "evacuation" in [o["playbook"] for o in officer["options"]]           # a current fire
    assert not any("shelter" in c.lower() for c in officer["checklist"])         # shelters: coordinator and above
    coord = assistant.advise(item, f, alerts, SOURCES, "coordinator", NOW)
    assert any("shelter" in c.lower() for c in coord["checklist"])
    for o in officer["options"]:
        assert o["why"] and o["needs"] and o["risks"] and o["trade_off"].startswith("Gain:")


def test_unknowns_and_next_review():
    item, f, _ = setup(fire=False)
    r = assistant.advise(item, f, [], SOURCES, "officer", NOW)
    assert "population not loaded" in r["we_do_not_know"]
    assert "damage is seen by one radar only" in r["we_do_not_know"]
    assert "evacuation" not in [o["playbook"] for o in r["options"]]  # radar change alone: no evacuation
    assert r["next_review"]["radar"] == "after the next NISAR pass and its 72-hour hold"  # no guessed date
    assert r["next_review"]["fire feed"] == "2026-11-14 12:00 UTC"
    assert r["note"].startswith("Options, not orders")


def test_numbers_come_from_inputs_and_no_banned_wording():
    item, f, alerts = setup(hit={"hospital": 1})
    r = assistant.advise(item, f, alerts, SOURCES, "officer", NOW)
    words = json.dumps({k: r[k] for k in ("situation", "options", "we_do_not_know", "checklist")})
    inputs = json.dumps([item, alerts, SOURCES])
    for number in set(re.findall(r"\d+", words)):
        assert number in inputs, number
    low = json.dumps(r).lower()
    assert "safe" not in low and "confirmed damage" not in low and "caused by" not in low
