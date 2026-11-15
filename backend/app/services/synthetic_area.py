"""Read-only synthetic contract adapter for the first full-stack slice.

No database, network, or real incident data is accessed here.
"""
import json
from pathlib import Path

from backend.app.core.config import get_settings

CONTRACTS = Path(__file__).resolve().parents[3] / 'docs' / 'contracts'
DEMO_AREA_ID = 'demo-area-01'
DEMO_SOURCE_ID = 'demo-source-01'


def enabled() -> bool:
    return get_settings().demo_synthetic


def area_summary(area_id: str) -> dict | None:
    if area_id != DEMO_AREA_ID:
        return None
    payload = json.loads((CONTRACTS / 'AreaSummary.json').read_text(encoding='utf-8'))
    if payload.get('synthetic') is not True or payload.get('area_id') != area_id:
        raise ValueError('Invalid synthetic area fixture')
    return payload


def source_record(source_id: str) -> dict | None:
    if source_id != DEMO_SOURCE_ID:
        return None
    payload = json.loads((CONTRACTS / 'SourceRecord.json').read_text(encoding='utf-8'))
    if payload.get('synthetic') is not True or payload.get('source_id') != source_id:
        raise ValueError('Invalid synthetic source fixture')
    return payload
