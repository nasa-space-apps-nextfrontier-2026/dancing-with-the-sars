"""Write data/manifests/nightlights_granules.json listing Black Marble granules for the demo box.

Run on Colab or locally:  python -m worker.services.discover_nightlights [out.json] [start] [end]
Without a start date it lists the last 120 days, which is all the 60-clear-night baseline needs.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

from worker.services.cmr import BLACK_MARBLE, manifest, search


def main(argv: list[str]) -> int:
    out = Path(argv[1] if len(argv) > 1 else "data/manifests/nightlights_granules.json")
    start = argv[2] if len(argv) > 2 else (date.today() - timedelta(days=120)).isoformat()
    end = argv[3] if len(argv) > 3 else None
    granules = []
    for short_name in BLACK_MARBLE:
        found = search(short_name, start=start, end=end)
        print(f"{short_name}: {len(found)} granules")
        granules.extend(found)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest(granules), indent=2), encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
