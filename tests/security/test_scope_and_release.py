"""M3-02 safety tests: area scopes, the 72-hour hold and scope enforcement on real requests.
Synthetic locations only (no study-area result is used)."""

import datetime as dt
import json

import h3
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.core.security import hash_password
from backend.app.main import app
from backend.app.policy.release import is_released
from backend.app.policy.scope import AOI_ID, area_in_scope

INSIDE_R8 = h3.latlng_to_cell(33.3, 35.5, 8)  # centre of the public demo box (docs/DATA_AND_API_PLAN.md)
INSIDE_R9 = h3.cell_to_children(INSIDE_R8, 9)[0]
OUTSIDE_R8 = h3.latlng_to_cell(10.0, 10.0, 8)


def test_aoi_scope_covers_cells_inside_the_box_only():
    assert area_in_scope(INSIDE_R8, (AOI_ID,))
    assert area_in_scope(INSIDE_R9, (AOI_ID,))
    assert not area_in_scope(OUTSIDE_R8, (AOI_ID,))


def test_cell_scope_covers_its_children_not_siblings_or_parents():
    sibling = next(c for c in h3.grid_disk(INSIDE_R8, 1) if c != INSIDE_R8)
    assert area_in_scope(INSIDE_R9, (INSIDE_R8,))
    assert not area_in_scope(h3.cell_to_children(sibling, 9)[0], (INSIDE_R8,))
    assert not area_in_scope(h3.cell_to_parent(INSIDE_R8, 7), (INSIDE_R8,))


def test_fixture_scope_is_exact_and_junk_is_denied():
    assert area_in_scope("demo-area-01", ("demo-area-01",))
    assert not area_in_scope("demo-area-02", ("demo-area-01",))
    assert not area_in_scope("../etc/passwd", (AOI_ID,))
    assert not area_in_scope(INSIDE_R8, ("*",))  # PR #21's wildcard scope was intentionally not imported


def test_release_hold_boundaries():
    now = dt.datetime(2026, 7, 21, 16, 25, 12, tzinfo=dt.UTC)
    assert is_released("2026-07-21T16:25:12+00:00", now)
    assert not is_released("2026-07-21T16:25:13+00:00", now)
    assert not is_released(None, now)
    with pytest.raises(ValueError):
        is_released(dt.datetime(2026, 7, 21), now)


@pytest.fixture
def client(monkeypatch):
    users = {"aoi-analyst": {"password_hash": hash_password("test-only-password"),
                             "role": "analyst", "area_scopes": [AOI_ID]}}
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", json.dumps(users))
    get_settings.cache_clear()
    with TestClient(app) as c:
        assert c.post("/api/v1/session", json={"username": "aoi-analyst",
                                               "password": "test-only-password"}).status_code == 200
        yield c
    get_settings.cache_clear()


def test_scoped_user_passes_for_inside_area_and_is_denied_outside(client):
    inside = client.get(f"/api/v1/areas/{INSIDE_R8}/summary")
    outside = client.get(f"/api/v1/areas/{OUTSIDE_R8}/summary")
    assert inside.status_code != 403
    assert outside.status_code == 403
    assert outside.json()["error"]["code"] == "FORBIDDEN"


def test_logged_out_user_is_rejected_before_scope():
    get_settings.cache_clear()
    with TestClient(app) as c:
        assert c.get(f"/api/v1/areas/{INSIDE_R8}/summary").status_code == 401
