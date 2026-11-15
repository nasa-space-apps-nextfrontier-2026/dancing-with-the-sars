"""Worker timer (M3-04). Real-data mode only; synthetic mode keeps `python -m worker.main --once`.

    python -m worker.scheduler --once          run every job once and exit
    python -m worker.scheduler                 run forever:
        fires every 30 min (FIRMS);
        night lights daily (refresh the Black Marble history when a token is set, then power loss);
        NISAR new-pass check daily (ASF, detection only);
        agents rerun after a job changed its data, at most once an hour;
        clean-up daily.

Uses DATABASE_URL like the API. One failing job never stops the others.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from worker.jobs import prune, run_fires
from worker.live import changed, check_radar, refresh_agents, run_nightlights

FIRE_EVERY_S = 30 * 60
LIGHTS_EVERY_S = 24 * 60 * 60
RADAR_EVERY_S = 24 * 60 * 60


def history() -> str | None:
    return os.environ.get("NIGHTLIGHT_HISTORY")


def run_once(engine, agents: bool = True) -> list[dict]:
    out = [run_fires(engine), *run_nightlights(engine, history()), check_radar(engine), prune(engine)]
    if agents:
        out.append(refresh_agents(force=True))
    return out


def _print(result: dict) -> None:
    print(json.dumps(result, default=str), flush=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--no-agents", action="store_true", help="skip the agents rerun")
    args = ap.parse_args(argv)
    from backend.app.db.base import make_engine

    engine = make_engine()
    if args.once:
        print(json.dumps(run_once(engine, agents=not args.no_agents), default=str))
        return 0
    seen: dict = {}
    next_fire = next_lights = next_radar = 0.0
    while True:
        now = time.monotonic()
        results: list[dict] = []
        if now >= next_fire:
            results.append(run_fires(engine))
            next_fire = now + FIRE_EVERY_S
        if now >= next_lights:
            results += run_nightlights(engine, history())
            results.append(prune(engine))
            next_lights = now + LIGHTS_EVERY_S
        if now >= next_radar:
            results.append(check_radar(engine))
            next_radar = now + RADAR_EVERY_S
        for r in results:
            _print(r)
        flags = [changed(r, seen) for r in results]   # update every job's last value, not just the first
        if not args.no_agents and any(flags):
            _print(refresh_agents())
        time.sleep(30)


if __name__ == "__main__":
    sys.exit(main())
