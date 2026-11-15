import json

from backend.app.core.config import get_settings
from backend.app.core.security import hash_password
from backend.app.handlers import HANDLERS
from backend.app.main import app
from fastapi.testclient import TestClient


def test_registry_calls_registered_handler(monkeypatch):
    users = {'test-analyst': {'password_hash': hash_password('test-only-password'), 'role': 'analyst', 'area_scopes': ['demo-area-01']}}
    monkeypatch.setenv('CIVISAR_DEMO_USERS_JSON', json.dumps(users))
    get_settings.cache_clear()

    async def test_handler(request, path_params):
        return {"custom": "ok", "synthetic": True}

    HANDLERS[("GET", "/status")] = test_handler
    try:
        with TestClient(app) as client:
            response = client.post('/api/v1/session', json={'username': 'test-analyst', 'password': 'test-only-password'})
            assert response.status_code == 200
            response = client.get('/api/v1/status')
            assert response.status_code == 200
            assert response.json() == {"custom": "ok", "synthetic": True}
    finally:
        del HANDLERS[("GET", "/status")]
    get_settings.cache_clear()

def test_unregistered_path_returns_501(monkeypatch):
    users = {'test-analyst': {'password_hash': hash_password('test-only-password'), 'role': 'analyst', 'area_scopes': ['demo-area-01']}}
    monkeypatch.setenv('CIVISAR_DEMO_USERS_JSON', json.dumps(users))
    get_settings.cache_clear()

    with TestClient(app) as client:
        response = client.post('/api/v1/session', json={'username': 'test-analyst', 'password': 'test-only-password'})
        assert response.status_code == 200
        response = client.get('/api/v1/areas/demo-area-01/summary')
        assert response.status_code == 501
        assert response.json()["error"]["code"] == "NOT_IMPLEMENTED"

    get_settings.cache_clear()

def test_private_path_requires_auth(monkeypatch):
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", '{}')
    get_settings.cache_clear()
    client = TestClient(app)
    response = client.get("/api/v1/shelters")
    assert response.status_code == 401
    get_settings.cache_clear()