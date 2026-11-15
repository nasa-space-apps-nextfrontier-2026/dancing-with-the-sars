"""PUBLIC_REAL_DATA: the dashboard has no sign-in (team decision 15 Nov 2026).

Anonymous GETs read real-data routes as a read-only viewer; writes and admin routes still need a session.
"""
from backend.app.api import v1
from backend.app.core.config import get_settings
from backend.app.main import app
from backend.app.policy.scope import AOI_ID
from fastapi.testclient import TestClient


def _mode(monkeypatch, public: bool, synthetic: bool = False) -> None:
    monkeypatch.setenv('DEMO_SYNTHETIC', 'true' if synthetic else 'false')
    monkeypatch.setenv('PUBLIC_REAL_DATA', 'true' if public else 'false')
    monkeypatch.setenv('CIVISAR_DEMO_USERS_JSON', '{}')
    get_settings.cache_clear()


def test_viewer_is_read_only_coordinator_over_the_demo_box():
    assert v1.PUBLIC_VIEWER.role == 'coordinator'
    assert v1.PUBLIC_VIEWER.area_scopes == (AOI_ID,)


def test_anonymous_get_passes_auth_only_when_enabled(monkeypatch):
    try:
        _mode(monkeypatch, public=False)
        with TestClient(app) as c:
            assert c.get('/api/v1/incidents').status_code == 401
        _mode(monkeypatch, public=True)
        with TestClient(app) as c:
            assert c.get('/api/v1/incidents').status_code != 401
    finally:
        get_settings.cache_clear()


def test_writes_and_admin_still_need_sign_in(monkeypatch):
    try:
        _mode(monkeypatch, public=True)
        with TestClient(app) as c:
            assert c.post('/api/v1/briefs', json={}).status_code in (401, 403)
            assert c.get('/api/v1/admin/audit').status_code == 401
    finally:
        get_settings.cache_clear()


def test_synthetic_mode_ignores_the_switch(monkeypatch):
    try:
        _mode(monkeypatch, public=True, synthetic=True)
        with TestClient(app) as c:
            assert c.get('/api/v1/incidents').status_code == 401
    finally:
        get_settings.cache_clear()
