"""Live refresh jobs with fakes: no network, no database."""

import csv
import datetime as dt
import gzip

from worker import live

FIELDS = ["date", "satellite", "cell", "mean_radiance", "n_pixels", "n_clear"]

def write_history(path, rows):
    with gzip.open(path, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        w.writerows(rows)

def read_dates(path):
    with gzip.open(path, "rt", newline="") as f:
        return sorted({r["date"] for r in csv.DictReader(f)})

def fake_store(calls):
    def _store(engine, source_id, alerts, acquired, detail):
        calls.append((source_id, alerts, acquired, detail))
    return _store

def test_refresh_without_token_is_unavailable(tmp_path, monkeypatch):
    monkeypatch.delenv("EARTHDATA_TOKEN", raising=False)
    monkeypatch.delenv("BM_TOKEN_FILE", raising=False)
    out = live.refresh_history(str(tmp_path / "h.csv.gz"))
    assert out["status"] == "unavailable"

def test_refresh_downloads_only_new_nights_and_merges(tmp_path, monkeypatch):
    hist = tmp_path / "h.csv.gz"
    write_history(hist, [["2026-11-10", "NOAA-20", "c1", "5.0", "4", "4"],
                         ["2026-11-12", "NOAA-20", "c1", "4.0", "4", "4"]])
    monkeypatch.setenv("EARTHDATA_TOKEN", "x")
    monkeypatch.setenv("BM_WORK", str(tmp_path / "work"))
    asked = {}

    def builder(days, token, work, out):
        asked["days"] = days
        write_history(out, [["2026-11-12", "NOAA-20", "c1", "4.5", "4", "4"],
                            ["2026-11-14", "NOAA-20", "c1", "0.5", "4", "4"]])

    res = live.refresh_history(str(hist), today=dt.date(2026, 11, 15), builder=builder)
    assert asked["days"] == 4                     # from the last night (12 Nov) to today
    assert res["status"] == "ok" and res["new_nights"] == 2 and res["last_night"] == "2026-11-14"
    assert read_dates(hist) == ["2026-11-10", "2026-11-12", "2026-11-14"]
    with gzip.open(hist, "rt") as f:
        rows = [r for r in csv.DictReader(f) if r["date"] == "2026-11-12"]
    assert len(rows) == 1 and rows[0]["mean_radiance"] == "4.5"   # the newer download wins

def test_refresh_is_capped_for_an_old_or_missing_history(tmp_path, monkeypatch):
    monkeypatch.setenv("EARTHDATA_TOKEN", "x")
    monkeypatch.setenv("BM_WORK", str(tmp_path / "work"))
    asked = {}
    live.refresh_history(str(tmp_path / "none.csv.gz"), today=dt.date(2026, 11, 15),
                         builder=lambda d, *a: asked.setdefault("days", d))
    assert asked["days"] == live.MAX_REFRESH_DAYS

def test_nightlights_failure_keeps_running_power_loss(monkeypatch):
    failures = []
    monkeypatch.setattr(live, "record_failure", lambda e, s, x: failures.append(s))

    def boom(path):
        raise OSError("LAADS down")

    out = live.run_nightlights(object(), "missing.csv.gz", refresher=boom)
    assert failures == [live.HISTORY_SOURCE]
    assert out[0]["status"] == "failed" and out[1]["status"] == "unavailable"

def feature(date, track=151, frame=72, direction="DESCENDING"):
    return {"properties": {"sceneName": f"S{date}", "processingLevel": "GCOV",
                           "collectionName": "NISAR_L2_GCOV_V1", "pathNumber": track, "frameNumber": frame,
                           "flightDirection": direction, "startTime": f"{date}T03:00:00Z"}}

def test_radar_check_records_new_passes(monkeypatch):
    calls = []
    monkeypatch.setattr(live, "store", fake_store(calls))
    monkeypatch.setenv("NISAR_LOADED_THROUGH", "2026-11-03")
    feats = [feature("2026-11-03"), feature("2026-11-15"), feature("2026-11-20", track=172)]
    out = live.check_radar(object(), search=lambda cfg, product: feats)
    assert out["new_passes"] == ["2026-11-15"]            # other tracks are ignored
    assert "new pass available: 2026-11-15" in out["action"]
    assert calls[0][0] == live.RADAR_SOURCE and calls[0][1] == []

def test_radar_check_up_to_date_and_failure(monkeypatch):
    calls, failures = [], []
    monkeypatch.setattr(live, "store", fake_store(calls))
    monkeypatch.setattr(live, "record_failure", lambda e, s, x: failures.append(s))
    monkeypatch.setenv("NISAR_LOADED_THROUGH", "2026-11-03")
    assert live.check_radar(object(), search=lambda c, p: [feature("2026-11-03")])["action"] == "up to date"

    def down(cfg, product):
        raise TimeoutError("ASF")

    assert live.check_radar(object(), search=down)["status"] == "failed" and failures == [live.RADAR_SOURCE]

def test_agents_run_in_order_and_at_most_hourly(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data/private/nisar/model").mkdir(parents=True)
    (tmp_path / "data/local").mkdir(parents=True)
    (tmp_path / live.DAMAGE).write_text("x")
    (tmp_path / live.TABLE).write_text("x")
    monkeypatch.setattr(live, "_last_agents_run", 0.0)
    ran = []
    t = [1000.0]
    out = live.refresh_agents(run=lambda cmd: ran.append(cmd[2]) or 0, clock=lambda: t[0])
    assert out["status"] == "ok" and ran == ["worker.main", "worker.main", "scripts.load_agent_outputs"]
    t[0] += 60
    assert live.refresh_agents(run=lambda cmd: 0, clock=lambda: t[0])["status"] == "skipped"
    assert live.refresh_agents(force=True, run=lambda cmd: 0, clock=lambda: t[0])["status"] == "ok"

def test_agents_unavailable_without_inputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(live, "_last_agents_run", 0.0)
    assert live.refresh_agents(run=lambda cmd: 0)["status"] == "unavailable"

def test_changed_detects_new_data_only():
    seen = {}
    assert live.changed({"source": "f", "status": "ok", "alerts": 2}, seen)
    assert not live.changed({"source": "f", "status": "ok", "alerts": 2}, seen)
    assert live.changed({"source": "f", "status": "ok", "alerts": 3}, seen)
    assert not live.changed({"source": "f", "status": "failed"}, seen)
