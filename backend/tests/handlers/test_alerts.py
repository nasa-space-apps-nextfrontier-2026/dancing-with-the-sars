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


def test_alerts_list_endpoint(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["synthetic"] is True
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 3
    assert data["next_cursor"] is None
    get_settings.cache_clear()


def test_alerts_list_pagination(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get("/api/v1/alerts?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["next_cursor"] == "1"

    response2 = client.get(f"/api/v1/alerts?limit=1&cursor={data['next_cursor']}")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["items"]) == 1
    assert data2["items"][0]["alert_id"] != data["items"][0]["alert_id"]
    assert data2["next_cursor"] == "2"
    get_settings.cache_clear()


def test_alerts_filter_by_area_id(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get("/api/v1/alerts?area_id=demo-area-01")
    assert response.status_code == 200
    data = response.json()
    for alert in data["items"]:
        assert alert["area_id"] == "demo-area-01"
    get_settings.cache_clear()


def test_alerts_filter_by_type(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get("/api/v1/alerts?type=fire_detected")
    assert response.status_code == 200
    data = response.json()
    for alert in data["items"]:
        assert alert["type"] == "fire_detected"
    get_settings.cache_clear()


def test_alerts_filter_by_since(monkeypatch):
    client = _login_client(monkeypatch)
    since = "2020-01-01T00:00:00Z"
    response = client.get(f"/api/v1/alerts?since={since}")
    assert response.status_code == 200
    data = response.json()
    for alert in data["items"]:
        assert alert["detected_at"] >= since
    get_settings.cache_clear()


def test_alerts_invalid_since_returns_422(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get("/api/v1/alerts?since=not-a-date")
    assert response.status_code == 422
    data = response.json()
    assert data["error"]["code"] == "REQUEST_FAILED"
    assert "Invalid since" in data["error"]["message"]
    get_settings.cache_clear()


def test_alert_detail_endpoint(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get("/api/v1/alerts/demo-alert-01")
    assert response.status_code == 200
    data = response.json()
    assert data["alert_id"] == "demo-alert-01"
    assert data["synthetic"] is True
    assert "title" in data
    assert "detected_at" in data
    assert "processed_at" in data
    assert "label" in data
    assert data["label"] in ["Observed", "Reported", "Corroborated", "Unknown"]
    assert "source" in data
    assert "cause" in data
    assert data["cause"] == "Unknown"
    assert "warning" in data
    get_settings.cache_clear()


def test_alert_detail_not_found(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get("/api/v1/alerts/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "REQUEST_FAILED"
    get_settings.cache_clear()


def test_no_forbidden_words_in_alerts(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    forbidden = ["caused by", "blackout"]
    # Check human-readable text fields only, not technical field names like "safety_tag"
    text_fields = ["title", "warning", "cause", "label"]
    for alert in data["items"]:
        for field in text_fields:
            text = str(alert.get(field, "")).lower()
            for word in forbidden:
                assert word not in text, f"Forbidden word '{word}' found in alert {alert['alert_id']} field {field}"
    get_settings.cache_clear()


def test_alert_labels_are_valid(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    valid_labels = {"Observed", "Reported", "Corroborated", "Unknown"}
    for alert in data["items"]:
        assert alert["label"] in valid_labels
    get_settings.cache_clear()


def test_alerts_have_required_fields(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    required = ["alert_id", "area_id", "type", "title", "detected_at", "processed_at",
                "label", "source", "cause", "warning", "synthetic"]
    for alert in data["items"]:
        for field in required:
            assert field in alert, f"Missing field '{field}' in alert {alert['alert_id']}"
    get_settings.cache_clear()


def test_alert_types_include_fire_and_power_loss(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    types = {alert["type"] for alert in data["items"]}
    assert "fire_detected" in types
    assert "possible_power_loss" in types
    get_settings.cache_clear()


def test_unauthorized_returns_401():
    client = TestClient(app)
    response = client.get("/api/v1/alerts")
    assert response.status_code == 401