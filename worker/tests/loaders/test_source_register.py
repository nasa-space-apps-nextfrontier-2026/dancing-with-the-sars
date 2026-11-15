import json

from worker.loaders.sources import (
    CONTRACT_PATH,
    SOURCES_PATH,
    load_sources,
    schema_errors,
)

# Sources the served data actually comes from (radar sources are in the radar export instead).
EXPECTED = {"ds-black-marble", "ds-firms-viirs", "ds-worldpop", "ds-ghs-obat", "ds-osm-facilities",
            "ds-hdx-lbn-boundaries"}


def _contract_fields():
    return set(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")).keys())


def test_sources_file_loads():
    data = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert {r["source_id"] for r in data} == EXPECTED


def test_every_record_has_all_required_fields():
    records = load_sources()
    required = _contract_fields()
    for record in records:
        missing = required - set(record.keys())
        assert not missing, f"record missing fields: {sorted(missing)}"


def test_every_record_matches_the_contract_schema():
    for record in load_sources():
        assert schema_errors(record) == [], record["source_id"]
        assert record["synthetic"] is False
        assert "VERIFY" not in json.dumps(record)


def test_source_ids_are_unique():
    records = load_sources()
    ids = [r["source_id"] for r in records]
    assert len(ids) == len(set(ids)) == len(EXPECTED)


def test_schema_errors_catch_bad_records():
    bad = dict(load_sources()[0], update_frequency="Daily")
    assert schema_errors(bad)
