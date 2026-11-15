"""The handler registry (C-01) serves sample data, so it must only answer in synthetic mode.

In real-data mode (DEMO_SYNTHETIC=false) /status and /sources must come from the real backend,
never from a registry fixture marked synthetic."""

import json

from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.handlers import HANDLERS
from backend.app.main import app


def test_registry_answers_only_in_synthetic_mode(monkeypatch, tmp_path):
    async def sample_status(request, path_params):
        return {"from": "registry", "synthetic": True}

    monkeypatch.setitem(HANDLERS, ("GET", "/status"), sample_status)  # restored after the test
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", json.dumps({}))

    monkeypatch.setenv("DEMO_SYNTHETIC", "false")
    get_settings.cache_clear()
    try:
        real = TestClient(app).get("/api/v1/status")
        assert real.status_code == 200 and real.json()["synthetic"] is False   # real backend answered
        assert TestClient(app).get("/api/v1/sources").status_code == 503       # no real catalogue here

        monkeypatch.setenv("DEMO_SYNTHETIC", "true")
        get_settings.cache_clear()
        sample = TestClient(app).get("/api/v1/status")
        assert sample.json() == {"from": "registry", "synthetic": True}         # registry answered
    finally:
        get_settings.cache_clear()


def test_synthetic_sources_never_relabel_real_records(monkeypatch, tmp_path):
    """A real source register on disk must not be served stamped synthetic (labelling rule)."""
    from backend.app.handlers import sources

    register = tmp_path / "sources.json"
    register.write_text(json.dumps([{"source_id": "ds-real", "dataset_id": "x", "name": "Real", "synthetic": False}]))
    monkeypatch.setattr(sources, "SOURCES_MANIFEST", register, raising=False)
    monkeypatch.setenv("DEMO_SYNTHETIC", "true")
    get_settings.cache_clear()
    try:
        items = TestClient(app).get("/api/v1/sources").json()["items"]
        assert [i["source_id"] for i in items] == ["demo-source-01"]
        assert TestClient(app).get("/api/v1/sources/ds-real").status_code == 404
    finally:
        get_settings.cache_clear()
