"""The real-mode public map remains hard-suppressed pending humanitarian review."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from backend.app.api import radar
from backend.app.core.config import get_settings
from backend.app.main import app
from backend.app.services import public_map_real

SPEC = json.loads(Path("docs/contracts/openapi.yaml").read_text(encoding="utf-8"))


def validate(payload):
    schema = {"$ref": "#/components/schemas/PublicMap", "components": SPEC["components"]}
    Draft202012Validator(schema).validate(payload)


def test_public_map_service_is_always_suppressed():
    payload = public_map_real.public_map()
    validate(payload)
    assert payload == {"synthetic": False, "resolution": 8, "layers": [],
                       "suppressed": True, "release_policy": "72h_and_review"}


@pytest.fixture
def real_mode(monkeypatch):
    monkeypatch.setenv("DEMO_SYNTHETIC", "false")
    monkeypatch.delenv("PUBLIC_RELEASE_APPROVED", raising=False)
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


def test_configuration_cannot_enable_publication_or_construct_engine(real_mode):
    def forbidden_engine():
        raise AssertionError("suppressed public map must not construct a database engine")

    real_mode.setattr(radar, "engine", forbidden_engine)
    real_mode.setenv("PUBLIC_RELEASE_APPROVED", "true")
    get_settings.cache_clear()
    client = TestClient(app)
    response = client.get("/api/v1/public/map")
    assert response.status_code == 200
    assert response.json()["suppressed"] is True
    assert response.json()["layers"] == []


def test_public_bbox_is_validated_and_applied(real_mode):
    client = TestClient(app)
    assert client.get("/api/v1/public/map?bbox=1,2,3").status_code == 422
    assert client.get("/api/v1/public/map?bbox=36,33,35,34").status_code == 422
    response = client.get("/api/v1/public/map?bbox=35.1,33.1,35.8,33.5")
    assert response.status_code == 200 and response.json()["suppressed"] is True
