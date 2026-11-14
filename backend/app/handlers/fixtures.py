import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_DIR = ROOT / "docs" / "contracts"

def load_fixture(name: str) -> dict:
    path = CONTRACTS_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))