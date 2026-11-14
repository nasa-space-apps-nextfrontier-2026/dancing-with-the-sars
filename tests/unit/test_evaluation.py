"""M1-03 evaluation tests on synthetic cells and events (no real locations)."""

import pytest

pytest.importorskip("sklearn")
pytest.importorskip("h3")

import numpy as np
import pandas as pd
from h3.api import basic_str as h3s

from pipelines.radar.nisar.evaluate import strike_context
from pipelines.radar.nisar.model import wilson

CENTRE = h3s.latlng_to_cell(10.0, 10.0, 9)  # synthetic location, not a study area


def cells_with_cluster():
    ids = sorted(h3s.grid_disk(CENTRE, 60))
    df = pd.DataFrame({"h3_r9": ids, "sparse_cell": False, "low_coverage": False,
                       "damage_class": "no_detected_change", "score": 0.1})
    near = set(h3s.grid_disk(CENTRE, 3))
    df.loc[df["h3_r9"].isin(near), ["damage_class", "score"]] = ["moderate_candidate", 0.9]
    return df


def test_strike_context_detects_enrichment():
    lat, lon = h3s.cell_to_latlng(CENTRE)
    out = strike_context(cells_with_cluster(), pd.DataFrame({"lat": [lat], "lon": [lon]}))
    assert out["near_lt_1km"]["rate"] > 0.5
    assert out["far_ge_5km"]["rate"] == 0
    assert out["top_cells_within_1km"]["20"] >= 0.8  # ring-3 cluster edge sits near 1 km


def test_unknown_and_sparse_cells_are_excluded():
    df = cells_with_cluster()
    df.loc[:9, "damage_class"] = "unknown"
    df.loc[10:19, "sparse_cell"] = True
    lat, lon = h3s.cell_to_latlng(CENTRE)
    out = strike_context(df, pd.DataFrame({"lat": [lat], "lon": [lon]}))
    assert out["n_cells"] == len(df) - 20


def test_wilson_interval_has_correct_denominator():
    lo, hi = wilson(1, 100)
    assert 0 < lo < 0.01 < hi < 0.06
    assert np.isnan(wilson(0, 0)[0])
