from pathlib import Path

import h3

from worker.loaders.grid import (
    CELL_ID,
    COLUMNS,
    DISTRICT_ID,
    GOVERNORATE_ID,
    PARENT_R8,
    build_grid,
)

FIXTURE = Path(__file__).with_name("fixture_grid.geojson")
TEST_BOX = (35.05, 33.05, 35.25, 33.25)


def test_grid_columns():
    rows = build_grid(boundaries_path=FIXTURE, box=TEST_BOX)
    assert rows
    assert list(rows[0].keys()) == COLUMNS


def test_cell_ids_are_valid_h3():
    rows = build_grid(boundaries_path=FIXTURE, box=TEST_BOX)
    assert all(h3.is_valid_cell(r[CELL_ID]) for r in rows)


def test_no_duplicate_cells():
    rows = build_grid(boundaries_path=FIXTURE, box=TEST_BOX)
    ids = [r[CELL_ID] for r in rows]
    assert len(ids) == len(set(ids))


def test_parent_r8_matches_h3():
    rows = build_grid(boundaries_path=FIXTURE, box=TEST_BOX)
    for r in rows:
        assert r[PARENT_R8] == h3.cell_to_parent(r[CELL_ID], 8)


def test_count_is_stable():
    a = build_grid(boundaries_path=FIXTURE, box=TEST_BOX)
    b = build_grid(boundaries_path=FIXTURE, box=TEST_BOX)
    assert len(a) == len(b)
    assert [r[CELL_ID] for r in a] == [r[CELL_ID] for r in b]


def test_district_join_assigns_ids():
    rows = build_grid(boundaries_path=FIXTURE, box=TEST_BOX)
    inside = [r for r in rows if 35.12 <= r["lon"] <= 35.18 and 33.12 <= r["lat"] <= 33.18]
    assert inside
    assert all(r[DISTRICT_ID] == "D1" for r in inside)
    assert all(r[GOVERNORATE_ID] == "G1" for r in inside)


def test_outside_district_is_none_not_a_guess():
    rows = build_grid(boundaries_path=FIXTURE, box=TEST_BOX)
    outside = [r for r in rows if r["lon"] < 35.1 or r["lat"] < 33.1]
    if outside:
        assert all(r[DISTRICT_ID] is None for r in outside)
        assert all(r[GOVERNORATE_ID] is None for r in outside)
