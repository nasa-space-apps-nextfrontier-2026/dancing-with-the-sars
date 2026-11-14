"""Real-data area, source, review and admin routes against an in-memory database stand-in.

Pins: capabilities per role; login rate limit; failed logins audited as "anonymous"; denials
audited; role changes end old sessions and apply at the next sign-in; sign-in fails closed when
the store is down; reviews only on alerts the reviewer may see; idempotent job retry; held values
hidden; validation and facilities reported as unavailable, never as an empty all-clear.
All values here are synthetic test numbers.
"""

import copy
import datetime as dt
import json
from pathlib import Path
from types import SimpleNamespace

import h3
import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from sqlalchemy.exc import OperationalError

from backend.app.api import radar
from backend.app.core.config import get_settings
from backend.app.core.permissions import capabilities
from backend.app.core.security import Identity, hash_password
from backend.app.main import app
from backend.app.services import admin_real, radar_real
from worker import jobs

SPEC = json.loads(Path("docs/contracts/openapi.yaml").read_text(encoding="utf-8"))
INSIDE = h3.latlng_to_cell(33.3, 35.5, 8)
NEAR = h3.latlng_to_cell(33.5, 35.9, 8)
FAR = h3.latlng_to_cell(10.0, 10.0, 8)
PAST = dt.datetime(2026, 7, 21, tzinfo=dt.UTC)
FUTURE = dt.datetime(2999, 1, 1, tzinfo=dt.UTC)
PW = "test-only-password"


def validate(name, obj):
    Draft202012Validator(
        SPEC["components"]["schemas"][name] | {"components": SPEC["components"]}
    ).validate(obj)


def alert(alert_id, area, release=PAST, kind="fire_detected"):
    return SimpleNamespace(
        alert_id=alert_id,
        area_id=area,
        type=kind,
        title="Fire detected",
        detected_at=PAST,
        processed_at=PAST,
        satellite="NOAA-20",
        product="VIIRS NRT",
        label="Observed",
        source=["firms"],
        lineage_ids=["snap"],
        independent_source_count=1,
        release_at=release,
        safety_tag="restricted_aggregate",
        review_status="unreviewed",
        detail={"warning": "No cause."},
    )


def value(
    vid, date, release="2026-07-21T00:00:00Z", metric="radar_candidate_change_cells"
):
    return {
        "synthetic": True,
        "value_id": vid,
        "area_id": INSIDE,
        "metric": metric,
        "low": 1,
        "high": 2,
        "unit": "cells",
        "label": "Observed",
        "source": ["nisar-gcov-beta-151d72"],
        "date": date,
        "safety_tag": "restricted_aggregate",
        "lineage_ids": ["run-a"],
        "processing_run_id": "run-a",
        "processing_version": "t",
        "confidence": None,
        "acquired_at": release,
        "processed_at": release,
        "release_at": release,
        "freshness": "Stale",
        "cached": True,
        "limitations": [],
    }


class StoreEngine:
    """Just enough of the tables for these routes."""

    def __init__(self, down=False, fail_audit=False):
        self.down = down
        self.fail_audit = fail_audit
        self.audit, self.access, self.job_runs, self.reviews = [], {}, {}, []
        self.alerts = {
            a.alert_id: a
            for a in (
                alert("a-ok", INSIDE),
                alert("a-held", INSIDE, FUTURE),
                alert("a-far", FAR),
                alert("a-power", INSIDE, kind="possible_power_loss"),
            )
        }
        self.values = [
            value("v1", "2026-07-18"),
            value("v2", "2026-09-01"),
            value("v-held", "2026-10-01", release="2999-01-01T00:00:00Z"),
            value("v-other", "2026-07-18", metric="other"),
        ]

    def _execute(self, sql, p=None):
        sql, p = " ".join(str(sql).split()), p or {}
        if self.down:
            raise OperationalError(sql, p, Exception("down"))
        rows, count = [], 1
        if sql.startswith("INSERT INTO audit_events"):
            if self.fail_audit:
                raise OperationalError(sql, p, Exception("audit down"))
            self.audit.append(
                SimpleNamespace(
                    actor_id=p["a"],
                    action=p["ac"],
                    resource_type=p["r"],
                    outcome=p["o"],
                    at=p["t"],
                )
            )
        elif "FROM audit_events" in sql:
            rows = sorted(
                (
                    r
                    for r in self.audit
                    if r.at >= p["f"] and (p["t"] is None or r.at <= p["t"])
                ),
                key=lambda r: r.at,
                reverse=True,
            )[p["o"] : p["o"] + p["l"]]
        elif "FROM user_access" in sql:
            rows = [self.access[p["u"]]] if p["u"] in self.access else []
        elif sql.startswith("INSERT INTO user_access"):
            self.access[p["u"]] = SimpleNamespace(
                role=p["r"], area_scopes=json.loads(p["s"])
            )
        elif sql.startswith("INSERT INTO job_runs"):
            count = 0 if p["k"] in self.job_runs else 1
            self.job_runs.setdefault(
                p["k"], SimpleNamespace(job_id=p["j"], status="running")
            )
        elif "FROM job_runs" in sql:
            rows = [self.job_runs[p["k"]]]
        elif sql.startswith("UPDATE job_runs"):
            self.job_runs[p["k"]].status = p["s"]
        elif "FROM source_status" in sql:
            rows = []
        elif sql.startswith("SELECT * FROM alerts WHERE alert_id"):
            rows = [self.alerts[p["a"]]] if p["a"] in self.alerts else []
        elif sql.startswith("INSERT INTO alert_reviews"):
            self.reviews.append(p)
        elif sql.startswith("UPDATE alerts SET review_status"):
            self.alerts[p["a"]].review_status = p["s"]
        elif "FROM alerts WHERE area_id" in sql:
            rows = [a for a in self.alerts.values() if a.area_id == p["a"]]
        elif "FROM areas WHERE resolution = 8" in sql:
            areas = sorted([INSIDE, NEAR, FAR])
            if {"w", "s", "e", "n"} <= p.keys():
                areas = [
                    a
                    for a in areas
                    if p["s"] <= h3.cell_to_latlng(a)[0] <= p["n"]
                    and p["w"] <= h3.cell_to_latlng(a)[1] <= p["e"]
                ]
            rows = [(a,) for a in areas]
        elif sql.startswith("SELECT 1 FROM areas"):
            rows = [(1,)] if p["a"] in (INSIDE, NEAR, FAR) else []
        elif "FROM metric_values WHERE area_id" in sql:
            rows = [(v,) for v in self.values] if p["a"] == INSIDE else []
        return SimpleNamespace(
            first=lambda: rows[0] if rows else None,
            all=lambda: list(rows),
            scalar=lambda: rows[0][0] if rows else None,
            rowcount=count,
        )

    def _ctx(self):
        engine = self

        class Ctx:
            def __enter__(self):
                self.snapshot = copy.deepcopy(
                    (engine.audit, engine.access, engine.job_runs, engine.reviews, engine.alerts)
                )
                return SimpleNamespace(execute=engine._execute)

            def __exit__(self, exc_type, _exc, _tb):
                if exc_type is not None:
                    (
                        engine.audit,
                        engine.access,
                        engine.job_runs,
                        engine.reviews,
                        engine.alerts,
                    ) = self.snapshot
                return False

        return Ctx()

    connect = begin = _ctx


@pytest.fixture
def db(tmp_path, monkeypatch):
    (tmp_path / "local" / "radar_contract").mkdir(parents=True)
    (tmp_path / "local" / "radar_contract" / "sources.json").write_text(
        json.dumps(
            [{"source_id": "s1", "name": "one"}, {"source_id": "s2", "name": "two"}]
        )
    )
    users = {
        r: {
            "password_hash": hash_password(PW),
            "role": r,
            "area_scopes": ["south-lebanon-demo"],
        }
        for r in ("analyst", "officer", "coordinator", "admin")
    }
    monkeypatch.setenv("DEMO_SYNTHETIC", "false")
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("CIVISAR_DEMO_USERS_JSON", json.dumps(users))
    get_settings.cache_clear()
    radar_real._catalogue.cache_clear()
    store = StoreEngine()
    monkeypatch.setattr(radar, "engine", lambda: store)
    yield store
    get_settings.cache_clear()


def login(role, password=PW):
    c = TestClient(app)
    r = c.post("/api/v1/session", json={"username": role, "password": password})
    if r.status_code == 200:
        c.headers["X-CSRF-Token"] = r.json()["csrf_token"]
    c.last = r
    return c


# --- sessions, roles, audit -------------------------------------------------------------------


def test_roles_carry_capabilities(db):
    r = login("analyst").get("/api/v1/roles").json()
    validate("Roles", r)
    assert (
        "review_alerts" in r["capabilities"] and "manage_roles" not in r["capabilities"]
    )
    assert (
        set(capabilities("analyst"))
        < set(capabilities("officer"))
        < set(capabilities("admin"))
    )
    assert r["synthetic"] is False


def test_login_rate_limit_and_anonymous_failures(db):
    for _ in range(5):
        assert login("analyst", "wrong-password-x").last.status_code == 401
    blocked = login("analyst").last  # even the right password waits
    assert blocked.status_code == 429 and int(blocked.headers["Retry-After"]) > 0
    failures = [a for a in db.audit if a.action == "login"]
    assert [a.outcome for a in failures] == ["failure"] * 5 + ["blocked"]
    assert {a.actor_id for a in failures} == {"anonymous"}  # never the typed name
    assert login("officer").last.status_code == 200  # other users are not affected


def test_denials_are_audited_without_detail(db):
    assert login("analyst").get("/api/v1/admin/audit").status_code == 403
    denied = [a for a in db.audit if a.action == "access_denied"]
    assert len(denied) == 1 and (denied[0].actor_id, denied[0].resource_type) == (
        "analyst",
        "admin",
    )


def test_audit_list_is_admin_only_and_30_days(db):
    db.audit.append(
        SimpleNamespace(
            actor_id="old",
            action="login",
            resource_type="session",
            outcome="success",
            at=dt.datetime.now(dt.UTC) - dt.timedelta(days=40),
        )
    )
    r = login("admin").get("/api/v1/admin/audit")
    assert r.status_code == 200
    validate("AuditList", r.json())
    assert "old" not in {i["actor_id"] for i in r.json()["items"]}
    assert login("admin").get("/api/v1/admin/audit?from=yesterday").status_code == 422


def test_role_change_ends_old_sessions_and_applies_at_next_login(db):
    analyst, admin = login("analyst"), login("admin")
    body = {
        "role": "officer",
        "area_scopes": ["south-lebanon-demo"],
        "reason": "Assigned to roads team",
    }
    assert (
        admin.patch(
            "/api/v1/admin/users/analyst/roles",
            json=body,
            headers={"X-CSRF-Token": "wrong"},
        ).status_code
        == 403
    )
    assert (
        analyst.patch("/api/v1/admin/users/analyst/roles", json=body).status_code == 403
    )
    assert (
        admin.patch(
            "/api/v1/admin/users/analyst/roles", json=body | {"reason": " "}
        ).status_code
        == 422
    )
    assert (
        admin.patch(
            "/api/v1/admin/users/analyst/roles", json=body | {"role": "root"}
        ).status_code
        == 422
    )
    assert admin.patch("/api/v1/admin/users/nobody/roles", json=body).status_code == 404
    r = admin.patch("/api/v1/admin/users/analyst/roles", json=body)
    assert r.status_code == 200
    validate("Roles", r.json())
    assert (
        analyst.get("/api/v1/session").status_code == 401
    )  # old role does not live on
    assert login("analyst").get("/api/v1/session").json()["role"] == "officer"
    assert (
        admin.patch("/api/v1/admin/users/admin/roles", json=body).status_code == 409
    )  # no self-lockout
    assert any(a.action == "role_change" and a.outcome == "success" for a in db.audit)


def test_privileged_mutations_fail_closed_when_audit_insert_fails(db):
    analyst, admin = login("analyst"), login("admin")
    db.fail_audit = True

    role = admin.patch(
        "/api/v1/admin/users/analyst/roles",
        json={
            "role": "officer",
            "area_scopes": ["south-lebanon-demo"],
            "reason": "Audit failure test",
        },
    )
    assert role.status_code == 503
    assert "analyst" not in db.access
    assert analyst.get("/api/v1/session").status_code == 200

    review = analyst.post(
        "/api/v1/alerts/a-ok/reviews",
        json={"status": "reviewed", "note": "Audit failure test"},
    )
    assert review.status_code == 503
    assert db.reviews == [] and db.alerts["a-ok"].review_status == "unreviewed"


def test_job_does_not_start_when_durable_audit_fails(db, monkeypatch):
    admin = login("admin")
    ran = []
    monkeypatch.setattr(
        admin_real, "_jobs", lambda: {"fires": lambda _e: ran.append(True) or {"status": "ok"}}
    )
    db.fail_audit = True
    response = admin.post(
        "/api/v1/admin/jobs/fires/retry", json={"idempotency_key": "audit-fails"}
    )
    assert response.status_code == 503
    assert ran == [] and "audit-fails" not in db.job_runs


def test_login_fails_closed_when_store_is_down(db, monkeypatch):
    monkeypatch.setattr(radar, "engine", lambda: StoreEngine(down=True))
    assert login("analyst").last.status_code == 503


# --- alert reviews -----------------------------------------------------------------------------


def test_review_only_visible_alerts_with_known_status(db):
    c = login("analyst")
    ok = {"status": "needs_follow_up", "note": "Ask the field team"}
    r = c.post("/api/v1/alerts/a-ok/reviews", json=ok)
    assert r.status_code == 200
    validate("Review", r.json())
    assert db.alerts["a-ok"].review_status == "needs_follow_up"
    assert c.get("/api/v1/alerts/a-ok").json()["review_status"] == "needs_follow_up"
    assert c.post("/api/v1/alerts/a-held/reviews", json=ok).status_code == 404
    assert c.post("/api/v1/alerts/a-far/reviews", json=ok).status_code == 404
    assert (
        c.post(
            "/api/v1/alerts/a-ok/reviews", json=ok | {"status": "confirmed"}
        ).status_code
        == 422
    )
    assert (
        c.post(
            "/api/v1/alerts/a-ok/reviews", json=ok | {"note": "x" * 1001}
        ).status_code
        == 422
    )
    assert (
        c.post(
            "/api/v1/alerts/a-ok/reviews", json=ok, headers={"X-CSRF-Token": "no"}
        ).status_code
        == 403
    )


# --- jobs ----------------------------------------------------------------------------------------


def test_job_retry_is_idempotent(db, monkeypatch):
    runs = []
    monkeypatch.setattr(
        admin_real,
        "_jobs",
        lambda: {
            "fires": lambda e: runs.append(1) or {"status": "ok"},
            "night_lights": lambda e: {"status": "unavailable"},
        },
    )
    admin = login("admin")
    r = admin.post("/api/v1/admin/jobs/fires/retry", json={"idempotency_key": "k1"})
    assert r.status_code == 200 and r.json()["status"] == "succeeded"
    validate("Job", r.json())
    assert (
        admin.post(
            "/api/v1/admin/jobs/fires/retry", json={"idempotency_key": "k1"}
        ).json()["status"]
        == "succeeded"
    )
    assert runs == [1]  # same key, one run
    assert (
        admin.post(
            "/api/v1/admin/jobs/night_lights/retry", json={"idempotency_key": "k1"}
        ).status_code
        == 409
    )
    assert (
        admin.post(
            "/api/v1/admin/jobs/night_lights/retry", json={"idempotency_key": "k2"}
        ).json()["status"]
        == "unavailable"
    )
    assert (
        admin.post(
            "/api/v1/admin/jobs/reboot/retry", json={"idempotency_key": "k3"}
        ).status_code
        == 404
    )
    assert admin.post("/api/v1/admin/jobs/fires/retry", json={}).status_code == 422
    assert (
        login("analyst")
        .post("/api/v1/admin/jobs/fires/retry", json={"idempotency_key": "k4"})
        .status_code
        == 403
    )


def test_failed_job_is_persisted_as_failed_not_running(db):
    result = admin_real.retry_job(
        db,
        Identity("admin", "admin", ("south-lebanon-demo",)),
        "fires",
        "job-raises",
        jobs={"fires": lambda _engine: (_ for _ in ()).throw(RuntimeError("boom"))},
        request_id="request-test",
    )
    assert result["status"] == "failed"
    assert db.job_runs["job-raises"].status == "failed"
    assert any(a.action == "job_retry" and a.outcome == "started" for a in db.audit)


def test_prune_job_reports_counts_and_failures():
    from tests.security.conftest import NullEngine

    e = NullEngine()
    assert (
        jobs.prune(e)["status"] == "ok"
        and sum("DELETE" in sql for sql, _ in e.calls) == 2
    )
    assert jobs.prune(StoreEngine(down=True))["status"] == "failed"


# --- areas and sources -----------------------------------------------------------------------------


def test_area_list_is_scoped_r8_with_bbox(db):
    c = login("analyst")
    r = c.get("/api/v1/areas").json()
    validate("AreaList", r)
    assert {i["area_id"] for i in r["items"]} == {
        INSIDE,
        NEAR,
    }  # FAR is outside the scope
    lat, lon = h3.cell_to_latlng(INSIDE)
    r = c.get(
        f"/api/v1/areas?bbox={lon - 0.01},{lat - 0.01},{lon + 0.01},{lat + 0.01}"
    ).json()
    assert [i["area_id"] for i in r["items"]] == [INSIDE]
    assert c.get("/api/v1/areas?bbox=1,2,3").status_code == 422
    assert c.get("/api/v1/areas?bbox=36,33,35,34").status_code == 422
    assert c.get("/api/v1/areas?limit=0").status_code == 422
    page = c.get("/api/v1/areas?limit=1").json()
    assert len(page["items"]) == 1 and page["next_cursor"] == "1"


def test_area_values_hide_held_and_filter(db):
    c = login("analyst")
    r = c.get(f"/api/v1/areas/{INSIDE}/values").json()
    validate("MetricList", r)
    assert [v["value_id"] for v in r["items"]] == ["v1", "v2", "v-other"]
    metric = c.get(
        f"/api/v1/areas/{INSIDE}/values?metric=radar_candidate_change_cells&as_of=2026-08-01"
    )
    assert [v["value_id"] for v in metric.json()["items"]] == ["v1"]
    db.values.append(value("v-late-release", "2026-07-18", release="2026-09-01T00:00:00Z"))
    historical = c.get(
        f"/api/v1/areas/{INSIDE}/values?as_of=2026-08-01T00:00:00Z"
    ).json()
    assert "v-late-release" not in {v["value_id"] for v in historical["items"]}
    assert c.get(f"/api/v1/areas/{INSIDE}/values?as_of=soon").status_code == 422
    assert c.get(f"/api/v1/areas/{FAR}/values").status_code == 403
    assert c.get("/api/v1/areas/8b0000000000000/values").status_code in (403, 404)


def test_services_validation_facilities_people(db):
    c = login("analyst")
    s = c.get(f"/api/v1/areas/{INSIDE}/services").json()
    validate("ServiceList", s)
    power = next(x for x in s["items"] if x["type"] == "power")
    assert power["status"] == "Possible loss" and power["date"] is not None
    historical = c.get(
        f"/api/v1/areas/{INSIDE}/services?as_of=2026-07-20T00:00:00Z"
    ).json()
    assert next(x for x in historical["items"] if x["type"] == "power")["status"] == "Unknown"
    assert {x["status"] for x in s["items"] if x["type"] != "power"} == {"Unknown"}
    v = c.get(f"/api/v1/areas/{INSIDE}/validation").json()
    validate("ValidationList", v)
    assert v["items"] == [] and v["availability"].startswith("unavailable")
    assert (
        c.get(f"/api/v1/areas/{INSIDE}/facilities").status_code == 503
    )  # not an empty all-clear
    assert (
        c.get(f"/api/v1/areas/{INSIDE}/people").status_code == 503
    )  # no population file


def test_sources_are_public_and_paged(db):
    c = TestClient(app)
    r = c.get("/api/v1/sources?limit=1").json()
    assert [s["source_id"] for s in r["items"]] == ["s1"] and r["next_cursor"] == "1"
    assert c.get("/api/v1/sources/s2").json()["name"] == "two"
    assert c.get("/api/v1/sources/zzz").status_code == 404


def test_missing_operational_datasets_are_honestly_unavailable(db):
    officer = login("officer")
    assert officer.post("/api/v1/routes", json={}).status_code == 503
    assert officer.post("/api/v1/closures", json={}).status_code == 503
    coordinator = login("coordinator")
    assert coordinator.get("/api/v1/shelters").status_code == 503
    assert coordinator.post("/api/v1/shelters/capacity", json={}).status_code == 503


def test_real_public_map_is_suppressed_without_claiming_synthetic_data(db):
    payload = TestClient(app).get("/api/v1/public/map").json()
    assert payload["synthetic"] is False
    assert payload["suppressed"] is True and payload["layers"] == []
