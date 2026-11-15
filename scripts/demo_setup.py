"""One command to set up the real-data demo on this machine (local PostGIS in Docker).

    python -m scripts.demo_setup                 # everything that the local files allow
    python -m scripts.demo_setup --no-docker     # PostGIS already running
    python -m scripts.demo_setup --offline       # skip the live FIRMS fetch
    python -m scripts.demo_setup --dry-run       # print the plan only

Steps, in order: start the database, migrate, load the radar results, build the building table,
publish (damage + live fires), run the agents, load the agent outputs, load the facilities, run the
worker once (fires, night lights when NIGHTLIGHT_HISTORY is set, clean-up). A step whose private input
files are not on this machine is skipped with the reason; nothing is downloaded except the public
FIRMS feed. Data files never go into Git. Afterwards it prints how to start the API and the frontend.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

PY = sys.executable


@dataclass
class Step:
    name: str
    cmd: list[str]
    needs: list[str]          # files that must exist (relative to the repo root)

    def missing(self, root: Path) -> list[str]:
        return [n for n in self.needs if not (root / n).exists()]


def default_database_url() -> str:
    port = os.environ.get("CIVISAR_DB_PORT", "5432")
    return f"postgresql+psycopg://civisar:civisar_local_only@localhost:{port}/civisar"


def plan(offline: bool = False, docker: bool = True) -> list[Step]:
    damage = "data/private/nisar/model/damage_cells.parquet"
    steps = [Step("Start PostGIS (Docker)", ["docker", "compose", "up", "-d", "db"], ["docker-compose.yml"])] if docker else []
    steps += [
        Step("Migrate the database", [PY, "-m", "alembic", "-c", "backend/alembic.ini", "upgrade", "head"], []),
        Step("Load the radar results", [PY, "-m", "scripts.load_radar_results", "--replace"],
             ["data/local/radar_contract/metric_values.json", damage]),
        Step("Build the building table", [PY, "-m", "pipelines.buildings.table"],
             ["data/local/buildings_base.parquet", "data/local/buildings_height.parquet", damage,
              "data/local/population.csv.gz"]),
        Step("Publish damage" + ("" if offline else " and live fires"),
             [PY, "-m", "worker.main", "--publish", "--damage", damage] + ([] if offline else ["--fires"]), [damage]),
        Step("Run the agents", [PY, "-m", "worker.main", "--agents", "--table", "data/local/building_table.parquet",
                                "--population", "data/local/population.csv.gz"],
             ["data/local/building_table.parquet", "data/local/population.csv.gz"]),
        Step("Load the agent outputs", [PY, "-m", "scripts.load_agent_outputs"], ["data/published/incidents.json"]),
        Step("Load the facilities", [PY, "-m", "scripts.load_facilities"],
             ["data/local/facilities.csv", "data/local/boundaries.geojson"]),
    ]
    if not offline:
        steps.append(Step("Run the worker once (fires, night lights, clean-up)", [PY, "-m", "worker.scheduler", "--once"], []))
    return steps


def wait_for_database(timeout_s: int = 90) -> bool:
    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["DATABASE_URL"], connect_args={"connect_timeout": 3})
    end = time.monotonic() + timeout_s
    while time.monotonic() < end:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:  # noqa: BLE001 - still starting
            time.sleep(2)
    return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-docker", action="store_true", help="PostGIS is already running")
    ap.add_argument("--offline", action="store_true", help="skip the live FIRMS fetch and the worker run")
    ap.add_argument("--dry-run", action="store_true", help="print the plan only")
    args = ap.parse_args(argv)
    root = Path.cwd()
    os.environ.setdefault("DATABASE_URL", default_database_url())
    os.environ.setdefault("DEMO_SYNTHETIC", "false")
    os.environ.setdefault("DATA_ROOT", "data")
    results = []
    for step in plan(args.offline, not args.no_docker):
        missing = step.missing(root)
        if missing:
            results.append((step.name, "skipped", "missing " + ", ".join(missing)))
            print(f"-- {step.name}: skipped (missing {', '.join(missing)})")
            continue
        print(f"-> {step.name}: {' '.join(step.cmd)}")
        if args.dry_run:
            results.append((step.name, "planned", ""))
            continue
        code = subprocess.call(step.cmd, cwd=root)
        if code != 0:
            print(f"!! {step.name} failed (exit {code}). Fix it and run this command again; loads are replaceable.")
            return code
        if step.cmd[:3] == ["docker", "compose", "up"] and not wait_for_database():
            print("!! PostGIS did not answer within 90 s. Check `docker compose ps` and CIVISAR_DB_PORT.")
            return 1
        results.append((step.name, "done", ""))
    print("\nSummary:")
    for name, state, why in results:
        print(f"  {state:8} {name}{'  (' + why + ')' if why else ''}")
    print("""
Next (each in its own terminal, from the repo root):
  1. Make a sign-in user:  python -m scripts.create_demo_user   (asks for name, role, password; saves to your ignored .env)
  2. API (real data):      in .env set DEMO_SYNTHETIC=false, DATA_ROOT=data and DATABASE_URL, then
                           python -m uvicorn backend.app.main:app --port 8000
  3. Frontend:             cd frontend && npm ci && npm run dev:auth   -> http://127.0.0.1:5173 (sign in for real data)
Guide: docs/31_BACKEND_REAL_DATA.md""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
