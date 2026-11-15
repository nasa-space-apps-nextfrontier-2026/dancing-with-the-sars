import json

import h3
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from backend.app.core.config import get_settings
from backend.app.core.security import Identity, hash_password
from backend.app.main import app
from backend.app.services import map_context_real

AREA = h3.latlng_to_cell(33.3, 35.5, 8)
CELL = h3.latlng_to_cell(33.3, 35.5, 9)


def _empty_bundle() -> dict:
    return {
        "synthetic": False,
        "generated_at": "",
        "incidents": {"synthetic": False, "generated_at": "", "weights": {}, "data_age": {}, "items": [], "next_cursor": None},
        "incident_details": {},
        "layers": {"synthetic": False, "items": [], "next_cursor": None},
        "damage": {},
        "alerts": {"synthetic": False, "items": [], "next_cursor": None},
        "people": {},
        "budgets": {},
        "centroids": {},
        "unavailable": {},
    }


def test_map_context_requires_authentication(monkeypatch):
    monkeypatch.setenv("DEMO_SYNTHETIC", "false")
    get_settings.cache_clear()
    with TestClient(app) as client:
        assert client.get("/api/v1/map/context").status_code == 401
    get_settings.cache_clear()


def test_map_context_dispatches_for_scoped_identity(monkeypatch):
    users = {"analyst": {"password_hash": hash_password("test-only-password"), "role": "analyst", "area_scopes": [AREA]}}
    monkeypatch.setenv("DEMO_SYNTHETIC", "false")
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", json.dumps(users))
    get_settings.cache_clear()


def test_map_context_database_failure_is_503(monkeypatch):
    users = {"analyst": {"password_hash": hash_password("test-only-password"), "role": "analyst", "area_scopes": [AREA]}}
    monkeypatch.setenv("DEMO_SYNTHETIC", "false")
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", json.dumps(users))
    get_settings.cache_clear()

    def fail(*_args):
        raise OperationalError("SELECT", {}, RuntimeError("offline"))

    monkeypatch.setattr(map_context_real, "build", fail)
    with TestClient(app) as client:
        assert client.post("/api/v1/session", json={"username": "analyst", "password": "test-only-password"}).status_code == 200
        response = client.get("/api/v1/map/context")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "UNAVAILABLE"
    get_settings.cache_clear()
    seen = {}

    def build(engine, identity, area_id, limit):
        seen.update(identity=identity, area_id=area_id, limit=limit)
        return _empty_bundle()

    monkeypatch.setattr(map_context_real, "build", build)
    with TestClient(app) as client:
        assert client.post("/api/v1/session", json={"username": "analyst", "password": "test-only-password"}).status_code == 200
        response = client.get(f"/api/v1/map/context?area_id={AREA}&limit=25")
    assert response.status_code == 200
    assert response.json()["synthetic"] is False
    assert seen == {"identity": Identity("analyst", "analyst", (AREA,)), "area_id": AREA, "limit": 25}
    get_settings.cache_clear()


def test_bundle_uses_h3_centres_and_reports_missing_domains(monkeypatch):
    incident = {"incident_id": "i1", "area_id": AREA}
    monkeypatch.setattr(map_context_real.agents_real, "list_incidents", lambda *_args: {
        "synthetic": False, "generated_at": "2026-11-15T00:00:00Z", "weights": {}, "data_age": {}, "items": [incident], "next_cursor": None,
    })
    monkeypatch.setattr(map_context_real.agents_real, "get_incident", lambda *_args: None)
    monkeypatch.setattr(map_context_real.agents_real, "area_budget", lambda *_args: None)
    monkeypatch.setattr(map_context_real.radar_real, "list_layers", lambda *_args: [])
    monkeypatch.setattr(map_context_real.radar_real, "damage", lambda *_args: {
        "synthetic": False, "items": [{"area_id": CELL}], "next_cursor": None,
    })
    monkeypatch.setattr(map_context_real.live_real, "list_alerts", lambda *_args, **_kwargs: {
        "synthetic": False, "items": [], "next_cursor": None,
    })
    monkeypatch.setattr(map_context_real.areas_real, "people", lambda *_args: (_ for _ in ()).throw(map_context_real.summary_real.Unavailable()))
    monkeypatch.setattr(map_context_real.facilities_real, "loaded", lambda *_args: False)
    monkeypatch.setattr(map_context_real, "_night_lights_loaded", lambda *_args: False)

    result = map_context_real.build(object(), Identity("u", "analyst", (AREA,)), None, 10)

    assert set(result["centroids"]) == {AREA, CELL}
    assert result["unavailable"]["routes"].startswith("Validated")
    assert result["unavailable"]["facilities"].startswith("Validated")
    assert "Unknown, not zero" in result["unavailable"]["night_lights"]
    monkeypatch.setattr(map_context_real.facilities_real, "loaded", lambda *_args: True)
    monkeypatch.setattr(map_context_real, "_night_lights_loaded", lambda *_args: True)
    loaded = map_context_real.build(object(), Identity("u", "analyst", (AREA,)), None, 10)
    # facility points are never in the bundle, so the map still reports them as unavailable
    assert "not on this map" in loaded["unavailable"]["facilities"]
    assert "night_lights" not in loaded["unavailable"]
    assert result["unavailable"][f"people:{AREA}"] == "Population evidence is not loaded."
    assert result["synthetic"] is False
