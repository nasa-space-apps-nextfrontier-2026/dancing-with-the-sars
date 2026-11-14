import json

from backend.app.core.config import get_settings
from backend.app.core.security import hash_password
from backend.app.main import app
from fastapi.testclient import TestClient


def _login_client(monkeypatch):
    users = {'test-analyst': {'password_hash': hash_password('test-only-password'), 'role': 'analyst', 'area_scopes': ['demo-area-01']}}
    monkeypatch.setenv('CIVISAR_DEMO_USERS_JSON', json.dumps(users))
    get_settings.cache_clear()
    client = TestClient(app)
    response = client.post('/api/v1/session', json={'username': 'test-analyst', 'password': 'test-only-password'})
    assert response.status_code == 200
    return client


def test_people_endpoint(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/demo-area-01/people')
    assert response.status_code == 200
    data = response.json()
    assert data["synthetic"] is True
    assert "items" in data
    assert isinstance(data["items"], list)
    if data["items"]:
        item = data["items"][0]
        assert "low" in item
        assert "high" in item
        assert item["label"] in ["Observed", "Reported", "Corroborated", "Unknown"]
        if item["low"] is not None and item["high"] is not None:
            assert item["low"] <= item["high"], f"low > high: {item['low']} > {item['high']}"
    get_settings.cache_clear()


def test_people_unknown_area(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/unknown-area/people')
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "FORBIDDEN"
    get_settings.cache_clear()


def test_services_endpoint(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/demo-area-01/services')
    assert response.status_code == 200
    data = response.json()
    assert data["synthetic"] is True
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 0
    assert data.get("message") == "No service-loss data yet"
    get_settings.cache_clear()


def test_services_unknown_area(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/unknown-area/services')
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "FORBIDDEN"
    get_settings.cache_clear()


def test_facilities_endpoint(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/demo-area-01/facilities')
    assert response.status_code == 200
    data = response.json()
    assert data["synthetic"] is True
    assert "items" in data
    assert "next_cursor" in data
    assert isinstance(data["items"], list)
    if data["items"]:
        item = data["items"][0]
        assert "facility_id" in item
        assert "type" in item
        assert "operating_status" in item
        assert "damage_status" in item
        assert "label" in item
        assert "source" in item
        assert "date" in item
        assert "geometry" in item
        assert item["label"] == "Unknown"
        assert item["operating_status"] == "Unknown"
    get_settings.cache_clear()


def test_facilities_type_filter(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/demo-area-01/facilities?type=clinic')
    assert response.status_code == 200
    data = response.json()
    assert data["synthetic"] is True
    if data["items"]:
        for item in data["items"]:
            assert item["type"].lower() == "clinic"
    get_settings.cache_clear()


def test_facilities_pagination(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/demo-area-01/facilities?cursor=0')
    assert response.status_code == 200
    data = response.json()
    assert "next_cursor" in data
    if data["next_cursor"]:
        response2 = client.get(f'/api/v1/areas/demo-area-01/facilities?cursor={data["next_cursor"]}')
        assert response2.status_code == 200
        data2 = response2.json()
        assert "items" in data2
    get_settings.cache_clear()


def test_facilities_unknown_area(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/unknown-area/facilities')
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "FORBIDDEN"
    get_settings.cache_clear()


def test_no_sensitive_facilities(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/demo-area-01/facilities')
    assert response.status_code == 200
    data = response.json()
    forbidden_types = ["military", "police", "prison"]
    for item in data["items"]:
        f_type = item.get("type", "").lower()
        for forbidden in forbidden_types:
            assert forbidden not in f_type, f"Sensitive facility type '{forbidden}' found in {item}"
    get_settings.cache_clear()


def test_people_always_range(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/demo-area-01/people')
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["low"] is not None or item["high"] is not None, "Both low and high are null"
        if item["low"] is not None and item["high"] is not None:
            assert item["low"] <= item["high"], f"low > high: {item['low']} > {item['high']}"
    get_settings.cache_clear()