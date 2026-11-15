"""Live refresh jobs for the scheduler: night-light history, new NISAR passes, agents.

Each job only wires existing code (Thanoban's Black Marble history builder, Udula's ASF discovery,
the agents and their loader) to run on current data. A job never crashes the scheduler: a missing
token or input reads "unavailable", a failure is recorded in source_status and the last good data
stays in place.

Env:
    NIGHTLIGHT_HISTORY   per-cell history file to refresh (data/local/bm_history.csv.gz)
    EARTHDATA_TOKEN      Earthdata bearer token, or BM_TOKEN_FILE: a file holding only the token
    BM_WORK              temporary tile folder (default data/raw/blackmarble_tmp, git-ignored)
    NISAR_LOADED_THROUGH last NISAR pass date already loaded (default: newest slider folder)
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from worker.jobs import record_failure, store

HISTORY_SOURCE = "blackmarble-history"
RADAR_SOURCE = "nisar-gcov"
MAX_REFRESH_DAYS = 30            # never re-download more than a month of nights in one run
AGENTS_MIN_GAP_S = 60 * 60       # agents at most once per hour
SLIDER_DIR = Path("data/private/nisar/model/slider")
DAMAGE = "data/private/nisar/model/damage_cells.parquet"
TABLE = "data/local/building_table.parquet"
POPULATION = "data/local/population.csv.gz"

_last_agents_run = 0.0


# ---------- night lights ----------

def last_night(history_path: str) -> dt.date | None:
    """Newest night in the per-cell history file, or None if the file is missing or empty."""
    if not os.path.exists(history_path):
        return None
    newest = None
    with gzip.open(history_path, "rt", newline="") as f:
        for row in csv.DictReader(f):
            d = row.get("date") or ""
            if d and (newest is None or d > newest):
                newest = d
    return dt.date.fromisoformat(newest) if newest else None


def token_file() -> str | None:
    """Path of a file holding the Earthdata token, writing EARTHDATA_TOKEN to the work dir if set."""
    token = os.environ.get("EARTHDATA_TOKEN", "").strip()
    if token:
        work = Path(os.environ.get("BM_WORK", "data/raw/blackmarble_tmp"))
        work.mkdir(parents=True, exist_ok=True)
        path = work / ".earthdata_token"
        path.write_text(token, encoding="utf-8")
        return str(path)
    path = os.environ.get("BM_TOKEN_FILE")
    return os.path.expanduser(path) if path and os.path.exists(os.path.expanduser(path)) else None


def merge_history(history_path: str, new_path: str) -> int:
    """Add the new nights to the history; rows for a night present in both come from the new file."""
    with gzip.open(new_path, "rt", newline="") as f:
        new_rows = list(csv.DictReader(f))
    new_keys = {(r["date"], r["satellite"]) for r in new_rows}
    old_rows = []
    if os.path.exists(history_path):
        with gzip.open(history_path, "rt", newline="") as f:
            old_rows = [r for r in csv.DictReader(f) if (r["date"], r["satellite"]) not in new_keys]
    fields = ["date", "satellite", "cell", "mean_radiance", "n_pixels", "n_clear"]
    tmp = history_path + ".tmp"
    with gzip.open(tmp, "wt", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(old_rows + new_rows, key=lambda r: (r["date"], r["satellite"], r["cell"])))
    os.replace(tmp, history_path)
    return len({d for d, _ in new_keys})


def refresh_history(history_path: str, today: dt.date | None = None,
                    builder: Callable[[int, str, str, str], None] | None = None) -> dict[str, Any]:
    """Download only the nights newer than the last one in the history, then merge them in."""
    today = today or dt.datetime.now(dt.UTC).date()
    token = token_file()
    if not token:
        return {"source": HISTORY_SOURCE, "status": "unavailable",
                "note": "set EARTHDATA_TOKEN or BM_TOKEN_FILE to refresh the night-light history"}
    newest = last_night(history_path)
    days = MAX_REFRESH_DAYS if newest is None else min(MAX_REFRESH_DAYS, (today - newest).days + 1)
    if days <= 0:
        return {"source": HISTORY_SOURCE, "status": "ok", "new_nights": 0, "last_night": str(newest)}
    work = os.environ.get("BM_WORK", "data/raw/blackmarble_tmp")
    out = os.path.join(work, "new_nights.csv.gz")
    (builder or _run_builder)(days, token, work, out)
    if not os.path.exists(out):
        return {"source": HISTORY_SOURCE, "status": "ok", "new_nights": 0, "last_night": str(newest)}
    added = merge_history(history_path, out)
    os.remove(out)
    return {"source": HISTORY_SOURCE, "status": "ok", "new_nights": added,
            "last_night": str(last_night(history_path))}


def _run_builder(days: int, token: str, work: str, out: str) -> None:
    from worker.services import blackmarble_history as bm

    bm.TOKEN_FILE, bm.WORK, bm.OUT = token, work, out
    try:
        bm.main(days)
    except IndexError:          # no granules in the window: nothing new yet
        return


def run_nightlights(engine: Any, history_path: str | None,
                    refresher: Callable[[str], dict] | None = None) -> list[dict]:
    """Refresh the history (when a token is set), then run the power-loss rule on it."""
    from worker.jobs import run_power_loss

    results: list[dict] = []
    if history_path:
        try:
            results.append((refresher or refresh_history)(history_path))
        except Exception as exc:  # noqa: BLE001 - keep the old history, still run the rule
            record_failure(engine, HISTORY_SOURCE, exc)
            results.append({"source": HISTORY_SOURCE, "status": "failed", "error": str(exc)[:200]})
    results.append(run_power_loss(engine, history_path))
    return results


# ---------- radar: new NISAR passes ----------

def loaded_through() -> str | None:
    """Newest NISAR pass already processed (env override, else the newest slider folder)."""
    if os.environ.get("NISAR_LOADED_THROUGH"):
        return os.environ["NISAR_LOADED_THROUGH"]
    dates = sorted(p.name for p in SLIDER_DIR.glob("*") if p.is_dir())
    return dates[-1] if dates else None


def check_radar(engine: Any, search: Callable[[dict, str], list[dict]] | None = None) -> dict[str, Any]:
    """Look for NISAR GCOV passes on the demo track/frame newer than the loaded ones.

    Detection only: the M1 pipeline (download, crop, process, model) needs a person to check each pass
    (scientific QA), so a new pass is recorded in source_status for the team to run, not processed here.
    """
    from pipelines.radar.nisar import discover

    try:
        cfg = discover.load_config()
        feats = (search or discover.search_asf)(cfg, "GCOV")
        dates = sorted({r["date"] for r in map(discover.to_record, feats) if discover.on_demo_track(r, cfg)})
    except Exception as exc:  # noqa: BLE001 - ASF down: keep the last status
        record_failure(engine, RADAR_SOURCE, exc)
        return {"source": RADAR_SOURCE, "status": "failed", "error": str(exc)[:200]}
    done = loaded_through()
    new = [d for d in dates if done is None or d > done]
    detail = {"latest_on_asf": dates[-1] if dates else None, "loaded_through": done, "new_passes": new,
              "action": (f"new pass available: {new[-1]}, run the M1 pipeline (docs/31)" if new
                         else "up to date")}
    acquired = dt.datetime.fromisoformat(f"{done}T00:00:00+00:00") if done else None
    store(engine, RADAR_SOURCE, [], acquired, detail)
    return {"source": RADAR_SOURCE, "status": "ok", **detail}


# ---------- agents ----------

def _py(*args: str) -> list[str]:
    return [sys.executable, "-m", *args]


def refresh_agents(force: bool = False, run: Callable[[list[str]], int] | None = None,
                   clock: Callable[[], float] = time.monotonic) -> dict[str, Any]:
    """Republish damage and alerts, rerun the agents and reload their output (at most once an hour)."""
    global _last_agents_run
    now = clock()
    if not force and _last_agents_run and now - _last_agents_run < AGENTS_MIN_GAP_S:
        return {"job": "agents", "status": "skipped", "note": "ran less than an hour ago"}
    missing = [p for p in (DAMAGE, TABLE) if not os.path.exists(p)]
    if missing:
        return {"job": "agents", "status": "unavailable", "note": "missing " + ", ".join(missing)}
    run = run or (lambda cmd: subprocess.call(cmd))
    publish = _py("worker.main", "--publish", "--damage", DAMAGE, "--fires")
    history = os.environ.get("NIGHTLIGHT_HISTORY")
    if history and os.path.exists(history):
        publish += ["--history", history]
    agents = _py("worker.main", "--agents", "--table", TABLE)
    if os.path.exists(POPULATION):
        agents += ["--population", POPULATION]
    for cmd in (publish, agents, _py("scripts.load_agent_outputs")):
        code = run(cmd)
        if code != 0:
            return {"job": "agents", "status": "failed", "step": cmd[2], "exit": code}
    _last_agents_run = now
    return {"job": "agents", "status": "ok"}


def changed(result: dict, previous: dict[str, Any]) -> bool:
    """True when a job's alert count differs from its last run (so the agents need a rerun)."""
    key = result.get("source") or result.get("job")
    value = (result.get("alerts"), result.get("new_nights"), tuple(result.get("new_passes") or ()))
    old = previous.get(key)
    previous[key] = value
    return result.get("status") == "ok" and old != value
