import json

from backend.app.core.config import get_settings
from backend.app.core.security import hash_password
from backend.app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_public_and_denials(monkeypatch):
    assert client.get('/api/v1/health').status_code == 200
    assert client.get('/api/v1/public/map').json()['layers'] == []
    assert client.get('/api/v1/shelters').status_code == 401
    assert client.post('/api/v1/routes',json={}).status_code == 401
    assert client.get('/api/v1/layers/private/tiles/1/0/0').status_code == 401
    assert client.get('/api/v1/layers/private/files/guessed').status_code == 401

def test_role_boundary(monkeypatch):
    users={'test-analyst':{'password_hash':hash_password('test-only-password'), 'role':'analyst','area_scopes':['demo-area-01']}}
    monkeypatch.setenv('CIVISAR_DEMO_USERS_JSON',json.dumps(users))
    get_settings.cache_clear()
    with TestClient(app) as logged_in:
        response=logged_in.post('/api/v1/session',json={'username':'test-analyst','password':'test-only-password'})
        assert response.status_code == 200
        assert logged_in.get('/api/v1/shelters').status_code == 403
        assert logged_in.get('/api/v1/shelters?area_id=other-area').status_code == 403
        assert logged_in.post('/api/v1/routes',json={},headers={'X-CSRF-Token':response.json()['csrf_token']}).status_code == 403
        assert logged_in.get('/api/v1/areas/demo-area-01/summary').status_code == 501
        assert logged_in.get('/api/v1/layers/private/files/guessed').status_code == 501
    get_settings.cache_clear()

def test_all_contract_paths_registered():
    from backend.app.api.v1 import SPEC
    routes={(method,path) for path, methods in SPEC['paths'].items() for method in methods}
    implemented={(method.lower(), route.path.removeprefix('/api/v1'))
                 for route in app.routes if route.path.startswith('/api/v1') for method in route.methods}
    assert routes <= implemented


def test_readiness_reflects_database(monkeypatch):
    monkeypatch.setattr('backend.app.main.check_database', lambda: False)
    assert client.get('/internal/ready').status_code == 503
    monkeypatch.setattr('backend.app.main.check_database', lambda: True)
    assert client.get('/internal/ready').json()['status'] == 'ready'
