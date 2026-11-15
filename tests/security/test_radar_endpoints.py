"""Real-data radar endpoints (DEMO_SYNTHETIC=false) on a tiny synthetic data folder.

Covers roles, the 72-hour hold, file allow-listing and tile rendering. No database needed:
the database-backed damage and series routes are covered by the live smoke test in the PR.
"""

import json
from types import SimpleNamespace

import numpy as np
import pytest
import rasterio
from fastapi.testclient import TestClient
from rasterio.transform import from_origin

from backend.app.core.config import get_settings
from backend.app.core.security import Identity, hash_password
from backend.app.main import app
from backend.app.services import radar_real

PAST, FUTURE = "2026-07-21T16:25:12Z", "2999-01-01T00:00:00Z"


def layer(layer_id, release_at=PAST, min_role="analyst"):
    return {
        "synthetic": False,
        "layer_id": layer_id,
        "title": layer_id,
        "kind": "raster",
        "product": "NISAR GCOV",
        "analytical": True,
        "polarizations": ["HH"],
        "available_acquisitions": [],
        "missing_intervals": [],
        "default_comparison": {"before": "2026-01-19", "after": "2026-07-18"},
        "tile_url": f"/api/v1/layers/{layer_id}/tiles/{{z}}/{{x}}/{{y}}",
        "min_role": min_role,
        "source_ids": [],
        "label": "Observed",
        "date": "2026-07-18",
        "acquired_at": PAST,
        "processed_at": PAST,
        "release_at": release_at,
        "freshness": "Stale",
        "cached": True,
        "public_resolution": 8,
        "safety_tag": "restricted_until_review",
        "extent": None,
        "attribution": "test",
    }


@pytest.fixture
def data(tmp_path, monkeypatch):
    change = tmp_path / "private" / "nisar" / "change"
    change.mkdir(parents=True)
    arr = np.full(
        (50, 50), -300, dtype="int16"
    )  # -3 dB everywhere (synthetic, not real data)
    with rasterio.open(
        change / "change_A_HH.tif",
        "w",
        driver="GTiff",
        height=50,
        width=50,
        count=1,
        dtype="int16",
        crs="EPSG:32636",
        transform=from_origin(700000, 3700000, 20, 20),
        nodata=-32768,
    ) as dst:
        dst.write(arr, 1)
    outside = tmp_path / "elsewhere.tif"
    outside.write_bytes(b"not a raster")
    entries = [
        ("change_A_HH", change / "change_A_HH.tif"),
        ("change_held_HH", change / "change_A_HH.tif"),
        ("change_officer_HH", change / "change_A_HH.tif"),
        ("change_escape_HH", outside),
    ]
    (tmp_path / "manifests").mkdir()
    (tmp_path / "manifests" / "nisar_change_index.json").write_text(
        json.dumps(
            {
                "layers": [
                    {"name": n, "kind": "change", "path": str(p)} for n, p in entries
                ]
            }
        )
    )
    (tmp_path / "local" / "radar_contract").mkdir(parents=True)
    (tmp_path / "local" / "radar_contract" / "layers.json").write_text(
        json.dumps(
            [
                layer("nisar-change-a-hh"),
                layer("nisar-change-held-hh", release_at=FUTURE),
                layer("nisar-change-officer-hh", min_role="officer"),
                layer("nisar-change-escape-hh"),
            ]
        )
    )
    users = {
        r: {
            "password_hash": hash_password("test-only-password"),
            "role": r,
            "area_scopes": ["south-lebanon-demo"],
        }
        for r in ("analyst", "admin")
    }
    users["cell-analyst"] = {
        "password_hash": hash_password("test-only-password"),
        "role": "analyst",
        "area_scopes": ["882db188e3fffff"],
    }
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
    assert (
        c.post(
            "/api/v1/session", json={"username": role, "password": "test-only-password"}
        ).status_code
        == 200
    )
    return c


def test_logged_out_sees_no_layers_and_no_tiles(data):
    c = TestClient(app)
    assert c.get("/api/v1/layers").json()["items"] == []
    assert c.get("/api/v1/layers/nisar-change-a-hh/tiles/10/612/411").status_code == 401


def test_analyst_sees_released_layers_for_their_role_only(data):
    ids = {
        x["layer_id"]
        for x in signed_in("analyst").get("/api/v1/layers").json()["items"]
    }
    assert "nisar-change-a-hh" in ids
    assert "nisar-change-held-hh" not in ids  # 72-hour hold
    assert "nisar-change-officer-hh" not in ids  # role above analyst


def test_admin_does_not_bypass_the_hold(
    data,
):  # doc 07: admin is not a bypass for publication delay
    assert (
        signed_in("admin").get("/api/v1/layers/nisar-change-held-hh").status_code == 404
    )


def test_tile_renders_png_inside_and_404_outside(data):
    c = signed_in("analyst")
    # z15 tile containing the synthetic raster (UTM 36N, around 700 km E / 3700 km N)
    from pyproj import Transformer

    lon, lat = Transformer.from_crs(32636, 4326, always_xy=True).transform(
        700500, 3699500
    )
    import math

    n = 2**15
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    r = c.get(f"/api/v1/layers/nisar-change-a-hh/tiles/15/{x}/{y}")
    assert (
        r.status_code == 200
        and r.headers["content-type"] == "image/png"
        and r.content[:4] == b"\x89PNG"
    )
    assert c.get("/api/v1/layers/nisar-change-a-hh/tiles/15/0/0").status_code == 404
    assert c.get("/api/v1/layers/nisar-change-a-hh/tiles/15/x/0").status_code == 422


def test_held_and_escaping_files_are_never_served(data):
    c = signed_in("analyst")
    assert (
        c.get("/api/v1/layers/nisar-change-held-hh/tiles/10/612/411").status_code == 404
    )
    assert (
        c.get("/api/v1/layers/nisar-change-escape-hh/tiles/10/612/411").status_code
        == 404
    )


def test_manifest_file_download_is_exact_scoped_and_range_capable(data):
    c = signed_in("analyst")
    url = "/api/v1/layers/nisar-change-a-hh/files/change_A_HH.tif"
    complete = c.get(url)
    assert complete.status_code == 200
    assert complete.headers["content-type"] == "application/octet-stream"
    partial = c.get(url, headers={"Range": "bytes=0-3"})
    assert partial.status_code == 206 and len(partial.content) == 4
    assert partial.headers["content-range"].startswith("bytes 0-3/")
    assert (
        c.get("/api/v1/layers/nisar-change-a-hh/files/elsewhere.tif").status_code == 404
    )
    assert (
        c.get("/api/v1/layers/nisar-change-held-hh/files/change_A_HH.tif").status_code
        == 404
    )
    # A cell-scoped analyst cannot download a full-AOI artifact.
    assert signed_in("cell-analyst").get(url).status_code == 404


def test_catalogue_paths_follow_custom_data_root(data):
    index_path = data / "manifests" / "nisar_change_index.json"
    payload = json.loads(index_path.read_text())
    for entry in payload["layers"]:
        entry["path"] = (
            "data/private/nisar/change/"
            + entry["name"]
            .replace("change_held_HH", "change_A_HH")
            .replace("change_officer_HH", "change_A_HH")
            .replace("change_escape_HH", "change_A_HH")
            + ".tif"
        )
    index_path.write_text(json.dumps(payload))
    radar_real._catalogue.cache_clear()
    assert (
        signed_in("analyst")
        .get("/api/v1/layers/nisar-change-a-hh/files/change_A_HH.tif")
        .status_code
        == 200
    )


def test_series_requires_area_and_valid_dates(data):
    c = signed_in("analyst")
    assert c.get("/api/v1/layers/nisar-change-a-hh/timeseries").status_code == 422
    r = c.get("/api/v1/layers/nisar-change-a-hh/timeseries?area_id=x&from=yesterday")
    assert r.status_code in (403, 422)


def test_damage_selects_latest_released_area_artifact_and_queries_by_artifact_id():
    calls = []

    class Engine:
        def connect(self):
            class Ctx:
                def __enter__(self):
                    class Conn:
                        def execute(self, sql, params=None):
                            calls.append((str(sql), params or {}))
                            if len(calls) == 1:
                                # The database eligibility predicate excludes a newer held
                                # artifact and selects this older released one.
                                row = SimpleNamespace(id="artifact-released", run_id="shared-run")
                                return SimpleNamespace(first=lambda: row)
                            rows = [
                                SimpleNamespace(
                                    area_id="cell-from-released-artifact",
                                    classification="candidate_change",
                                    anomaly_score=0.7,
                                    reason_codes=["level:possible_candidate"],
                                    run_id="shared-run",
                                    release_at=PAST,
                                )
                            ] if params["artifact"] == "artifact-released" else []
                            return SimpleNamespace(all=lambda: rows)

                    return Conn()

                def __exit__(self, *args):
                    return False

            return Ctx()

    result = radar_real.damage(
        Engine(),
        "area-requested",
        "A",
        Identity("analyst", "analyst", ("south-lebanon-demo",)),
    )
    assert [item["area_id"] for item in result["items"]] == [
        "cell-from-released-artifact"
    ]
    assert "requested.parent_id" in calls[0][0]
    assert "visible.release_at IS NOT NULL" in calls[0][0]
    assert "visible.release_at <= :now" in calls[0][0]
    assert calls[0][1]["area"] == "area-requested"
    assert calls[1][1] == {
        "artifact": "artifact-released",
        "area": "area-requested",
    }
    assert "r.artifact_id = :artifact" in calls[1][0]
    assert "a.run_id = :run" not in calls[1][0]


def test_damage_does_not_mix_duplicate_run_ids_across_artifacts():
    class Engine:
        def connect(self):
            class Context:
                def __enter__(self):
                    class Connection:
                        def execute(self, sql, params=None):
                            if "SELECT a.id, a.run_id" in str(sql):
                                return SimpleNamespace(
                                    first=lambda: SimpleNamespace(
                                        id="artifact-for-area", run_id="duplicate-run"
                                    )
                                )
                            assert params["artifact"] == "artifact-for-area"
                            return SimpleNamespace(
                                all=lambda: [
                                    SimpleNamespace(
                                        area_id="only-selected-artifact",
                                        classification="candidate_change",
                                        anomaly_score=0.5,
                                        reason_codes=[],
                                        run_id="duplicate-run",
                                        release_at=PAST,
                                    )
                                ]
                            )

                    return Connection()

                def __exit__(self, *args):
                    return False

            return Context()

    result = radar_real.damage(
        Engine(),
        "area-requested",
        "A",
        Identity("analyst", "analyst", ("south-lebanon-demo",)),
    )
    assert [item["area_id"] for item in result["items"]] == ["only-selected-artifact"]
