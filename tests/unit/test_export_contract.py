"""Contract export tests on synthetic cells (no real locations or results)."""

import pytest

pytest.importorskip("h3")
pytest.importorskip("jsonschema")

import pandas as pd
from h3.api import basic_str as h3s

from pipelines.radar.nisar.export_contract import (
    area_metrics,
    load_spec,
    missing_intervals,
    validator,
)

CENTRE = h3s.latlng_to_cell(10.0, 10.0, 9)  # synthetic location, not a study area


def cells():
    ids = sorted(h3s.grid_disk(CENTRE, 6))
    df = pd.DataFrame({"h3_r9": ids, "sparse_cell": False, "low_coverage": False,
                       "damage_class": "no_detected_change", "evidence_label": "none"})
    df["h3_r8"] = [h3s.cell_to_parent(c, 8) for c in ids]
    df.loc[0, ["damage_class", "evidence_label"]] = ["moderate_candidate", "corroborated"]
    df.loc[1, ["damage_class", "evidence_label"]] = ["possible_candidate", "observed"]
    return df


def rows(df, with_s1=True):
    return area_metrics(df, metric_date="2026-07-18", acquired_at="2026-07-18T16:25:12Z",
                        processed_at="2026-11-14T06:00:00Z", run_id="testrun",
                        source_ids=["nisar-gcov-beta-151d72"], with_s1=with_s1, tag="a")


def test_every_row_matches_the_metricvalue_contract():
    v = validator(load_spec(), "MetricValue")
    out = rows(cells())
    assert out
    for r in out:
        v.validate(r)
        assert r["label"] in {"Observed", "Reported", "Corroborated", "Unknown"}
        assert r["low"] is None or r["low"] <= r["high"]


def test_only_resolution_8_areas_are_published():
    assert all(h3s.get_resolution(r["area_id"]) == 8 for r in rows(cells()))


def test_range_and_label_with_second_satellite():
    df = cells()
    area = df.loc[0, "h3_r8"]
    cand = next(r for r in rows(df) if r["area_id"] == area and r["metric"] == "radar_candidate_change_cells")
    n_cand = int(df[(df["h3_r8"] == area) & df["damage_class"].str.endswith("_candidate")].shape[0])
    assert cand["low"] == 1 and cand["high"] == n_cand and cand["label"] == "Corroborated"
    assert cand["release_at"] == "2026-07-21T16:25:12Z"


def test_unassessed_area_is_unknown_not_zero():
    df = cells()
    df["low_coverage"] = True
    for r in rows(df):
        assert r["low"] is None and r["high"] is None and r["label"] == "Unknown"


def test_missing_passes_grouped_into_intervals():
    out = missing_intervals(["2025-12-02", "2025-12-14", "2026-01-31", "2026-02-12", "2026-07-30"])
    assert [(i["start"], i["end"]) for i in out] == [
        ("2025-12-02", "2025-12-14"), ("2026-01-31", "2026-02-12"), ("2026-07-30", "2026-07-30")]
