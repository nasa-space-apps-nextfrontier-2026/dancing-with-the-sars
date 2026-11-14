import csv
import json
import random

import pytest

from worker.evaluation.events import from_csv, from_ucdp_json
from worker.evaluation.run_strike_tests import load_cells, main


def test_ucdp_json_keeps_dated_events_with_coordinates():
    payload = {"Result": [
        {"date_start": "2026-09-01 00:00:00.000", "latitude": 33.3, "longitude": 35.4},
        {"date_start": "2025-01-01 00:00:00.000", "latitude": 33.3, "longitude": 35.4},
        {"date_start": "2026-09-02 00:00:00.000", "latitude": None, "longitude": 35.4},
    ]}
    events = from_ucdp_json(payload, start="2026-06-01")
    assert len(events) == 1 and events[0].lat == 33.3


def test_csv_events_skip_bad_rows():
    lines = ["latitude,longitude,date_start", "33.3,35.4,2026-09-01", "x,y,2026-09-01", "33.4,35.5,2024-01-01"]
    assert len(from_csv(lines, start="2026-01-01")) == 1


def test_loader_accepts_the_real_damage_table_columns(tmp_path):
    table = tmp_path / "damage_cells.csv"
    rows = [
        "h3_r9,damage_class,evidence_label",
        "892db110033ffff,possible_candidate,observed",
        "892db110037ffff,no_detected_change,none",
        "892db11003bffff,unknown,unknown",
    ]
    table.write_text("\n".join(rows) + "\n", encoding="utf-8")
    h3 = pytest.importorskip("h3")
    cells = load_cells(str(table))
    assert [c.flagged for c in cells] == [True, False, False] and cells[0].district == "unknown"
    assert abs(cells[0].lat - h3.cell_to_latlng("892db110033ffff")[0]) < 1e-9


def test_runner_reports_enrichment_from_csv_files(tmp_path):
    rng = random.Random(3)
    table = tmp_path / "damage.csv"
    with open(table, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["h3_r9", "damage_class", "district", "lat", "lon"])
        for i in range(200):
            near = i < 100
            flagged = rng.random() < (0.6 if near else 0.1)
            w.writerow([f"c{i}", "destroyed" if flagged else "no_change", f"D{i % 3}",
                        33.300 + rng.uniform(-0.004, 0.004) if near else 33.500, 35.400])
    events = tmp_path / "events.csv"
    events.write_text("latitude,longitude\n33.300,35.400\n")
    out = tmp_path / "out.json"
    assert main(["x", str(table), str(events), str(out)]) == 0
    result = json.loads(out.read_text())
    assert result["status"] == "ok" and result["near_flagged_share"] > result["far_flagged_share"]
    assert len(load_cells(str(table))) == 200
