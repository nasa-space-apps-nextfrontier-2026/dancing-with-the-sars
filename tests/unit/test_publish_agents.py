"""U-06 publish step on a tiny synthetic dataset: files written, release times carried for the 72-hour
gate, role-specific recommendations, no residents per building. All values are made up."""

import json
from datetime import UTC, datetime

import pytest

pd = pytest.importorskip("pandas")
pa = pytest.importorskip("pyarrow")
shapely = pytest.importorskip("shapely")
pytest.importorskip("h3")

import pyarrow.parquet as pq

from worker.agents.publish_agents import publish_agents

NOW = datetime(2026, 11, 14, 12, tzinfo=UTC)


def setup(tmp_path):
    rows = []
    for i, (cell, cls, label) in enumerate([("c1", "destroyed_or_severe_candidate", "corroborated"),
                                            ("c1", "destroyed_or_severe_candidate", "corroborated"),
                                            ("c2", "no_detected_change", "none")]):
        rows.append({"building_id": f"b{i}", "h3_r9": cell, "h3_r8": "area-1", "footprint_m2": 100.0,
                     "height_low_m": 3.0, "height_mid_m": 6.0, "height_high_m": 9.0, "height_source": "ghsl",
                     "floors_low": 1, "floors_high": 3, "use": "residential", "use_ghsl": "residential",
                     "facility_flag": False, "osm_condition_tag": None, "residential": True,
                     "residential_floor_m2": 200.0, "residents_low": 5, "residents_high": 9,
                     "damage_class": cls, "evidence_label": label,
                     "second_sensor_agrees": True if cell == "c1" else None, "run_id": "run-a"})
    table = pd.DataFrame(rows)
    table["residents_low"] = table["residents_low"].astype("Int64")
    table["residents_high"] = table["residents_high"].astype("Int64")
    table["second_sensor_agrees"] = table["second_sensor_agrees"].astype("boolean")
    tpath, bpath = tmp_path / "table.parquet", tmp_path / "base.parquet"
    pq.write_table(pa.Table.from_pandas(table, preserve_index=False), tpath)
    box = shapely.box(35.5, 33.3, 35.5001, 33.3001)
    pq.write_table(pa.Table.from_pandas(pd.DataFrame({"building_id": ["b0", "b1", "b2"],
                                                      "geom": [shapely.to_wkb(box)] * 3})), bpath)
    out = tmp_path / "published"
    out.mkdir()
    (out / "damage.json").write_text(json.dumps({"release_at": "2026-07-21T00:00:00Z", "items": []}))
    (out / "alerts.json").write_text(json.dumps({"items": [
        {"alert_id": "fire-1", "area_id": "area-1", "type": "fire_detected", "independent_source_count": 2,
         "detected_at": "2026-11-14T10:00:00Z", "release_at": "2026-11-14T10:30:00Z",
         "review_status": "unreviewed"}]}))
    (out / "manifest.json").write_text(json.dumps({"sources": [
        {"id": "firms", "last_success_at": "2026-11-14T11:00:00Z", "failure": ""},
        {"id": "nisar-damage", "acquired_at": "2026-07-21T00:00:00Z", "last_success_at": "2026-11-14T00:00:00Z",
         "failure": ""}]}))
    return out, tpath, bpath


def test_publish_writes_contract_shaped_files(tmp_path):
    out, tpath, bpath = setup(tmp_path)
    m = publish_agents(out, tpath, bpath, now=NOW)
    assert m["incidents"] == 1 and m["building_files"] == 1 and m["buildings"] == 3
    inc = json.loads((out / "incidents.json").read_text())["items"][0]
    assert inc["incident_id"] == "fire-1" and inc["release_at"] == "2026-11-14T10:30:00Z"
    budget = json.loads((out / "budget.json").read_text())
    assert budget["whole_demo_box"]["label"] == "Planning indication only" and "area-1" in budget["areas"]
    assert budget["release_at"] == "2026-07-21T00:00:00Z"


def test_recommendations_follow_roles(tmp_path):
    out, tpath, bpath = setup(tmp_path)
    publish_agents(out, tpath, bpath, now=NOW)
    rec = json.loads((out / "recommendations.json").read_text())["by_role"]
    plays = {role: [o["playbook"] for o in rec[role]["fire-1"]["options"]] for role in rec}
    assert "evacuation" not in plays["analyst"] and "evacuation" in plays["officer"]
    assert any("shelter" in c.lower() for c in rec["coordinator"]["fire-1"]["checklist"])
    assert not any("shelter" in c.lower() for c in rec["officer"]["fire-1"]["checklist"])


def test_buildings_have_no_residents_and_cell_damage(tmp_path):
    out, tpath, bpath = setup(tmp_path)
    publish_agents(out, tpath, bpath, now=NOW)
    f = json.loads((out / "buildings" / "area-1.json").read_text())
    assert f["release_at"] == "2026-07-21T00:00:00Z"
    for feat in f["features"]:
        p = feat["properties"]
        assert not any(k.startswith("resident") for k in p)
        assert p["damage_tag"] == "From data (cell result)" and p["height_tag"] == "Inferred"
        assert feat["geometry"]["type"] == "Polygon"
    agrees = {feat["properties"]["building_id"]: feat["properties"]["second_sensor_agrees"] for feat in f["features"]}
    assert agrees == {"b0": True, "b1": True, "b2": None}
