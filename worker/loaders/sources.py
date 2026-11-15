"""Source register loader (Kisara K-05).

Loads data/manifests/sources.json and validates each record against the
SourceRecord schema in docs/contracts/openapi.yaml (fields, types, no extra
fields). The API serves these records with the radar export's records.
"""

from __future__ import annotations

import json

from worker.loaders.config import MANIFESTS_DIR, ROOT

CONTRACT_PATH = ROOT / "docs" / "contracts" / "SourceRecord.json"
OPENAPI_PATH = ROOT / "docs" / "contracts" / "openapi.yaml"
SOURCES_PATH = MANIFESTS_DIR / "sources.json"


def schema_errors(record: dict) -> list[str]:
    """Contract errors for one record (empty when it matches SourceRecord)."""
    from jsonschema import Draft202012Validator

    spec = json.loads(OPENAPI_PATH.read_text(encoding="utf-8"))
    schema = spec["components"]["schemas"]["SourceRecord"] | {"components": spec["components"]}
    return [e.message for e in Draft202012Validator(schema).iter_errors(record)]


def _contract_fields() -> set[str]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    return set(contract.keys())


def load_sources() -> list[dict]:
    """Load and validate the source register.

    Returns the list of source records. Raises ValueError if any record is
    missing a field required by SourceRecord.json, does not match the
    SourceRecord schema, or if source_id values are not unique.
    """
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    if not isinstance(sources, list):
        raise TypeError("sources.json must contain a list of records")

    required = _contract_fields()
    seen: set[str] = set()
    for record in sources:
        if not isinstance(record, dict):
            raise TypeError("each source record must be an object")
        missing = required - set(record.keys())
        if missing:
            raise ValueError(f"record missing fields: {sorted(missing)}")
        errors = schema_errors(record)
        if errors:
            raise ValueError(f"{record.get('source_id')}: {errors[0]}")
        sid = record.get("source_id")
        if sid in seen:
            raise ValueError(f"duplicate source_id: {sid}")
        seen.add(sid)

    return sources


if __name__ == "__main__":
    records = load_sources()
    print(f"loaded {len(records)} source records")
    print("source_ids:", [r["source_id"] for r in records])
