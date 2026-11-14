"""M1-02 terrain mask tests on synthetic slopes (no real DEM)."""

import pytest

pytest.importorskip("h5py")
pytest.importorskip("rasterio")
pytest.importorskip("scipy")

import numpy as np

from pipelines.radar.nisar.terrain import classify_terrain

SHAPE = (50, 50)
PX = 20.0
# Sensor to the west, looking east-north-east down: line of sight (target to sensor) points west.
LX, LY = np.full(SHAPE, -0.64), np.zeros(SHAPE)
INC = np.full(SHAPE, 40.0)


def ramp_east(deg):
    """DEM rising to the east by `deg` degrees (faces west, toward the sensor)."""
    cols = np.arange(SHAPE[1]) * PX
    return np.tile(cols * np.tan(np.radians(deg)), (SHAPE[0], 1))


def test_flat_ground_is_kept():
    mask, _ = classify_terrain(np.zeros(SHAPE), LX, LY, INC, PX)
    assert not mask.any()


def test_slope_facing_sensor_beyond_incidence_is_layover():
    dem = -ramp_east(45)  # rises toward the west (toward the sensor) by 45 deg > 40 deg incidence
    _, stats = classify_terrain(dem, LX, LY, INC, PX)
    assert stats["layover"] > 0.9


def test_slope_facing_away_beyond_90_minus_incidence_is_shadow():
    dem = ramp_east(55)  # falls away from the sensor by 55 deg > 50 deg
    _, stats = classify_terrain(dem, LX, LY, INC, PX)
    assert stats["shadow"] > 0.9


def test_moderate_slope_is_kept_and_steep_slope_masked():
    kept, _ = classify_terrain(ramp_east(10), LX, LY, INC, PX)
    assert not kept[5:-5, 5:-5].any()
    steep, _ = classify_terrain(np.rot90(ramp_east(30)).copy(), LX, LY, INC, PX)
    assert steep[5:-5, 5:-5].all()
