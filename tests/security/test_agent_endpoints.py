"""U-06 endpoints on PostGIS (in-memory stand-in): 72-hour hold, area scope, role-specific
recommendations, insights only for whole-box users, bbox limits, no residents, contract shapes.
All records are synthetic test values."""

import copy
import datetime as dt
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

SPEC = json.loads(Path("docs/contracts/openapi.yaml").read_text(encoding="utf-8"))
INSIDE = h3.latlng_to_cell(33.3, 35.5, 8)
INSIDE2 = h3.latlng_to_cell(33.45, 35.7, 8)
FAR = h3.latlng_to_cell(10.0, 10.0, 8)
PAST = dt.datetime(2026, 7, 21, tzinfo=dt.UTC)
FUTURE = dt.datetime(2999, 1, 1, tzinfo=dt.UTC)
PW = "test-only-password"
PARTS = ["people", "facility", "damage", "fire", "services", "time", "access"]


def validate(name, obj):
    Draft202012Validator(SPEC["components"]["schemas"][name] | {"components": SPEC["components"]}).validate(obj)


def incident(iid, area, rank, kind="damage_candidate_area"):
    parts = {n: {"status": "unknown", "value": None, "points": None, "weight": w, "detail": "not loaded"}
             for n, w in zip(PARTS, [30, 20, 15, 15, 10, 5, 5], strict=True)}
    parts["damage"] = {"status": "known", "value": 0.6, "points": 9.0, "weight": 15,
                       "detail": "radar damage candidate (moderate); one radar only"}
    return {"incident_id": iid, "area_id": area, "kind": kind, "rank": rank, "score_low": 9.0, "score_high": 89.0,
            "could_rank_higher": True, "parts": parts, "reasons": ["radar damage candidate (moderate); one radar only"],
            "unknowns": ["people: not loaded"]}


def rec(playbooks, checklist=("Field check of the area before acting on radar candidates",)):
    return {"assistant": "CIVISAR assistant", "situation": "Data shows: test.",
            "options": [{"playbook": p, "title": p, "why": ["test"], "needs": ["x"], "risks": ["y"],
                         "trade_off": "Gain: a. Give up: b."} for p in playbooks],
            "we_do_not_know": ["population not loaded"], "checklist": list(checklist),
            "next_review": {"radar": "after the next NISAR pass and its 72-hour hold"},
            "note": "Options, not orders. The officer decides; choices are logged by the API."}


def budget(area):
    return {"synthetic": False, "area_id": area, "label": "Planning indication only",
            "cost_usd": {"low": 1.0, "high": 2.0}, "duration_months": {"low": 3.0, "high": 9.0},
            "work_floor_area_m2": {"low": 1.0, "high": 2.0}, "crew_scale": "per_neighbourhood",
            "buildings_in_candidate_cells": 1, "assumptions": {}, "limits": ["test"]}


def building(bid, cell):
    return {"building_id": bid, "h3_r9": cell, "use": "residential", "height_low_m": 3.0, "height_mid_m": 6.0,
            "height_high_m": 9.0, "height_source": "ghsl", "floors_low": 1, "floors_high": 3,
            "damage_class": "moderate_candidate", "evidence_label": "observed", "second_sensor_agrees": None,
            "height_tag": "Inferred", "damage_tag": "From data (cell result)"}


SQUARE = json.dumps({"type": "Polygon", "coordinates": [[[35.5, 33.3], [35.5001, 33.3], [35.5001, 33.3001],
                                                         [35.5, 33.3]]]})


class AgentDB:
    def __init__(self, loaded=True):
        self.loaded = loaded
        self.incidents = [SimpleNamespace(incident_id="i1", area_id=INSIDE, release_at=PAST, record=incident("i1", INSIDE, 1)),
                          SimpleNamespace(incident_id="i2", area_id=INSIDE2, release_at=PAST, record=incident("i2", INSIDE2, 2)),
                          SimpleNamespace(incident_id="held", area_id=INSIDE, release_at=FUTURE, record=incident("held", INSIDE, 3)),
                          SimpleNamespace(incident_id="far", area_id=FAR, release_at=PAST, record=incident("far", FAR, 4))]
        self.recs = {(i, r): rec(p) for i in ("i1", "i2", "held", "far")
                     for r, p in (("analyst", ["medical", "verification"]),
                                  ("officer", ["medical", "evacuation", "verification"]),
                                  ("coordinator", ["medical", "evacuation", "verification"]))}
        self.budgets = {INSIDE: (PAST, budget(INSIDE)), INSIDE2: (FUTURE, budget(INSIDE2)),
                        "south-lebanon-demo": (PAST, budget("south-lebanon-demo"))}
        self.buildings = [SimpleNamespace(h3_r8=INSIDE, release_at=PAST, g=SQUARE, properties=building(f"b{i}", "c"))
                          for i in range(5)]
        self.buildings += [SimpleNamespace(h3_r8=INSIDE, release_at=FUTURE, g=SQUARE, properties=building("held", "c")),
                           SimpleNamespace(h3_r8=FAR, release_at=PAST, g=SQUARE, properties=building("far", "c"))]

    def _execute(self, sql, p=None):
        sql, p = " ".join(str(sql).split()), p or {}
        rows = []
        if "FROM agent_runs" in sql:
            rows = [SimpleNamespace(generated_at=PAST, counts={})] if self.loaded else []
        elif "FROM agent_incidents WHERE incident_id" in sql:
            rows = [i for i in self.incidents if i.incident_id == p["i"]]
        elif "FROM agent_incidents" in sql:
            rows = list(self.incidents)
        elif "FROM agent_recommendations" in sql:
            rows = [(self.recs[(p["i"], p["r"])],)] if (p["i"], p["r"]) in self.recs else []
        elif "FROM agent_insights" in sql:
            rows = [({"text": "A second radar agrees in 1 of 2 neighbourhoods with radar damage candidates.",
                      "values": {"agreeing": 1, "with_candidates": 2}, "sources": ["NISAR"], "date": None},)]
        elif "FROM agent_budgets" in sql:
            b = self.budgets.get(p["a"])
            rows = [SimpleNamespace(release_at=b[0], record=b[1])] if b else []
        elif "FROM agent_buildings" in sql:
            rows = list(self.buildings)[: p["l"]]
        rows = copy.deepcopy(rows)
        return SimpleNamespace(first=lambda: rows[0] if rows else None, all=lambda: rows,
                               scalar=lambda: rows[0][0] if rows else None, rowcount=1)

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
             for r in ("analyst", "officer", "admin")}
    users["narrow"] = {"password_hash": hash_password(PW), "role": "officer", "area_scopes": [INSIDE]}
    monkeypatch.setenv("DEMO_SYNTHETIC", "false")
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", json.dumps(users))
    get_settings.cache_clear()
    store = AgentDB()
    monkeypatch.setattr(radar, "engine", lambda: store)
    yield store
    get_settings.cache_clear()


def login(user):
    c = TestClient(app)
    assert c.post("/api/v1/session", json={"username": user, "password": PW}).status_code == 200
    return c


def test_logged_out_and_not_loaded(db):
    anon = TestClient(app)
    for path in ("/incidents", "/incidents/i1", f"/areas/{INSIDE}/budget", "/buildings?bbox=35.4,33.2,35.6,33.3"):
        assert anon.get("/api/v1" + path).status_code == 401
    db.loaded = False
    c = login("analyst")
    for path in ("/incidents", "/incidents/i1", f"/areas/{INSIDE}/budget", "/buildings?bbox=35.4,33.2,35.6,33.3"):
        r = c.get("/api/v1" + path)
        assert r.status_code == 503 and r.json()["error"]["code"] == "UNAVAILABLE"


def test_incident_list_hold_scope_and_rank(db):
    r = login("analyst").get("/api/v1/incidents").json()
    validate("IncidentList", r)
    assert [i["incident_id"] for i in r["items"]] == ["i1", "i2"]      # held and out-of-box left out
    assert [i["rank"] for i in r["items"]] == [1, 2]
    narrow = login("narrow").get("/api/v1/incidents").json()
    assert [i["incident_id"] for i in narrow["items"]] == ["i1"]        # only the user's area
    assert login("analyst").get("/api/v1/incidents?limit=0").status_code == 422
    page = login("analyst").get("/api/v1/incidents?limit=1").json()
    assert len(page["items"]) == 1 and page["next_cursor"] == "1"


def test_incident_detail_by_role(db):
    analyst = login("analyst").get("/api/v1/incidents/i1").json()
    validate("IncidentDetail", analyst)
    assert "evacuation" not in [o["playbook"] for o in analyst["recommendation"]["options"]]
    officer = login("officer").get("/api/v1/incidents/i1").json()
    assert "evacuation" in [o["playbook"] for o in officer["recommendation"]["options"]]
    admin = login("admin").get("/api/v1/incidents/i1").json()
    assert admin["recommendation"] == officer["recommendation"]          # admin reads the coordinator version
    assert analyst["insights"] and login("narrow").get("/api/v1/incidents/i1").json()["insights"] == []
    for iid in ("held", "far", "missing"):
        assert login("admin").get(f"/api/v1/incidents/{iid}").status_code == 404  # admin is not a bypass


def test_budget_scope_and_hold(db):
    r = login("analyst").get(f"/api/v1/areas/{INSIDE}/budget")
    assert r.status_code == 200
    validate("Budget", r.json())
    assert login("analyst").get("/api/v1/areas/south-lebanon-demo/budget").json()["label"] == "Planning indication only"
    assert login("analyst").get(f"/api/v1/areas/{INSIDE2}/budget").status_code == 404   # held
    assert login("analyst").get(f"/api/v1/areas/{FAR}/budget").status_code == 403       # out of scope


def test_buildings_bbox_limits_and_no_residents(db):
    c = login("analyst")
    for bad in ("", "?bbox=1,2,3", "?bbox=36,33,35,34", "?bbox=35.0,33.0,36.0,33.6",
                "?bbox=35.4,33.2,35.5,33.3&limit=0"):
        assert c.get("/api/v1/buildings" + bad).status_code == 422
    r = c.get("/api/v1/buildings?bbox=35.45,33.25,35.55,33.32").json()
    validate("BuildingCollection", r)
    ids = [f["properties"]["building_id"] for f in r["features"]]
    assert ids == ["b0", "b1", "b2", "b3", "b4"] and not r["truncated"]   # held and out-of-box left out
    assert not any(k.startswith("resident") for f in r["features"] for k in f["properties"])
    assert r["fidelity"] == "Reconstruction from satellite data, not footage"
    small = c.get("/api/v1/buildings?bbox=35.45,33.25,35.55,33.32&limit=2").json()
    assert len(small["features"]) == 2 and small["truncated"]
