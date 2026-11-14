"""Worker timer (M3-04). Real-data mode only; synthetic mode keeps `python -m worker.main --once`.

    python -m worker.scheduler --once          run every job once and exit
    python -m worker.scheduler                 run forever: fires every 30 min; night lights and clean-up daily

Uses DATABASE_URL like the API. One failing job never stops the others.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from worker.jobs import prune, run_fires, run_power_loss

FIRE_EVERY_S = 30 * 60
LIGHTS_EVERY_S = 24 * 60 * 60


def run_once(engine) -> list[dict]:
    return [run_fires(engine), run_power_loss(engine, os.environ.get("NIGHTLIGHT_HISTORY")), prune(engine)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args(argv)
    from backend.app.db.base import make_engine

    engine = make_engine()
    if args.once:
        print(json.dumps(run_once(engine), default=str))
        return 0
    next_fire = next_lights = 0.0
    while True:
        now = time.monotonic()
        if now >= next_fire:
            print(json.dumps(run_fires(engine), default=str), flush=True)
            next_fire = now + FIRE_EVERY_S
        if now >= next_lights:
            print(json.dumps(run_power_loss(engine, os.environ.get("NIGHTLIGHT_HISTORY")), default=str),
                  flush=True)
            print(json.dumps(prune(engine), default=str), flush=True)
            next_lights = now + LIGHTS_EVERY_S
        time.sleep(30)


if __name__ == "__main__":
    sys.exit(main())
