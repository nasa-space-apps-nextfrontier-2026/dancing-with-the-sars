"""Run the strike-enrichment tests on Udula's damage table and a list of events (task M1-04).

    python -m worker.evaluation.run_strike_tests damage_table.csv events.csv [out.json]

The damage table is one row per cell. Column names are settable because they are only fixed at the
H2 contract freeze. Cells need coordinates: either `lat` and `lon` columns, or an H3 `cell_id`
(then the `h3` package must be installed). A cell is flagged when its class is one of the candidate
damage classes. Results are evidence about the model, never confirmed damage.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from worker.evaluation.events import from_csv
from worker.evaluation.strike_tests import Cell, strike_enrichment

CANDIDATE_CLASSES = {"destroyed", "severely_damaged", "moderately_damaged", "possibly_damaged"}


def load_cells(path: str, id_col: str = "cell_id", class_col: str = "damage_class",
               district_col: str = "district", lat_col: str = "lat", lon_col: str = "lon",
               flagged_classes: set[str] = frozenset(CANDIDATE_CLASSES)) -> list[Cell]:
    cells = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if lat_col in row and row[lat_col] != "":
                lat, lon = float(row[lat_col]), float(row[lon_col])
            else:
                import h3  # only needed when the table has H3 cell ids and no coordinates
                lat, lon = h3.cell_to_latlng(row[id_col])
            cells.append(Cell(row[id_col], lat, lon, row.get(district_col) or "unknown",
                              row[class_col].strip().lower() in flagged_classes))
    return cells


def main(argv: list[str]) -> int:
    cells = load_cells(argv[1])
    with open(argv[2], newline="", encoding="utf-8") as f:
        events = from_csv(f)
    text = json.dumps(strike_enrichment(cells, events), indent=2)
    if len(argv) > 3:
        Path(argv[3]).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
