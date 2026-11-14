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


def test_status_endpoint(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/status')
    assert response.status_code == 200
    data = response.json()
    assert data["synthetic"] is True
    assert "sources" in data
    assert isinstance(data["sources"], list)
    for src in data["sources"]:
        assert "id" in src
        assert "freshness" in src
        assert "cached" in src
        assert "failure" in src
    get_settings.cache_clear()


def test_sources_list_endpoint(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/sources')
    assert response.status_code == 200
    data = response.json()
    assert data["synthetic"] is True
    assert "items" in data
    assert "next_cursor" in data
    assert isinstance(data["items"], list)
    if data["items"]:
        item = data["items"][0]
        assert "source_id" in item
        assert "dataset_id" in item
        assert "name" in item
    get_settings.cache_clear()


def test_sources_pagination(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/sources?cursor=0')
    assert response.status_code == 200
    data = response.json()
    assert "next_cursor" in data
    if data["next_cursor"]:
        response2 = client.get(f'/api/v1/sources?cursor={data["next_cursor"]}')
        assert response2.status_code == 200
        data2 = response2.json()
        assert "items" in data2
    get_settings.cache_clear()


def test_source_detail_endpoint(monkeypatch):
    client = _login_client(monkeypatch)
    list_resp = client.get('/api/v1/sources')
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    if items:
        source_id = items[0]["source_id"]
        response = client.get(f'/api/v1/sources/{source_id}')
        assert response.status_code == 200
        data = response.json()
        assert data["synthetic"] is True
        assert data["source_id"] == source_id
    get_settings.cache_clear()


def test_source_detail_not_found(monkeypatch):
    client = _login_client(monkeypatch)
    response = client.get('/api/v1/sources/nonexistent-source-id')
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "REQUEST_FAILED"
    get_settings.cache_clear()


def test_no_sensitive_data_in_responses(monkeypatch):
    client = _login_client(monkeypatch)
    endpoints = ['/api/v1/status', '/api/v1/sources', '/api/v1/sources/demo-source-01']
    forbidden = ['http://localhost', 'file://', '/home/', '/tmp/', 'api_key', 'password', 'secret']
    for ep in endpoints:
        response = client.get(ep)
        if response.status_code == 200:
            text = json.dumps(response.json())
            for f in forbidden:
                assert f not in text.lower(), f"Forbidden '{f}' found in {ep}"
    get_settings.cache_clear()