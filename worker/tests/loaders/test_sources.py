import json
from pathlib import Path

from worker.loaders.sources import CONTRACT_PATH, SOURCES_PATH, load_sources


def _contract_fields():
    return set(json.loads(CONTRACT_PATH.read_text(encoding="utf-8")).keys())


def test_sources_file_loads():
    data = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 15


def test_every_record_has_all_required_fields():
    records = load_sources()
    required = _contract_fields()
    for record in records:
        missing = required - set(record.keys())
        assert not missing, f"record missing fields: {sorted(missing)}"


def test_source_ids_are_unique():
    records = load_sources()
    ids = [r["source_id"] for r in records]
    assert len(ids) == len(set(ids)) == 15


def test_record_count_is_fifteen():
    records = load_sources()
    assert len(records) == 15
