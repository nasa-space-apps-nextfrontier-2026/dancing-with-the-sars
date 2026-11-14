"""U-04 building table on synthetic rows (doc 25: residents sum to the cell total; no building gets a
damage class its cell does not have). All values are made up for the test."""

import numpy as np
import pandas as pd

from pipelines.buildings import table


def frames():
    heights = pd.DataFrame({
        "building_id": ["a", "b", "c", "d", "e", "f"],
        "h3_r9": ["c1", "c1", "c1", "c2", "c3", "c4"],
        "h3_r8": ["p1"] * 6,
        "use": ["residential", "unknown", "school", "residential", "other", "residential"],
        "footprint_m2": [100.0, 300.0, 500.0, 200.0, 50.0, 80.0],
        "height_low_m": [3.0] * 6, "height_mid_m": [6.0] * 6, "height_high_m": [9.0] * 6,
        "height_source": ["ghsl"] * 6, "floors_low": [1, 1, 1, 1, 1, 1], "floors_high": [3, 3, 3, 3, 3, 3],
        "use_ghsl": ["residential", "residential", "non_residential", "residential", "residential", None],
    })
    base = heights[["building_id", "footprint_m2", "use"]].assign(
        facility_flag=lambda d: d["use"].eq("school"), osm_condition_tag=None)
    damage = pd.DataFrame({"h3_r9": ["c1", "c2", "c3"],
                           "damage_class": ["moderate_candidate", "no_detected_change", "unknown"],
                           "evidence_label": ["corroborated", "none", "unknown"],
                           "s1_agrees": [True, False, False], "run_id": ["run-a"] * 3})
    pop = pd.DataFrame({"cell_id": ["c1", "c2", "c3"], "pop_low": [101.0, 7.0, 12.0],
                        "pop_high": [150.0, 9.0, 20.0], "pop_year": [2020] * 3})
    return base, heights, damage, pop


def test_residents_sum_to_cell_totals():
    rows, people = table.build(*frames())
    r = rows.set_index("building_id")
    c1 = r.loc[["a", "b", "c"]]
    assert int(c1["residents_low"].sum()) == 101 and int(c1["residents_high"].sum()) == 150
    assert r.loc["c", "residents_low"] == 0                # a school holds no residents
    assert r.loc["b", "residents_low"] > r.loc["a", "residents_low"]  # GHSL-residential, bigger floor area
    assert (r.loc["d", "residents_low"], r.loc["d", "residents_high"]) == (7, 9)
    assert (rows["residents_low"].dropna() <= rows["residents_high"].dropna()).all()
    assert people["status"] == "loaded"


def test_people_left_unknown_not_zero():
    rows, people = table.build(*frames())
    r = rows.set_index("building_id")
    assert pd.isna(r.loc["e", "residents_low"])   # c3 has people but no residential building
    assert people["people_not_allocated_low"] == 12
    assert pd.isna(r.loc["f", "residents_low"])   # c4 has no population estimate
    base, heights, damage, _ = frames()
    rows, people = table.build(base, heights, damage, None)
    assert rows["residents_low"].isna().all() and people["status"] == "unavailable"


def test_damage_is_the_cell_result():
    rows, _ = table.build(*frames())
    cell_class = {"c1": "moderate_candidate", "c2": "no_detected_change", "c3": "unknown"}
    for _, row in rows.iterrows():
        assert row["damage_class"] == cell_class.get(row["h3_r9"], "not_assessed")
    r = rows.set_index("building_id")
    assert r.loc["a", "second_sensor_agrees"] and r.loc["a", "evidence_label"] == "corroborated"
    assert r.loc["f", "damage_class"] == "not_assessed" and r.loc["f", "evidence_label"] == "unknown"
    assert pd.isna(r.loc["d", "second_sensor_agrees"])  # not a candidate cell: does not apply


def test_spread_is_exact_and_proportional():
    out = table.spread(10, np.array([1.0, 1.0, 1.0]))
    assert out.sum() == 10 and sorted(out.tolist()) == [3, 3, 4]
    assert table.spread(5, np.array([0.0, 0.0])).tolist() == [0, 0]
    assert table.spread(100, np.array([3.0, 1.0])).tolist() == [75, 25]
