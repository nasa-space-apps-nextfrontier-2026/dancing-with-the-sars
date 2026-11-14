"""M1-02 anomaly model tests on synthetic cells (no war-zone geometry, no real scenes)."""

import pytest

pytest.importorskip("sklearn")
pytest.importorskip("h3")

import numpy as np
import pandas as pd
from h3.api import basic_str as h3s

from pipelines.radar.nisar.model import fit_and_score, holdout_false_alarms, quiet_cells

CENTRE = h3s.latlng_to_cell(10.0, 10.0, 9)  # synthetic location, not a real study area


def synthetic_cells(n_damaged=60, n_other=20, seed=0):
    rng = np.random.default_rng(seed)
    ids = sorted(h3s.grid_disk(CENTRE, 40))
    n = len(ids)
    df = pd.DataFrame({
        "h3_r9": ids,
        "d_hh": rng.normal(-0.4, 0.5, n),  # small "season" shift everywhere
        "d_hv": rng.normal(-0.2, 0.5, n),
        "d_pol": rng.normal(-0.2, 0.4, n),
        "strong_drop_share": rng.beta(1, 40, n),
        "built_density": rng.uniform(0.1, 0.8, n),
        "n_valid_px": 200, "n_built_px": 220, "low_coverage": False,
    })
    dmg = rng.choice(n, n_damaged + n_other, replace=False)
    d, o = dmg[:n_damaged], dmg[n_damaged:]
    df.loc[d, ["d_hh", "d_hv", "d_pol", "strong_drop_share"]] = [-6.0, 1.5, -7.0, 0.6]
    df.loc[o, ["d_hh", "d_hv", "d_pol", "strong_drop_share"]] = [5.0, 3.0, 2.0, 0.0]
    df["truth"] = "normal"
    df.loc[d, "truth"] = "damage"
    df.loc[o, "truth"] = "other"
    return df


def test_damage_flagged_and_other_change_separated():
    cells = synthetic_cells()
    quiet = (cells["truth"] == "normal").to_numpy()
    out, fit = fit_and_score(cells, quiet, seed=1)
    dmg = out[out["truth"] == "damage"]["damage_class"]
    assert dmg.str.endswith("_candidate").mean() > 0.95
    oth = out[out["truth"] == "other"]["damage_class"]
    assert (oth == "other_change").mean() > 0.95
    assert fit.n_train > 1000


def test_holdout_false_alarm_near_design_rate():
    cells = synthetic_cells(n_damaged=0, n_other=0)
    quiet = np.ones(len(cells), dtype=bool)
    out, fit = fit_and_score(cells, quiet, seed=3)
    fa = holdout_false_alarms(out, fit)
    assert fa["n"] > 300
    assert fa["moderate"]["observed"] < 0.04
    assert fa["possible"]["observed"] < 0.12


def test_train_and_holdout_blocks_do_not_overlap():
    cells = synthetic_cells()
    _out, fit = fit_and_score(cells, np.ones(len(cells), dtype=bool), seed=5)
    assert not set(fit.train_blocks) & set(fit.holdout_blocks)


def test_low_coverage_is_unknown_not_no_damage():
    cells = synthetic_cells()
    cells.loc[:9, "low_coverage"] = True
    cells.loc[10:19, "d_hh"] = np.nan
    out, _ = fit_and_score(cells, np.ones(len(cells), dtype=bool), seed=1)
    assert (out.loc[:19, "damage_class"] == "unknown").all()


def test_reproducible_with_seed():
    cells = synthetic_cells()
    q = np.ones(len(cells), dtype=bool)
    a, _ = fit_and_score(cells, q, seed=7)
    b, _ = fit_and_score(cells, q, seed=7)
    pd.testing.assert_series_equal(a["damage_class"], b["damage_class"])


def test_small_training_set_marks_tail_unreliable():
    cells = synthetic_cells().iloc[:800].reset_index(drop=True)
    out, fit = fit_and_score(cells, np.ones(len(cells), dtype=bool), seed=1)
    assert not fit.tail_reliable
    assert "higher" not in set(out["confidence"].dropna())


def test_zscore_fallback_same_output_format():
    cells = synthetic_cells()
    quiet = (cells["truth"] == "normal").to_numpy()
    out, fit = fit_and_score(cells, quiet, seed=1, method="zscore")
    assert fit.method == "zscore"
    assert {"damage_class", "confidence", "reasons", "score"} <= set(out.columns)


def test_quiet_cells_excludes_near_events():
    cells = synthetic_cells()
    lat, lon = h3s.cell_to_latlng(CENTRE)
    q = quiet_cells(cells, pd.DataFrame({"lat": [lat], "lon": [lon]}), radius_km=2.0)
    assert not q[cells["h3_r9"] == CENTRE][0]
    assert 0.5 < q.mean() < 1.0


def test_too_few_quiet_cells_raises():
    cells = synthetic_cells()
    quiet = np.zeros(len(cells), dtype=bool)
    with pytest.raises(ValueError):
        fit_and_score(cells, quiet)
