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


def test_areas_list_endpoint(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas')
    assert response.status_code == 200
    data = response.json()
    assert data["synthetic"] is True
    assert "items" in data
    assert "next_cursor" in data
    assert isinstance(data["items"], list)
    if data["items"]:
        item = data["items"][0]
        assert "area_id" in item
        assert "h3_id" in item
        assert "cadaster_code" in item
    get_settings.cache_clear()


def test_areas_pagination(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas?cursor=0')
    assert response.status_code == 200
    data = response.json()
    assert "next_cursor" in data
    if data["next_cursor"]:
        response2 = client.get(f'/api/v1/areas?cursor={data["next_cursor"]}')
        assert response2.status_code == 200
        data2 = response2.json()
        assert "items" in data2
    get_settings.cache_clear()


def test_area_summary_endpoint(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/demo-area-01/summary')
    assert response.status_code == 200
    data = response.json()
    assert data["synthetic"] is True
    assert data["area_id"] == "demo-area-01"
    assert "people" in data
    assert "services" in data
    assert "facilities" in data
    assert "hazards" in data
    get_settings.cache_clear()


def test_area_summary_unknown_area(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/unknown-area/summary')
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "FORBIDDEN"
    get_settings.cache_clear()


def test_area_values_endpoint(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/demo-area-01/values')
    assert response.status_code == 200
    data = response.json()
    assert data["synthetic"] is True
    assert "items" in data
    assert "next_cursor" in data
    assert isinstance(data["items"], list)
    if data["items"]:
        item = data["items"][0]
        assert "metric" in item
        assert "low" in item
        assert "high" in item
        assert "label" in item
        assert "source" in item
        assert "date" in item
        assert item["label"] in ["Observed", "Reported", "Corroborated", "Unknown"]
        assert item["low"] is not None or item["high"] is not None
    get_settings.cache_clear()


def test_area_values_metric_filter(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/demo-area-01/values?metric=residents_baseline')
    assert response.status_code == 200
    data = response.json()
    assert data["synthetic"] is True
    if data["items"]:
        for item in data["items"]:
            assert item["metric"] == "residents_baseline"
    get_settings.cache_clear()


def test_area_values_unknown_area(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/unknown-area/values')
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "FORBIDDEN"
    get_settings.cache_clear()


def test_values_no_bare_numbers(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/areas/demo-area-01/values')
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["label"] in ["Observed", "Reported", "Corroborated", "Unknown"], f"Invalid label: {item['label']}"
        assert item["low"] is not None or item["high"] is not None, "Both low and high are null"
        if item["low"] is not None and item["high"] is not None:
            assert item["low"] <= item["high"], f"low > high: {item['low']} > {item['high']}"
    get_settings.cache_clear()