import json
from pathlib import Path

from backend.app.api.v1 import SPEC


def test_contract_examples_are_synthetic():
    root=Path(__file__).resolve().parents[1]
    assert len(SPEC['paths'])>=30
    for fixture in (root/'docs/contracts').glob('*.json'):
        if fixture.name=='planning_manifest.json': continue
        assert json.loads(fixture.read_text(encoding='utf-8'))['synthetic'] is True
