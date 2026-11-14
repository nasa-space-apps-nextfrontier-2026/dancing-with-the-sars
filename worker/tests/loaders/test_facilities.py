from pathlib import Path

from worker.loaders.facilities import (
    CELL_ID,
    COLUMNS,
    FACILITY_ID,
    NAME,
    SOURCE,
    STATUS,
    STATUS_SOURCE,
    TYPE,
    load_facilities,
)

FIXTURE = Path(__file__).with_name("fixture_overpass.json")


def test_load_facilities_columns():
    rows = load_facilities(FIXTURE)
    assert rows
    assert list(rows[0].keys()) == COLUMNS


def test_types_map_correctly():
    rows = load_facilities(FIXTURE)
    by_id = {r[FACILITY_ID]: r for r in rows}
    assert by_id["osm:hospital1001"][TYPE] == "hospital"
    assert by_id["osm:clinic1002"][TYPE] == "clinic"
    assert by_id["osm:school1003"][TYPE] == "school"
    assert by_id["osm:water1004"][TYPE] == "water"
    assert by_id["osm:power1005"][TYPE] == "power"
    # healthcare=clinic on a way maps to clinic
    assert by_id["osm:clinic2001"][TYPE] == "clinic"


def test_status_always_unknown():
    rows = load_facilities(FIXTURE)
    assert all(r[STATUS] == "Unknown" for r in rows)
    assert all(r[STATUS_SOURCE] is None for r in rows)


def test_excluded_tags_never_appear():
    rows = load_facilities(FIXTURE)
    types = {r[TYPE] for r in rows}
    ids = {r[FACILITY_ID] for r in rows}
    assert "police" not in types
    assert "prison" not in types
    assert "osm:police1006" not in ids
    assert "osm:prison1007" not in ids
    assert "osm:base1008" not in ids


def test_no_coordinates_skipped():
    rows = load_facilities(FIXTURE)
    assert all(r[NAME] != "No Coordinates" for r in rows)


def test_source_and_cell_id():
    rows = load_facilities(FIXTURE)
    assert all(r[SOURCE] == "OpenStreetMap contributors" for r in rows)
    assert all(r[CELL_ID] for r in rows)
    assert all(len(r[CELL_ID]) == 15 for r in rows)  # H3 res-9 cells are 15 hex chars
