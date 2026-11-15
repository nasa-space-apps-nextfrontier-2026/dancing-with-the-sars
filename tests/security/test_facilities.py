"""Real-data facilities (doc 07): sign-in, area scope, need-to-know subset for analysts (no location),
point for officer and above, damage status from the cell's radar result (no detected change is never
"undamaged"), 503 until loaded, and the loader keeps only sites inside Lebanon. Synthetic test values."""

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
from backend.app.services import facilities_real
from scripts import load_facilities

SPEC = json.loads(Path("docs/contracts/openapi.yaml").read_text(encoding="utf-8"))
PW = "test-only-password"
INSIDE = h3.latlng_to_cell(33.3, 35.5, 8)
CELL_A, CELL_B = sorted(h3.cell_to_children(INSIDE, 9))[:2]
OTHER = h3.latlng_to_cell(33.45, 35.7, 8)
FAR = h3.latlng_to_cell(10.0, 10.0, 8)


def facility(fid, kind, cell):
    lat, lon = h3.cell_to_latlng(cell)
    return SimpleNamespace(facility_id=fid, type=kind, h3_r9=cell, h3_r8=h3.cell_to_parent(cell, 8),
                           osm_timestamp=None, lon=lon, lat=lat)


class FacilityDB:
    def __init__(self, loaded=True):
        self.loaded = loaded
        self.rows = [facility("osm:hospital1", "hospital", CELL_A), facility("osm:school1", "school", CELL_B),
                     facility("osm:water1", "water", h3.cell_to_children(OTHER, 9)[0])]

    def _execute(self, sql, p=None):
        sql, p = " ".join(str(sql).split()), p or {}
        rows = []
        if "FROM facility_runs" in sql:
            rows = [SimpleNamespace(run_id="r1")] if self.loaded else []
        elif "FROM facilities" in sql:
            rows = [r for r in self.rows
                    if ("a" not in p or p["a"] in (r.h3_r8, r.h3_r9)) and ("t" not in p or r.type == p["t"])]
        return SimpleNamespace(first=lambda: rows[0] if rows else None, all=lambda: list(rows))

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
def db(monkeypatch):
    users = {r: {"password_hash": hash_password(PW), "role": r, "area_scopes": ["south-lebanon-demo"]}
             for r in ("analyst", "officer", "coordinator", "admin")}
    users["narrow"] = {"password_hash": hash_password(PW), "role": "officer", "area_scopes": [INSIDE]}
    monkeypatch.setenv("DEMO_SYNTHETIC", "false")
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", json.dumps(users))
    get_settings.cache_clear()
    store = FacilityDB()
    monkeypatch.setattr(radar, "engine", lambda: store)
    monkeypatch.setattr(facilities_real, "_cell_damage", lambda _e, r8, _i: {
        CELL_A: "Radar damage candidate in this cell (moderate). Not confirmed; field check needed."}
        if r8 == INSIDE else {})
    yield store
    get_settings.cache_clear()


def login(user):
    c = TestClient(app)
    assert c.post("/api/v1/session", json={"username": user, "password": PW}).status_code == 200
    return c


def validate(obj):
    Draft202012Validator(SPEC["components"]["schemas"]["FacilityList"] | {"components": SPEC["components"]}).validate(obj)


def test_signed_out_and_not_loaded(db):
    assert TestClient(app).get(f"/api/v1/areas/{INSIDE}/facilities").status_code == 401
    db.loaded = False
    r = login("analyst").get(f"/api/v1/areas/{INSIDE}/facilities")
    assert r.status_code == 503  # never an empty "no facilities"


def test_analyst_gets_no_location(db):
    r = login("analyst").get(f"/api/v1/areas/{INSIDE}/facilities")
    assert r.status_code == 200
    body = r.json()
    validate(body)
    assert body["synthetic"] is False
    assert {i["facility_id"] for i in body["items"]} == {"osm:hospital1", "osm:school1"}
    assert all(i["geometry"] is None and i["operating_status"] == "Unknown" for i in body["items"])
    by_id = {i["facility_id"]: i for i in body["items"]}
    assert by_id["osm:hospital1"]["damage_status"].startswith("Radar damage candidate")
    assert by_id["osm:school1"]["damage_status"] == facilities_real.NO_CHANGE
    assert "undamaged" in facilities_real.NO_CHANGE and "Not confirmed" in facilities_real.NO_CHANGE


@pytest.mark.parametrize("role", ["officer", "coordinator", "admin"])
def test_officer_and_above_get_the_point(db, role):
    body = login(role).get(f"/api/v1/areas/{INSIDE}/facilities").json()
    validate(body)
    assert all(i["geometry"]["type"] == "Point" for i in body["items"])


def test_scope_type_filter_paging_and_bad_area(db):
    narrow = login("narrow")
    assert narrow.get(f"/api/v1/areas/{OTHER}/facilities").status_code == 403
    assert narrow.get(f"/api/v1/areas/{FAR}/facilities").status_code == 403
    assert narrow.get("/api/v1/areas/south-lebanon-demo/facilities").status_code == 403
    cell = narrow.get(f"/api/v1/areas/{CELL_A}/facilities").json()
    assert [i["facility_id"] for i in cell["items"]] == ["osm:hospital1"]
    a = login("analyst")
    whole = a.get("/api/v1/areas/south-lebanon-demo/facilities").json()
    assert len(whole["items"]) == 3
    assert [i["type"] for i in a.get(f"/api/v1/areas/{INSIDE}/facilities?type=school").json()["items"]] == ["school"]
    first = a.get(f"/api/v1/areas/{INSIDE}/facilities?limit=1").json()
    assert len(first["items"]) == 1 and first["next_cursor"] == "1"
    assert a.get(f"/api/v1/areas/{INSIDE}/facilities?limit=0").status_code == 422
    r7 = h3.cell_to_parent(INSIDE, 7)
    assert a.get(f"/api/v1/areas/{r7}/facilities").status_code == 404


def test_loader_keeps_lebanon_sites_only(tmp_path):
    square = {"type": "Polygon", "coordinates": [[[35.4, 33.2], [35.6, 33.2], [35.6, 33.4], [35.4, 33.4], [35.4, 33.2]]]}
    (tmp_path / "b.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {}, "geometry": square}]}), encoding="utf-8")
    (tmp_path / "f.csv").write_text(
        "facility_id,type,name,lat,lon,cell_id,source,osm_timestamp,status,status_source\n"
        "osm:h1,hospital,A,33.3,35.5,,OSM,,Unknown,\n"
        "osm:s1,school,B,33.05,35.5,,OSM,,Unknown,\n"
        "osm:p1,police,C,33.3,35.5,,OSM,,Unknown,\n", encoding="utf-8")
    rows, counts = load_facilities.read(tmp_path / "f.csv", tmp_path / "b.geojson")
    assert [r["id"] for r in rows] == ["osm:h1"]
    assert counts["outside_lebanon"] == 1 and counts["excluded_type"] == 1
    assert rows[0]["r8"] == h3.cell_to_parent(rows[0]["r9"], 8)
    assert "name" not in rows[0]
