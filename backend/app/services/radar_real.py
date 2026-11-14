"""Real-data radar adapter (used when DEMO_SYNTHETIC is false).

Layers come from the contract export (data/local/radar_contract/layers.json) and point to the
private change COGs listed in data/manifests/nisar_change_index.json. Damage results and the
time series come from PostGIS (loaded by scripts/load_radar_results.py).

Safety: the 72-hour hold applies to every record (admins excepted, for review); layers need the
role named in min_role; area scope is checked by the router before these functions run.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.app.core.config import get_settings
from backend.app.core.permissions import ROLE_LEVEL
from backend.app.core.security import Identity
from backend.app.policy.release import is_released

ROOT = Path(__file__).resolve().parents[3]
CHANGE_INDEX = "manifests/nisar_change_index.json"
LAYERS_FILE = "local/radar_contract/layers.json"


def data_root() -> Path:
    root = Path(get_settings().data_root)
    return root if root.is_absolute() else ROOT / root


def _visible(release_at: Any, identity: Identity | None) -> bool:
    return (identity is not None and identity.role == "admin") or is_released(release_at)


def _role_ok(identity: Identity | None, min_role: str) -> bool:
    if min_role == "public":
        return True
    return identity is not None and ROLE_LEVEL.get(identity.role, 0) >= ROLE_LEVEL.get(min_role, 99)


@lru_cache(maxsize=4)
def _catalogue(layers_mtime: float, index_mtime: float) -> dict[str, tuple[dict, str, str]]:
    root = data_root()
    layers = json.loads((root / LAYERS_FILE).read_text(encoding="utf-8"))
    index = json.loads((root / CHANGE_INDEX).read_text(encoding="utf-8"))
    by_name = {layer["name"]: layer for layer in index["layers"]}
    out = {}
    for rec in layers:
        name = next(n for n in by_name if f"nisar-{n.lower().replace('_', '-')}" == rec["layer_id"])
        entry = by_name[name]
        kind = "mean" if entry["kind"] in ("mean", "pass") else "change"
        out[rec["layer_id"]] = (rec, str((ROOT / entry["path"]).resolve()), kind)
    return out


def catalogue() -> dict[str, tuple[dict, str, str]]:
    root = data_root()
    lf, ix = root / LAYERS_FILE, root / CHANGE_INDEX
    if not lf.exists() or not ix.exists():
        return {}
    return _catalogue(lf.stat().st_mtime, ix.stat().st_mtime)


def list_layers(identity: Identity | None) -> list[dict]:
    return [rec for rec, _, _ in catalogue().values()
            if _role_ok(identity, rec["min_role"]) and _visible(rec["release_at"], identity)]


def get_layer(layer_id: str, identity: Identity | None) -> dict | None:
    item = catalogue().get(layer_id)
    if item is None or not _role_ok(identity, item[0]["min_role"]) or not _visible(item[0]["release_at"], identity):
        return None
    return item[0]


def layer_file(layer_id: str, identity: Identity | None) -> tuple[str, str] | None:
    """Private COG path and colour kind, only when the layer itself may be shown."""
    if get_layer(layer_id, identity) is None:
        return None
    _, path, kind = catalogue()[layer_id]
    allowed_dir = (data_root() / "private" / "nisar" / "change").resolve()
    resolved = Path(path).resolve()
    if allowed_dir not in resolved.parents or not resolved.is_file():
        return None  # never serve anything outside the change-layer folder
    return str(resolved), kind


def damage(engine: Any, area_id: str, pass_id: str | None, identity: Identity | None) -> dict:
    """r9 radar results inside an area for one run (pass_id = 'A' or a later pass date)."""
    from sqlalchemy import text

    with engine.connect() as conn:
        if pass_id in (None, "A"):
            run = conn.execute(text(
                "SELECT run_id FROM radar_artifacts WHERE before_acquired_at < '2026-06-01' "
                "ORDER BY after_acquired_at DESC LIMIT 1")).scalar()
        else:
            run = conn.execute(text(
                "SELECT run_id FROM radar_artifacts WHERE CAST(after_acquired_at AS date) = CAST(:d AS date) "
                "AND before_acquired_at >= '2026-06-01'"), {"d": pass_id}).scalar()
        if run is None:
            return {"synthetic": False, "items": [], "next_cursor": None}
        rows = conn.execute(text(
            "SELECT r.area_id, r.classification, r.anomaly_score, r.reason_codes, a.run_id, r.release_at "
            "FROM radar_area_results r JOIN radar_artifacts a ON a.id = r.artifact_id "
            "JOIN areas c ON c.area_id = r.area_id "
            "WHERE a.run_id = :run AND (c.area_id = :area OR c.parent_id = :area) ORDER BY r.area_id"),
            {"run": run, "area": area_id}).all()
    items = [{"area_id": r.area_id, "candidate_class": r.classification,
              "score": float(r.anomaly_score) if r.anomaly_score is not None else None,
              "reason_codes": list(r.reason_codes), "run_id": r.run_id}
             for r in rows if _visible(r.release_at, identity)]
    return {"synthetic": False, "items": items, "next_cursor": None}


def series(engine: Any, layer_id: str, area_id: str, date_from: str | None, date_to: str | None,
           identity: Identity | None) -> dict | None:
    """Per-pass candidate counts for an r8 area (MetricValue records), plus known gaps."""
    from sqlalchemy import text

    layer = get_layer(layer_id, identity)
    if layer is None:
        return None
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT record FROM metric_values WHERE area_id = :area "
            "AND metric = 'radar_candidate_change_cells' ORDER BY observed_at"), {"area": area_id}).all()
    points = []
    for (rec,) in rows:
        if not _visible(rec["release_at"], identity):
            continue
        if (date_from and rec["date"] < date_from) or (date_to and rec["date"] > date_to):
            continue
        points.append({"date": rec["date"], "metric": rec["metric"], "low": rec["low"], "high": rec["high"],
                       "unit": rec["unit"], "label": rec["label"], "source": rec["source"],
                       "run_id": rec["processing_run_id"], "release_at": rec["release_at"],
                       "limitations": rec["limitations"]})
    return {"synthetic": False, "area_id": area_id, "points": points,
            "missing_intervals": layer["missing_intervals"]}


def trace(engine: Any, value_id: str, identity: Identity | None) -> dict | None:
    """A value with the source records and model runs behind it (Trace contract)."""
    from backend.app.policy.scope import area_in_scope
    from sqlalchemy import text

    with engine.connect() as conn:
        row = conn.execute(text("SELECT record FROM metric_values WHERE value_id = :v"),
                           {"v": value_id}).first()
    if row is None or identity is None:
        return None
    rec = row[0]
    if identity.role != "admin" and (not is_released(rec["release_at"])
                                     or not area_in_scope(rec["area_id"], identity.area_scopes)):
        return None
    root = data_root()
    sources_file = root / "local" / "radar_contract" / "sources.json"
    sources = json.loads(sources_file.read_text(encoding="utf-8")) if sources_file.exists() else []
    used = [s for s in sources if s["source_id"] in rec["source"]]
    tests_file = root / "manifests" / "model_tests.json"
    tests = json.loads(tests_file.read_text(encoding="utf-8")) if tests_file.exists() else {}
    run_tests: list = []
    if tests.get("run_id") == rec["processing_run_id"]:
        run_tests = [{"holdout_false_alarms": tests.get("holdout_false_alarms"),
                      "eye_check": tests.get("eye_check"), "strike_context": tests.get("strike_context"),
                      "sentinel1_check": tests.get("sentinel1_check")}]
    else:
        for s in tests.get("time_slider", []):
            if s.get("run_id") == rec["processing_run_id"]:
                run_tests = [{"holdout_false_alarms": s.get("holdout_false_alarms")}]
    redactions = ["Single-cell (H3 r9) results and exact building locations are not part of this trace."]
    if len(used) < len(rec["source"]):
        redactions.append("Some source records are not loaded on this server.")
    return {"synthetic": False, "value": rec, "sources": used,
            "runs": [{"run_id": rec["processing_run_id"], "model_tests": run_tests}],
            "redactions": redactions}
