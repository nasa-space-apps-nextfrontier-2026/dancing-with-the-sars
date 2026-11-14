"""Check inventory and safety defaults without external credentials."""
import json
from pathlib import Path

from backend.app.agents import NAMES
from backend.app.api.v1 import SPEC
from backend.app.main import app

root=Path(__file__).resolve().parents[1]
assert len(NAMES)==12
expected={(method.upper(),'/api/v1'+path) for path,methods in SPEC['paths'].items() for method in methods}
actual={(method,route.path) for route in app.routes if route.path.startswith('/api/v1') for method in route.methods}
assert expected <= actual, sorted(expected-actual)
assert len(expected)==40
for fixture in (root/'docs/contracts').glob('*.json'):
    if fixture.name=='planning_manifest.json': continue
    assert json.loads(fixture.read_text(encoding='utf-8'))['synthetic'] is True
print(f'PASS: {len(expected)} API operations registered, 12 deterministic interfaces, synthetic fixtures')
