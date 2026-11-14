import json

from backend.app.core.config import get_settings
from backend.app.core.security import hash_password
from backend.app.main import app
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

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
        summary = logged_in.get('/api/v1/areas/demo-area-01/summary')
        assert summary.status_code == 200
        assert summary.json()['synthetic'] is True
        assert summary.json()['people']['residents']['label'] == 'Unknown'
        assert logged_in.get('/api/v1/areas/other-area/summary').status_code == 403
        assert logged_in.get('/api/v1/areas/unknown/summary').status_code == 403
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


def test_synthetic_area_and_source_match_canonical_contract(monkeypatch):
    from backend.app.api.v1 import SPEC

    users = {'analyst': {'password_hash': hash_password('local-test-password'),
                         'role': 'analyst', 'area_scopes': ['demo-area-01', 'missing']}}
    monkeypatch.setenv('CIVISAR_DEMO_USERS_JSON', json.dumps(users))
    get_settings.cache_clear()
    with TestClient(app) as visitor:
        assert visitor.get('/api/v1/areas/demo-area-01/summary').status_code == 401
        login = visitor.post('/api/v1/session', json={
            'username': 'analyst', 'password': 'local-test-password'})
        assert login.status_code == 200
        summary = visitor.get('/api/v1/areas/demo-area-01/summary')
        source = visitor.get('/api/v1/sources/demo-source-01')
        assert summary.status_code == source.status_code == 200
        root = {'components': SPEC['components']}
        for name, payload in [('AreaSummary', summary.json()), ('SourceRecord', source.json())]:
            Draft202012Validator({**root, '$ref': f'#/components/schemas/{name}'}).validate(payload)
        assert summary.json()['people']['residents']['source'] == [source.json()['source_id']]
        assert source.json()['live_tested'] is False
        assert visitor.get('/api/v1/areas/demo-area-01/summary').headers['Cache-Control'] == 'private, no-store'
        assert visitor.get('/api/v1/areas/missing/summary').status_code == 404
        assert visitor.get('/api/v1/areas/outside-scope/summary').status_code == 403
        assert visitor.get('/api/v1/sources/missing').status_code == 404
    get_settings.cache_clear()


def test_synthetic_adapter_does_not_serve_as_real_data(monkeypatch):
    monkeypatch.setenv('DEMO_SYNTHETIC', 'false')
    monkeypatch.setenv('CIVISAR_DEMO_USERS_JSON', json.dumps({
        'analyst': {'password_hash': hash_password('local-test-password'),
                    'role': 'analyst', 'area_scopes': ['demo-area-01']}}))
    get_settings.cache_clear()
    try:
        response = client.get('/api/v1/sources/demo-source-01')
        assert response.status_code == 503
        assert response.json()['error']['code'] == 'UNAVAILABLE'
        with TestClient(app) as visitor:
            login = visitor.post('/api/v1/session', json={
                'username': 'analyst', 'password': 'local-test-password'})
            assert login.status_code == 200
            assert visitor.get('/api/v1/areas/demo-area-01/summary').status_code == 503
    finally:
        get_settings.cache_clear()


def test_radar_catalogue_exposes_dates_but_no_renderable_pixels(monkeypatch):
    users = {'analyst': {'password_hash': hash_password('local-test-password'),
                         'role': 'analyst', 'area_scopes': ['demo-area-01']}}
    monkeypatch.setenv('CIVISAR_DEMO_USERS_JSON', json.dumps(users))
    get_settings.cache_clear()
    try:
        with TestClient(app) as visitor:
            login = visitor.post('/api/v1/session', json={
                'username': 'analyst', 'password': 'local-test-password'})
            assert login.status_code == 200
            layers = visitor.get('/api/v1/layers?area_id=demo-area-01')
            assert layers.status_code == 200
            assert layers.json()['items'][0]['extent'] is None
            series = visitor.get(
                '/api/v1/layers/demo-damage-r8/timeseries?area_id=demo-area-01')
            assert series.status_code == 200
            payload = series.json()
            assert [point['acquired_at'] for point in payload['points']] == [
                '2026-01-19T00:00:00Z', '2026-06-24T00:00:00Z']
            assert all(point['valid_pixel_count'] == 0 for point in payload['points'])
            assert all(point['raster_available'] is False for point in payload['points'])
            assert payload['missing_intervals'] == [{
                'start': '2026-01-20', 'end': '2026-06-17',
                'reason': 'Source-reported acquisition gap; not interpolated'}]
    finally:
        get_settings.cache_clear()


def test_session_restoration_logout_and_expiry(monkeypatch):
    from backend.app.core import security

    monkeypatch.setenv('CIVISAR_DEMO_USERS_JSON', json.dumps({
        'analyst': {'password_hash': hash_password('local-test-password'),
                    'role': 'analyst', 'area_scopes': ['demo-area-01']}}))
    get_settings.cache_clear()
    try:
        with TestClient(app) as visitor:
            login = visitor.post('/api/v1/session', json={
                'username': 'analyst', 'password': 'local-test-password'})
            assert login.status_code == 200
            assert visitor.get('/api/v1/session').json()['role'] == 'analyst'
            assert visitor.delete('/api/v1/session').status_code == 403
            logout = visitor.delete('/api/v1/session', headers={
                'X-CSRF-Token': login.json()['csrf_token']})
            assert logout.status_code == 204
            assert logout.content == b''
            assert visitor.get('/api/v1/session').status_code == 401
            login = visitor.post('/api/v1/session', json={
                'username': 'analyst', 'password': 'local-test-password'})
            token = visitor.cookies.get('civisar_session')
            key = security.hashlib.sha256(token.encode()).hexdigest()
            identity, _, csrf = security._sessions[key]
            security._sessions[key] = (identity, security.time.time() - 1, csrf)
            assert visitor.get('/api/v1/session').status_code == 401
            assert visitor.get('/api/v1/areas/demo-area-01/summary').status_code == 401
    finally:
        get_settings.cache_clear()
