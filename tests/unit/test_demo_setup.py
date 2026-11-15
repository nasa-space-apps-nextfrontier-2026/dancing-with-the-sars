"""The demo setup runs every step in order and skips a step only when its private inputs are missing."""

from pathlib import Path

from scripts import demo_setup


def test_plan_order_and_offline():
    names = [s.name for s in demo_setup.plan()]
    assert names[0].startswith("Start PostGIS") and names[1] == "Migrate the database"
    assert names.index("Run the agents") < names.index("Load the agent outputs")
    assert names.index("Build the building table") < names.index("Run the agents")
    offline = demo_setup.plan(offline=True, docker=False)
    assert not any("--fires" in s.cmd for s in offline)
    assert not any(s.name.startswith(("Start PostGIS", "Run the worker")) for s in offline)


def test_steps_skip_only_for_missing_inputs(tmp_path: Path):
    steps = {s.name: s for s in demo_setup.plan(offline=True, docker=False)}
    assert steps["Migrate the database"].missing(tmp_path) == []
    assert "data/local/facilities.csv" in steps["Load the facilities"].missing(tmp_path)
    (tmp_path / "data/local").mkdir(parents=True)
    (tmp_path / "data/local/facilities.csv").write_text("x")
    (tmp_path / "data/local/boundaries.geojson").write_text("x")
    assert steps["Load the facilities"].missing(tmp_path) == []


def test_dry_run_runs_nothing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(demo_setup.subprocess, "call", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("ran")))
    assert demo_setup.main(["--dry-run", "--no-docker", "--offline"]) == 0
    out = capsys.readouterr().out
    assert "Migrate the database" in out and "skipped (missing" in out
