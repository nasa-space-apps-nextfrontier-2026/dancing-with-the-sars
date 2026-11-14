"""U-03 calibration on synthetic numbers: band table, held-out scoring by area, honest scores."""

import numpy as np
import pandas as pd
import pytest

from pipelines.buildings import height_check as hc


def refs(n=200, seed=1):
    rng = np.random.default_rng(seed)
    ghsl = rng.choice([2.5, 3.5, 5.0, 7.5, 11.0, 20.0], n)
    ref = np.clip(np.round(ghsl / 3 + rng.normal(0, 0.7, n)) * 3, 3, None)  # levels x 3 m
    return pd.DataFrame({"ghsl_height_m": ghsl, "footprint_m2": rng.uniform(50, 500, n), "ref_m": ref,
                         "osm_levels": ref / 3, "h3_r8": [f"area-{i % 20}" for i in range(n)]})


def test_table_covers_bands_and_ranges_are_ordered():
    table = hc.fit(refs(), 0.15, 0.85, use_footprint=False)
    assert {t["ghsl_from_m"] for t in table} == {0.0, 2.5, 4.0, 6.0, 9.0, 13.0}
    for t in table:
        assert hc.STOREY_M <= t["low_m"] <= t["mid_m"] <= t["high_m"] and t["n"] > 0


def test_predict_uses_the_right_band():
    table = [{"ghsl_from_m": 0.0, "ghsl_to_m": 2.5, "footprint_from_m2": 0.0, "footprint_to_m2": 1e12,
              "n": 20, "mid_m": 6.0, "low_m": 3.0, "high_m": 9.0},
             {"ghsl_from_m": 2.5, "ghsl_to_m": 1000.0, "footprint_from_m2": 0.0, "footprint_to_m2": 1e12,
              "n": 20, "mid_m": 12.0, "low_m": 6.0, "high_m": 18.0}]
    out = hc.predict(table, np.array([2.5, 2.6, 30.0]), np.array([100.0, 100.0, 100.0]))
    assert out[0].tolist() == [6.0, 3.0, 9.0] and out[1].tolist() == [12.0, 6.0, 18.0]
    assert out[2].tolist() == [12.0, 6.0, 18.0]


def test_held_out_folds_are_whole_areas():
    df = refs()
    cv = hc.cross_validate(df, 0.15, 0.85, False)
    assert cv["mid"].notna().all()
    folds = df.groupby("h3_r8")["h3_r8"].first().map(hc.fold_of)
    assert folds.groupby(level=0).nunique().max() == 1  # one fold per area
    assert hc.fold_of("area-1") == hc.fold_of("area-1")


def test_scores_are_plain():
    s = hc.scores(np.array([3.0, 6.0, 30.0]), np.array([3.0, 9.5, 12.0]), np.array([3.0, 3.0, 6.0]),
                  np.array([6.0, 9.0, 18.0]))
    assert s["within_one_storey"] == pytest.approx(1 / 3, abs=1e-3)
    assert s["range_holds_reference"] == pytest.approx(2 / 3, abs=1e-3)
    assert s["bias_m"] < 0  # the tower is underestimated
