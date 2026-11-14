"""Real-data radar endpoints (DEMO_SYNTHETIC=false) on a tiny synthetic data folder.

Covers roles, the 72-hour hold, file allow-listing and tile rendering. No database needed:
the database-backed damage and series routes are covered by the live smoke test in the PR.
"""

import json

import numpy as np
import pytest
import rasterio
from fastapi.testclient import TestClient
from rasterio.transform import from_origin

from backend.app.core.config import get_settings
from backend.app.core.security import hash_password
from backend.app.main import app
from backend.app.services import radar_real

PAST, FUTURE = "2026-07-21T16:25:12Z", "2999-01-01T00:00:00Z"


def layer(layer_id, release_at=PAST, min_role="analyst"):
    return {"synthetic": False, "layer_id": layer_id, "title": layer_id, "kind": "raster",
            "product": "NISAR GCOV", "analytical": True, "polarizations": ["HH"],
            "available_acquisitions": [], "missing_intervals": [],
            "default_comparison": {"before": "2026-01-19", "after": "2026-07-18"},
            "tile_url": f"/api/v1/layers/{layer_id}/tiles/{{z}}/{{x}}/{{y}}", "min_role": min_role,
            "source_ids": [], "label": "Observed", "date": "2026-07-18", "acquired_at": PAST,
            "processed_at": PAST, "release_at": release_at, "freshness": "Stale", "cached": True,
            "public_resolution": 8, "safety_tag": "restricted_until_review", "extent": None,
            "attribution": "test"}


@pytest.fixture
def data(tmp_path, monkeypatch):
    change = tmp_path / "private" / "nisar" / "change"
    change.mkdir(parents=True)
    arr = np.full((50, 50), -300, dtype="int16")  # -3 dB everywhere (synthetic, not real data)
    with rasterio.open(change / "change_A_HH.tif", "w", driver="GTiff", height=50, width=50, count=1,
                       dtype="int16", crs="EPSG:32636", transform=from_origin(700000, 3700000, 20, 20),
                       nodata=-32768) as dst:
        dst.write(arr, 1)
    outside = tmp_path / "elsewhere.tif"
    outside.write_bytes(b"not a raster")
    entries = [("change_A_HH", change / "change_A_HH.tif"), ("change_held_HH", change / "change_A_HH.tif"),
               ("change_officer_HH", change / "change_A_HH.tif"), ("change_escape_HH", outside)]
    (tmp_path / "manifests").mkdir()
    (tmp_path / "manifests" / "nisar_change_index.json").write_text(json.dumps({"layers": [
        {"name": n, "kind": "change", "path": str(p)} for n, p in entries]}))
    (tmp_path / "local" / "radar_contract").mkdir(parents=True)
    (tmp_path / "local" / "radar_contract" / "layers.json").write_text(json.dumps([
        layer("nisar-change-a-hh"), layer("nisar-change-held-hh", release_at=FUTURE),
        layer("nisar-change-officer-hh", min_role="officer"), layer("nisar-change-escape-hh")]))
    users = {r: {"password_hash": hash_password("test-only-password"), "role": r,
                 "area_scopes": ["south-lebanon-demo"]} for r in ("analyst", "admin")}
    monkeypatch.setenv("DEMO_SYNTHETIC", "false")
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", json.dumps(users))
    get_settings.cache_clear()
    radar_real._catalogue.cache_clear()
    yield tmp_path
    get_settings.cache_clear()
    radar_real._catalogue.cache_clear()


def signed_in(role):
    c = TestClient(app)
    assert c.post("/api/v1/session", json={"username": role, "password": "test-only-password"}).status_code == 200
    return c


def test_logged_out_sees_no_layers_and_no_tiles(data):
    c = TestClient(app)
    assert c.get("/api/v1/layers").json()["items"] == []
    assert c.get("/api/v1/layers/nisar-change-a-hh/tiles/10/612/411").status_code == 401


def test_analyst_sees_released_layers_for_their_role_only(data):
    ids = {x["layer_id"] for x in signed_in("analyst").get("/api/v1/layers").json()["items"]}
    assert "nisar-change-a-hh" in ids
    assert "nisar-change-held-hh" not in ids  # 72-hour hold
    assert "nisar-change-officer-hh" not in ids  # role above analyst


def test_admin_can_review_held_layer(data):
    assert signed_in("admin").get("/api/v1/layers/nisar-change-held-hh").status_code == 200


def test_tile_renders_png_inside_and_404_outside(data):
    c = signed_in("analyst")
    # z15 tile containing the synthetic raster (UTM 36N, around 700 km E / 3700 km N)
    from pyproj import Transformer
    lon, lat = Transformer.from_crs(32636, 4326, always_xy=True).transform(700500, 3699500)
    import math
    n = 2 ** 15
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    r = c.get(f"/api/v1/layers/nisar-change-a-hh/tiles/15/{x}/{y}")
    assert r.status_code == 200 and r.headers["content-type"] == "image/png" and r.content[:4] == b"\x89PNG"
    assert c.get("/api/v1/layers/nisar-change-a-hh/tiles/15/0/0").status_code == 404
    assert c.get("/api/v1/layers/nisar-change-a-hh/tiles/15/x/0").status_code == 422


def test_held_and_escaping_files_are_never_served(data):
    c = signed_in("analyst")
    assert c.get("/api/v1/layers/nisar-change-held-hh/tiles/10/612/411").status_code == 404
    assert c.get("/api/v1/layers/nisar-change-escape-hh/tiles/10/612/411").status_code == 404


def test_series_requires_area_and_valid_dates(data):
    c = signed_in("analyst")
    assert c.get("/api/v1/layers/nisar-change-a-hh/timeseries").status_code == 422
    r = c.get("/api/v1/layers/nisar-change-a-hh/timeseries?area_id=x&from=yesterday")
    assert r.status_code in (403, 422)
