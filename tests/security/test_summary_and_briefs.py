"""Real-data area summary and briefs (DEMO_SYNTHETIC=false) against a fake database.

Pins: no people numbers without the population file (503, never invented); ranges from the
population cells; held records hidden from analysts and from every brief; area scope; CSRF on
create; role-based sections re-checked on read; expiry; escaped print page.
Population and radar values here are synthetic test numbers, not real data.
"""

import copy
import csv
import datetime as dt
import gzip
import json
from pathlib import Path
from types import SimpleNamespace

import h3
import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from backend.app.api import radar
from backend.app.core.config import get_settings
from backend.app.core.security import hash_password
from backend.app.main import app
from backend.app.services import radar_real
from backend.app.services.live_real import iso

SPEC = json.loads(Path("docs/contracts/openapi.yaml").read_text(encoding="utf-8"))
AREA = h3.latlng_to_cell(33.3, 35.5, 8)
CELLS = sorted(h3.cell_to_children(AREA, 9))
PAST = dt.datetime(2026, 7, 21, tzinfo=dt.UTC)
FUTURE = dt.datetime(2999, 1, 1, tzinfo=dt.UTC)
SOURCE = {"synthetic": True, "accessed_at": "2026-11-14T00:00:00Z", "checksum": None, "live_tested": False,
          "source_id": "nisar-gcov-beta-151d72", "dataset_id": "T", "name": "Test <script>x</script>",
          "provider": "test", "product_level": "L2", "cmr_concept_id": "T", "challenge_provenance": "T",
          "source_url": "https://example.org/", "acquisition_start": "2026-01-01T00:00:00Z",
          "acquisition_end": "2026-01-02T00:00:00Z", "processing_version": "T",
          "spatial_coverage": {"area_id": "south-lebanon-demo", "geometry": None, "track": 151, "frame": 72},
          "resolution_m": 20, "licence": "test", "api": "test", "independence_family": "nisar", "limits": []}


def validate(name, obj):
    Draft202012Validator(SPEC["components"]["schemas"][name] | {"components": SPEC["components"]}).validate(obj)


def result(cell, level, release=PAST, label="Observed"):
    return SimpleNamespace(area_id=cell, classification="candidate_change", evidence_label=label,
                           reason_codes=[f"level:{level}"], release_at=release)


class FakeEngine:
    """Answers the handful of queries the summary and briefs make."""

    def __init__(self):
        self.briefs = {}
        self.results = [result(CELLS[0], "destroyed_or_severe_candidate"),
                        result(CELLS[1], "moderate_candidate"),
                        result(CELLS[2], "possible_candidate", release=FUTURE)]

    def _execute(self, sql, params=None):
        sql, params = str(sql), params or {}
        rows: list = []
        if "INSERT INTO briefs" in sql:
            self.briefs[params["id"]] = SimpleNamespace(area_id=params["a"], expires_at=params["e"],
                                                        payload=json.loads(params["p"]))
        elif "FROM briefs" in sql:
            rows = [self.briefs[params["i"]]] if params["i"] in self.briefs else []
        elif "SELECT area_id, resolution FROM areas" in sql:
            rows = [SimpleNamespace(area_id=AREA, resolution=8)] if params["a"] == AREA else []
        elif "FROM radar_artifacts" in sql:
            rows = [SimpleNamespace(id="art-a", run_id="run-a", after_acquired_at=PAST)]
        elif "FROM radar_area_results" in sql:
            rows = self.results if params["a"] == AREA else []
        elif "SELECT area_id FROM areas" in sql:
            rows = [(c,) for c in [AREA, *CELLS]] if params["a"] == AREA else []
        rows = copy.deepcopy(rows)
        return SimpleNamespace(first=lambda: rows[0] if rows else None, all=lambda: rows,
                               scalar=lambda: rows[0][0] if rows else None)

    def _ctx(self):
        engine = self

        class Ctx:
            def __enter__(self):
                return SimpleNamespace(execute=engine._execute)

            def __exit__(self, *a):
                return False
        return Ctx()

    connect = begin = _ctx


@pytest.fixture
def env(tmp_path, monkeypatch):
    (tmp_path / "local" / "radar_contract").mkdir(parents=True)
    (tmp_path / "local" / "radar_contract" / "sources.json").write_text(json.dumps([SOURCE]))
    users = {r: {"password_hash": hash_password("test-only-password"), "role": r,
                 "area_scopes": ["south-lebanon-demo"]} for r in ("analyst", "officer", "admin")}
    users["elsewhere"] = {"password_hash": hash_password("test-only-password"), "role": "coordinator",
                          "area_scopes": ["demo-area-01"]}
    monkeypatch.setenv("DEMO_SYNTHETIC", "false")
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", json.dumps(users))
    get_settings.cache_clear()
    radar_real._catalogue.cache_clear()
    fake = FakeEngine()
    monkeypatch.setattr(radar, "engine", lambda: fake)
    yield SimpleNamespace(root=tmp_path, db=fake)
    get_settings.cache_clear()


def add_population(root):
    with gzip.open(root / "local" / "population.csv.gz", "wt", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cell_id", "pop_low", "pop_high", "pop_year"])
        for cell, low, high in ((CELLS[0], 100, 150), (CELLS[1], 200, 260), (CELLS[2], 50, 70)):
            w.writerow([cell, low, high, 2020])


def signed_in(role):
    c = TestClient(app)
    r = c.post("/api/v1/session", json={"username": role, "password": "test-only-password"})
    assert r.status_code == 200
    c.headers["X-CSRF-Token"] = r.json()["csrf_token"]
    return c


def people(summary):
    return {k: (v["low"], v["high"], v["label"]) for k, v in summary["people"].items()}


def test_no_population_means_unavailable_not_invented(env):
    r = signed_in("analyst").get(f"/api/v1/areas/{AREA}/summary")
    assert r.status_code == 503 and r.json()["error"]["code"] == "UNAVAILABLE"


def test_summary_ranges_follow_population_and_hold(env):
    add_population(env.root)
    r = signed_in("analyst").get(f"/api/v1/areas/{AREA}/summary")
    assert r.status_code == 200
    s = r.json()
    validate("AreaSummary", s)
    assert people(s) == {"residents": (350, 480, "Reported"),
                         "potentially_affected": (300, 410, "Reported"),  # held cell left out
                         "potentially_displaced": (200, 280, "Reported")}  # 100% + 50% shares
    assert s["permissions"] == {"routes": False, "shelters": False, "brief": True}
    assert s["severity"]["rank"] is None and s["safety_tag"] == "restricted_aggregate"
    admin = signed_in("admin").get(f"/api/v1/areas/{AREA}/summary").json()
    assert people(admin)["potentially_affected"][:2] == (300, 410)  # no admin bypass of the hold


def test_summary_scope_and_unknown_area(env):
    add_population(env.root)
    other = h3.latlng_to_cell(10.0, 10.0, 8)
    assert signed_in("analyst").get(f"/api/v1/areas/{other}/summary").status_code == 403
    near = h3.latlng_to_cell(33.4, 35.6, 8)
    assert signed_in("analyst").get(f"/api/v1/areas/{near}/summary").status_code == 404


def test_brief_needs_csrf_valid_body_and_scope(env):
    add_population(env.root)
    c = signed_in("analyst")
    body = {"area_id": AREA, "as_of": "2026-11-14T12:00:00Z"}
    assert c.post("/api/v1/briefs", json=body, headers={"X-CSRF-Token": "wrong"}).status_code == 403
    assert c.post("/api/v1/briefs", json={"area_id": AREA}).status_code == 422
    assert c.post("/api/v1/briefs", json=body | {"as_of": "soon"}).status_code == 422
    far = h3.latlng_to_cell(10.0, 10.0, 8)
    assert c.post("/api/v1/briefs", json=body | {"area_id": far}).status_code == 403
    assert c.post("/api/v1/briefs", json=body | {"area_id": "nowhere"}).status_code == 403


def test_brief_round_trip_and_read_checks(env):
    add_population(env.root)
    admin = signed_in("admin")
    r = admin.post("/api/v1/briefs", json={"area_id": AREA, "as_of": "2026-11-14T12:00:00Z"})
    assert r.status_code == 200
    brief = r.json()
    validate("Brief", brief)
    assert people(brief["area_summary"])["potentially_affected"][:2] == (300, 410)
    assert [f["source_id"] for f in brief["source_footnotes"]] == ["nisar-gcov-beta-151d72"]

    rid = brief["report_id"]
    analyst = signed_in("analyst").get(f"/api/v1/briefs/{rid}").json()
    validate("Brief", analyst)
    assert analyst["area_summary"]["permissions"]["routes"] is False
    assert "route_options: needs officer role" in analyst["omitted_sections"]
    officer = signed_in("officer").get(f"/api/v1/briefs/{rid}").json()
    assert officer["area_summary"]["permissions"] == {"routes": True, "shelters": False, "brief": True}

    assert signed_in("elsewhere").get(f"/api/v1/briefs/{rid}").status_code == 404  # out of scope
    assert TestClient(app).get(f"/api/v1/briefs/{rid}").status_code == 401
    env.db.briefs[rid].expires_at = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
    assert signed_in("analyst").get(f"/api/v1/briefs/{rid}").status_code == 404  # expired


def test_print_page_is_escaped_and_self_contained(env):
    add_population(env.root)
    c = signed_in("analyst")
    rid = c.post("/api/v1/briefs", json={"area_id": AREA, "as_of": "2026-11-14T12:00:00Z"}).json()["report_id"]
    r = c.get(f"/api/v1/briefs/{rid}/print")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
    assert "default-src 'none'" in r.headers["content-security-policy"]
    page = r.text
    assert "<script>" not in page and "&lt;script&gt;" in page
    assert "RESTRICTED" in page and "300–410" in page
    assert "http" not in page.replace("https://example.org/", "")  # loads nothing from outside
    assert "safe" not in page.lower()


def test_brief_expiry_is_eight_hours(env):
    add_population(env.root)
    c = signed_in("analyst")
    b = c.post("/api/v1/briefs", json={"area_id": AREA, "as_of": "2026-11-14T12:00:00Z"}).json()
    stored = env.db.briefs[b["report_id"]]
    assert b["expires_at"] == iso(stored.expires_at)
    left = stored.expires_at - dt.datetime.now(dt.UTC)
    assert dt.timedelta(hours=7, minutes=59) < left <= dt.timedelta(hours=8)
