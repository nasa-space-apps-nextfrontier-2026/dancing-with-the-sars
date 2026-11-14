"""Insights agent (doc 24 6.2): every sentence has sources and the values it was built from; every
number in the text comes from those values; unknown data is said, not filled. Synthetic inputs."""

import json
import re
from datetime import UTC, datetime

from worker.agents import insights, ranking
from worker.agents.inputs import AreaFacts

NOW = datetime(2026, 11, 14, 12, tzinfo=UTC)
SOURCES = {"nisar-damage": {"id": "nisar-damage", "acquired_at": "2026-07-21T00:00:00Z",
                            "last_success_at": "2026-11-14T00:00:00Z", "failure": ""},
           "firms": {"id": "firms", "last_success_at": "2026-11-14T11:00:00Z", "failure": ""}}


def facts(area, cand=0, corroborated=0, unknown=1, hit=None):
    return AreaFacts(area_id=area, buildings=10, residents_low=None, residents_high=None,
                     candidate_cells={"destroyed_or_severe_candidate": cand, "moderate_candidate": 0,
                                      "possible_candidate": 0},
                     corroborated_cells=corroborated, assessed_cells=4, unknown_cells=unknown,
                     facilities_mapped={"school": 1}, facilities_hit=hit or {}, run_id="run-a")


def build():
    fx = {"a": facts("a", 1, 1, hit={"school": 1}), "b": facts("b", 2), "c": facts("c")}
    alerts = [{"alert_id": "f1", "area_id": "b", "type": "fire_detected", "independent_source_count": 2,
               "detected_at": "2026-11-14T10:00:00Z", "review_status": "unreviewed"}]
    return insights.insights(ranking.rank(alerts, fx, SOURCES, now=NOW), fx, alerts, SOURCES)


def test_every_insight_is_sourced_and_numbers_come_from_values():
    for item in build():
        assert item["sources"] and item["text"]
        allowed = {str(v) for v in item["values"].values()}
        for number in re.findall(r"\d+", item["text"]):
            assert number in allowed, (number, item["text"])


def test_expected_sentences():
    texts = [i["text"] for i in build()]
    assert "A second radar agrees in 1 of 2 neighbourhoods with radar damage candidates." in texts
    assert any(t.startswith("1 fire detection in the latest feed; 1 in a neighbourhood") for t in texts)
    assert "People are unknown for every incident: the population estimate is not loaded yet." in texts
    assert "Power status is unknown: night-light data is not loaded." in texts
    assert any("could not assess 3 of 15 cells (20%)" in t for t in texts)


def test_no_banned_wording():
    text = json.dumps(build()).lower()
    assert "safe" not in text and "confirmed damage" not in text and "caused by" not in text
