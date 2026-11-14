"""ML wiring: worker artifacts -> API. Small synthetic tables only; checks safety and the contract."""
import csv
import gzip
import json
from datetime import UTC, datetime, timedelta

import pytest
from backend.app.api.v1 import SPEC
from backend.app.core.config import get_settings
from backend.app.core.security import hash_password
from backend.app.main import app
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from worker.publish import damage_artifacts, publish

NOW = datetime.now(UTC) - timedelta(hours=1)


def damage_rows(n_candidates=4, pair_after="2026-06-24..2026-07-18"):
    rows = []
    for i in range(n_candidates):
        rows.append({"h3_r9": f"892db110{i:02d}33ffff", "h3_r8": "882db11003fffff",
                     "damage_class": "possible_candidate", "score": 0.7 + i / 100, "reasons": "hh_drop,low_hv",
                     "run_id": "run1", "evidence_label": "observed", "confidence": "medium",
                     "s1_agrees": "False", "version_confounded": "True",
                     "pair_after": pair_after})
    rows.append({"h3_r9": "892db1200033ffff", "h3_r8": "882db12003fffff", "damage_class": "unknown",
                 "score": None, "reasons": "sparse_buildings", "run_id": "run1",
                 "evidence_label": "unknown", "confidence": None, "s1_agrees": "False",
                 "version_confounded": "True", "pair_after": pair_after})
    return rows


def history(path, flagged_by_both=True):
    start = datetime(2026, 7, 1)
    with gzip.open(path, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "satellite", "cell", "mean_radiance", "n_pixels", "n_clear"])
        for sat in ("NOAA-20", "NOAA-21"):
            for i in range(100):
                dark = flagged_by_both and i >= 98
                w.writerow([(start + timedelta(days=i)).date().isoformat(), sat, "882db1900ffffff",
                            2.0 if dark else 10.0, 4, 4])


@pytest.fixture
def published(tmp_path, monkeypatch):
    out = tmp_path / "published"
    dmg, vals = damage_artifacts(damage_rows(), NOW)
    out.mkdir()
    (out / "damage.json").write_text(json.dumps(dmg))
    (out / "values.json").write_text(json.dumps(vals))
    history(tmp_path / "h.csv.gz")
    publish(str(out), None, str(tmp_path / "h.csv.gz"), False, NOW)   # writes alerts and manifest
    (out / "damage.json").write_text(json.dumps(dmg))
    (out / "values.json").write_text(json.dumps(vals))
    monkeypatch.setenv("PUBLISHED_DIR", str(out))
    users = {"scoped": {"password_hash": hash_password("test-only-password"), "role": "analyst",
                        "area_scopes": ["892db1100033ffff", "882db19ffffffff"]},
             "wide": {"password_hash": hash_password("test-only-password"), "role": "analyst",
                      "area_scopes": ["*"]}}
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", json.dumps(users))
    get_settings.cache_clear()
    yield out
    get_settings.cache_clear()


def login(name):
    client = TestClient(app)
    response = client.post("/api/v1/session", json={"username": name, "password": "test-only-password"})
    assert response.status_code == 200
    return client


def valid(schema_name, payload):
    schema = {"$ref": f"#/components/schemas/{schema_name}", "components": SPEC["components"]}
    errors = list(Draft202012Validator(schema).iter_errors(payload))
    assert not errors, errors[:2]


def test_restricted_endpoints_need_sign_in(published):
    anon = TestClient(app)
    for path in ("/alerts", "/areas", "/areas/892db1100033ffff/damage", "/areas/x/values"):
        assert anon.get("/api/v1" + path).status_code == 401


def test_damage_values_and_areas_follow_the_contract_and_scope(published):
    client = login("scoped")
    damage = client.get("/api/v1/areas/892db1100033ffff/damage")
    assert damage.status_code == 200
    valid("DamageList", damage.json())
    item = damage.json()["items"][0]
    assert item["candidate_class"] == "possible_candidate" and item["reason_codes"] == ["hh_drop", "low_hv"]
    values = client.get("/api/v1/areas/892db1100033ffff/values").json()
    valid("MetricList", values)
    assert values["items"][0]["label"] == "Observed" and values["items"][0]["synthetic"] is False
    assert client.get("/api/v1/areas/892db1100133ffff/damage").status_code == 403      # outside scope
    valid("AreaList", client.get("/api/v1/areas").json())
    assert [a["area_id"] for a in client.get("/api/v1/areas").json()["items"]] == ["892db1100033ffff"]
    wide = login("wide").get("/api/v1/areas?limit=2").json()
    assert len(wide["items"]) == 2 and wide["next_cursor"] == "2"


def test_alerts_come_from_both_satellites_and_never_state_a_cause(published):
    client = login("wide")
    alerts = client.get("/api/v1/alerts")
    assert alerts.status_code == 200
    valid("AlertList", alerts.json())
    alert = alerts.json()["items"][0]
    assert alert["type"] == "possible_power_loss" and alert["independent_source_count"] == 2
    assert alert["cause"] == "not determined" and "blackout" not in json.dumps(alert).lower()
    assert client.get(f"/api/v1/alerts/{alert['alert_id']}").status_code == 200
    assert client.get("/api/v1/alerts/missing").status_code == 404
    assert login("scoped").get(f"/api/v1/alerts/{alert['alert_id']}").status_code == 404   # outside scope


def test_status_reports_sources_and_failures(published):
    status = TestClient(app).get("/api/v1/status").json()
    valid("Status", status)
    by_id = {s["id"]: s for s in status["sources"]}
    assert by_id["black-marble"]["freshness"] == "Fresh" and by_id["firms"]["freshness"] == "Unknown"
    assert by_id["nisar-damage"]["failure"] == "no damage table given"


def test_public_map_is_suppressed_until_a_person_approves_and_never_shows_cells_or_exact_counts(
        published, monkeypatch):
    anon = TestClient(app)
    first = anon.get("/api/v1/public/map").json()
    valid("PublicMap", first)
    assert first["suppressed"] is True and first["layers"] == []
    monkeypatch.setenv("PUBLIC_RELEASE_APPROVED", "true")
    get_settings.cache_clear()
    second = anon.get("/api/v1/public/map").json()
    valid("PublicMap", second)
    cells = second["layers"][0]["cells"]
    assert cells == [{"h3_id": "882db11003fffff", "candidate_cells": "3-5"}]    # r8 only, bucketed
    assert "892db1100" not in json.dumps(second) and "score" not in json.dumps(second)


def test_radar_results_are_withheld_for_72_hours(tmp_path, monkeypatch):
    out = tmp_path / "published"
    out.mkdir()
    recent = (datetime.now(UTC) - timedelta(hours=10)).date().isoformat()
    dmg, vals = damage_artifacts(damage_rows(pair_after=f"2026-06-24..{recent}"), datetime.now(UTC))
    (out / "damage.json").write_text(json.dumps(dmg))
    (out / "values.json").write_text(json.dumps(vals))
    monkeypatch.setenv("PUBLISHED_DIR", str(out))
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", json.dumps(
        {"wide": {"password_hash": hash_password("test-only-password"), "role": "analyst",
                  "area_scopes": ["*"]}}))
    monkeypatch.setenv("PUBLIC_RELEASE_APPROVED", "true")
    get_settings.cache_clear()
    client = login("wide")
    assert client.get("/api/v1/areas").json()["items"] == []
    assert client.get("/api/v1/areas/892db1100033ffff/damage").json()["items"] == []
    assert client.get("/api/v1/areas/892db1100033ffff/values").json()["items"] == []
    assert TestClient(app).get("/api/v1/public/map").json()["suppressed"] is True
    get_settings.cache_clear()


def test_nothing_published_means_not_available_not_invented(tmp_path, monkeypatch):
    monkeypatch.setenv("PUBLISHED_DIR", str(tmp_path / "empty"))
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", json.dumps(
        {"wide": {"password_hash": hash_password("test-only-password"), "role": "analyst",
                  "area_scopes": ["*"]}}))
    get_settings.cache_clear()
    client = login("wide")
    assert client.get("/api/v1/alerts").json()["items"] == []
    assert client.get("/api/v1/areas/x/damage").json()["items"] == []
    assert TestClient(app).get("/api/v1/status").json()["sources"] == []
    get_settings.cache_clear()
