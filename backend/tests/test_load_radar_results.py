"""Loader tests. Pure mapping tests always run; the database round trip runs only when
CIVISAR_TEST_DATABASE_URL points at a disposable PostGIS with migrations applied."""

import os

import pytest
from scripts.load_radar_results import CLASS_MAP, classify, stable_id


def test_candidate_levels_map_to_allowed_classes_and_keep_level():
    r = classify({"damage_class": "moderate_candidate", "reasons": "strong_hh_drop|hv_shift",
                  "score": 0.7, "evidence_label": "observed"})
    assert r["classification"] == "candidate_change"
    assert r["reason_codes"][0] == "level:moderate_candidate"
    assert r["evidence_label"] == "Observed"


def test_corroborated_only_when_second_satellite_agrees():
    r = classify({"damage_class": "possible_candidate", "reasons": "", "score": 0.6,
                  "evidence_label": "corroborated"})
    assert r["evidence_label"] == "Corroborated"


def test_unknown_has_no_score_and_no_change_is_not_stored():
    u = classify({"damage_class": "unknown", "reasons": "low_coverage", "score": 0.4})
    assert u["classification"] == "Unknown" and u["anomaly_score"] is None
    assert u["evidence_label"] == "Unknown"
    assert classify({"damage_class": "no_detected_change", "reasons": "", "score": 0.1}) is None


def test_only_schema_allowed_classifications():
    assert set(CLASS_MAP.values()) <= {"Unknown", "candidate_change", "other_change"}


def test_ids_are_stable():
    assert stable_id("a", "b") == stable_id("a", "b") != stable_id("a", "c")


def test_cell_polygon_is_closed():
    pytest.importorskip("h3")
    from h3.api import basic_str as h3s
    from scripts.load_radar_results import cell_polygon_wkt

    wkt = cell_polygon_wkt(h3s.latlng_to_cell(10.0, 10.0, 9))  # synthetic location
    pts = wkt[len("POLYGON(("):-2].split(", ")
    assert wkt.startswith("POLYGON((") and pts[0] == pts[-1] and len(pts) == 7


@pytest.mark.skipif(not os.environ.get("CIVISAR_TEST_DATABASE_URL"),
                    reason="needs a disposable PostGIS (CIVISAR_TEST_DATABASE_URL)")
def test_database_constraints_reject_bad_rows():
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import IntegrityError

    eng = create_engine(os.environ["CIVISAR_TEST_DATABASE_URL"])
    with pytest.raises(IntegrityError), eng.begin() as conn:
        conn.execute(text("INSERT INTO metric_values (id, area_id, run_id, metric, low, high, unit, "
                          "label, source_id, safety_tag) VALUES ('t', 'missing-area', 'missing-run', "
                          "'m', 2, 1, 'u', 'Observed', 'missing-source', 'x')"))
