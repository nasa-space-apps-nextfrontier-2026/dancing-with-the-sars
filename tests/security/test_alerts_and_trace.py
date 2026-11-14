"""Real-data alerts, status and trace: pure rules (no database).

The database round trip was smoke-tested live (see docs/31_BACKEND_REAL_DATA.md); here we pin
the safety rules: no coordinates, no cause, fire wording, freshness bands, visibility.
"""

import datetime as dt
from types import SimpleNamespace

import h3

from backend.app.core.security import Identity
from backend.app.services import live_real
from worker import jobs
from worker.services.fires import FireEvent

INSIDE = h3.latlng_to_cell(33.3, 35.5, 8)
OUTSIDE = h3.latlng_to_cell(10.0, 10.0, 8)


def event(lat=33.3, lon=35.5, start="2026-11-12T23:11:00+00:00"):
    return FireEvent("fire_detected", start, start, lat, lon, 2, ("NOAA-20",), "nominal")


def test_fire_alert_is_neighbourhood_level_without_cause():
    a = jobs.fire_alert(event(), dt.datetime(2026, 11, 13, tzinfo=dt.UTC), "snap")
    assert a["area_id"] == INSIDE and h3.get_resolution(a["area_id"]) == 8
    assert not {"lat", "lon", "latitude", "longitude"} & set(a) and "lat" not in a["detail"]
    assert a["title"] == "Fire detected" and "cause" in a["detail"]["warning"]
    assert a["alert_id"] == jobs.fire_alert(event(), dt.datetime(2030, 1, 1, tzinfo=dt.UTC), "x")["alert_id"]


def test_power_alert_wording_and_corroboration():
    e = {"area": h3.cell_to_children(INSIDE, 9)[0], "time": "2026-11-10", "source": "Black Marble",
         "confidence": "high", "corroborated": True, "satellites": ["NOAA-20", "NOAA-21"], "reasons": []}
    a = jobs.power_alert(e, dt.datetime(2026, 11, 13, tzinfo=dt.UTC), "snap")
    assert a["title"] == "Possible power loss" and a["label"] == "Corroborated" and a["area_id"] == INSIDE
    assert "blackout" in a["detail"]["warning"].lower()  # only in the "not a blackout claim" sentence
    assert jobs.power_alert(e | {"area": "junk"}, dt.datetime(2026, 11, 13, tzinfo=dt.UTC), "s") is None


def test_freshness_bands():
    now = dt.datetime(2026, 11, 14, 12, tzinfo=dt.UTC)
    f = lambda m: live_real.freshness(now - dt.timedelta(minutes=m), live_real.FRESH, live_real.AGING, now)
    assert (f(30), f(90), f(300)) == ("Fresh", "Aging", "Stale")
    assert live_real.freshness(None, live_real.FRESH, live_real.AGING, now) == "Stale"


def test_alert_visibility_follows_scope_release_and_role():
    row = SimpleNamespace(area_id=INSIDE, release_at=dt.datetime(2026, 1, 1, tzinfo=dt.UTC))
    held = SimpleNamespace(area_id=INSIDE, release_at=dt.datetime(2999, 1, 1, tzinfo=dt.UTC))
    far = SimpleNamespace(area_id=OUTSIDE, release_at=dt.datetime(2026, 1, 1, tzinfo=dt.UTC))
    analyst = Identity("a", "analyst", ("south-lebanon-demo",))
    admin = Identity("b", "admin", ())
    assert live_real._visible(row, analyst)
    assert not live_real._visible(held, analyst) and live_real._visible(held, admin)
    assert not live_real._visible(far, analyst)
    assert not live_real._visible(row, None)


def test_failed_fetch_keeps_data_and_reports_failure():
    calls = []

    class Eng:
        def begin(self):
            class Ctx:
                def __enter__(self_inner):
                    return SimpleNamespace(execute=lambda *a, **k: calls.append(a))

                def __exit__(self_inner, *a):
                    return False
            return Ctx()

    def boom():
        raise TimeoutError("feed down")

    out = jobs.run_fires(Eng(), current_events=boom)
    assert out["status"] == "failed" and len(calls) == 1  # only the failure is recorded
