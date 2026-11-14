"""Sentinel-1 cross-check helper tests (synthetic values only)."""

import pytest

pytest.importorskip("rasterio")
pytest.importorskip("h3")
pytest.importorskip("sklearn")

import numpy as np
import pandas as pd

from pipelines.radar.nisar.s1_check import AGREE_Z, NAME, robust_z


def test_robust_z_flags_strong_drops_only():
    rng = np.random.default_rng(0)
    v = pd.Series(np.concatenate([rng.normal(0, 0.5, 1000), [-6.0, -5.0]]))
    z = robust_z(v)
    assert (z.iloc[-2:] <= AGREE_Z).all()
    assert (z.iloc[:1000] <= AGREE_Z).mean() < 0.05


def test_granule_name_parsing():
    m = NAME.match("OPERA_L2_RTC-S1_T021-044123-IW2_20260625T034512Z_20260626T120000Z_S1C_30_v1.0")
    assert m and m.group(1) == "021" and m.group(4) == "20260625"
