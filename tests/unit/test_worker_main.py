"""worker/main.py keeps both entry points (Thanoban's review): one test per mode.

--publish (PR #21: ML outputs) and --agents (U-06: agent outputs) must both reach their function
with the right arguments; --once stays the no-network scaffold run."""

import json
import runpy
import sys

import pytest


def run(monkeypatch, capsys, *args):
    monkeypatch.setattr(sys, "argv", ["worker.main", *args])
    runpy.run_module("worker.main", run_name="__main__")
    return capsys.readouterr().out


def test_publish_mode(monkeypatch, capsys):
    import worker.publish as pub

    seen = {}
    monkeypatch.setattr(pub, "publish", lambda *a: seen.setdefault("args", a) and {"ok": "publish"})
    out = run(monkeypatch, capsys, "--publish", "--damage", "d.parquet", "--history", "h.csv.gz", "--fires",
              "--out", "out")
    assert seen["args"] == ("out", "d.parquet", "h.csv.gz", True)
    assert json.loads(out) == {"ok": "publish"}


def test_agents_mode(monkeypatch, capsys):
    import worker.agents.publish_agents as pa

    seen = {}

    def fake(out, table, population_path=None):
        seen.update(out=out, table=table, population=population_path)
        return {"ok": "agents"}

    monkeypatch.setattr(pa, "publish_agents", fake)
    out = run(monkeypatch, capsys, "--agents", "--table", "t.parquet", "--population", "p.csv.gz", "--out", "out")
    assert seen == {"out": "out", "table": "t.parquet", "population": "p.csv.gz"}
    assert json.loads(out) == {"ok": "agents"}


def test_once_mode_and_no_mode(monkeypatch, capsys):
    out = json.loads(run(monkeypatch, capsys, "--once"))
    assert out["synthetic"] is True and out["status"] == "unavailable"
    with pytest.raises(SystemExit):
        run(monkeypatch, capsys)
