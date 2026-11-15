"""Real-data radar adapter (used when DEMO_SYNTHETIC is false).

Layers come from the contract export (data/local/radar_contract/layers.json) and point to the
private change COGs listed in data/manifests/nisar_change_index.json. Damage results and the
time series come from PostGIS (loaded by scripts/load_radar_results.py).

Safety: the 72-hour hold applies to every record and every role (Admin is not a bypass for the hold or for area scope (doc 07)); layers need the
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
from backend.app.policy.release import is_released, now_utc
from backend.app.policy.scope import AOI_ID

ROOT = Path(__file__).resolve().parents[3]
CHANGE_INDEX = "manifests/nisar_change_index.json"
LAYERS_FILE = "local/radar_contract/layers.json"


def data_root() -> Path:
    root = Path(get_settings().data_root)
    return root if root.is_absolute() else ROOT / root


def _visible(release_at: Any, identity: Identity | None) -> bool:
    return is_released(release_at)


def _role_ok(identity: Identity | None, min_role: str) -> bool:
    if min_role == "public":
        return True
    return identity is not None and ROLE_LEVEL.get(identity.role, 0) >= ROLE_LEVEL.get(min_role, 99)


@lru_cache(maxsize=4)
def _catalogue(root_value: str, layers_mtime: float,
               index_mtime: float) -> dict[str, tuple[dict, str, str]]:
    root = Path(root_value)
    layers = json.loads((root / LAYERS_FILE).read_text(encoding="utf-8"))
    index = json.loads((root / CHANGE_INDEX).read_text(encoding="utf-8"))
    by_name = {layer["name"]: layer for layer in index["layers"]}
    out = {}
    for rec in layers:
        name = next(n for n in by_name if f"nisar-{n.lower().replace('_', '-')}" == rec["layer_id"])
        entry = by_name[name]
        kind = "mean" if entry["kind"] in ("mean", "pass") else "change"
        raw_path = Path(entry["path"])
        if raw_path.is_absolute():
            resolved = raw_path.resolve()
        else:
            # Export manifests use repository-relative data/... paths.  DATA_ROOT may point
            # elsewhere, so strip that conventional prefix before resolving under it.
            parts = (
                raw_path.parts[1:]
                if raw_path.parts and raw_path.parts[0].lower() == "data"
                else raw_path.parts
            )
            resolved = (root / Path(*parts)).resolve()
        out[rec["layer_id"]] = (rec, str(resolved), kind)
    return out


def catalogue() -> dict[str, tuple[dict, str, str]]:
    root = data_root()
    lf, ix = root / LAYERS_FILE, root / CHANGE_INDEX
    if not lf.exists() or not ix.exists():
        return {}
    return _catalogue(str(root), lf.stat().st_mtime, ix.stat().st_mtime)


def list_layers(identity: Identity | None) -> list[dict]:
    return [
        rec
        for rec, _, _ in catalogue().values()
        if _role_ok(identity, rec["min_role"]) and _visible(rec["release_at"], identity)
    ]


def get_layer(layer_id: str, identity: Identity | None) -> dict | None:
    item = catalogue().get(layer_id)
    if (
        item is None
        or not _role_ok(identity, item[0]["min_role"])
        or not _visible(item[0]["release_at"], identity)
    ):
        return None
    return item[0]


def layer_file(layer_id: str, identity: Identity | None) -> tuple[str, str] | None:
    """Private COG path and colour kind, only when the layer itself may be shown."""
    # A full-AOI raster would disclose cells beyond a single-cell assignment.  Until
    # clipped artifacts exist, only identities explicitly scoped to the AOI may read it.
    if (
        identity is None
        or AOI_ID not in identity.area_scopes
        or get_layer(layer_id, identity) is None
    ):
        return None
    _, path, kind = catalogue()[layer_id]
    allowed_dir = (data_root() / "private" / "nisar" / "change").resolve()
    resolved = Path(path).resolve()
    if allowed_dir not in resolved.parents or not resolved.is_file():
        return None  # never serve anything outside the change-layer folder
    return str(resolved), kind


def downloadable_file(layer_id: str, file_id: str, identity: Identity | None) -> str | None:
    """Resolve one exact manifest-listed COG filename; never accept a client path."""
    found = layer_file(layer_id, identity)
    if found is None:
        return None
    path = Path(found[0])
    return str(path) if file_id == path.name else None


def damage(engine: Any, area_id: str, pass_id: str | None, identity: Identity | None) -> dict:
    """r9 radar results inside an area for one run (pass_id = 'A' or a later pass date)."""
    from sqlalchemy import text

    with engine.connect() as conn:
        area_match = (
            "JOIN areas requested ON requested.area_id = :area "
            "WHERE (a.area_id = requested.area_id OR a.area_id = requested.parent_id) "
        )
        eligible = (
            "AND EXISTS (SELECT 1 FROM radar_area_results visible "
            "JOIN areas visible_area ON visible_area.area_id = visible.area_id "
            "WHERE visible.artifact_id = a.id "
            "AND (visible_area.area_id = requested.area_id "
            "OR visible_area.parent_id = requested.area_id) "
            "AND visible.release_at IS NOT NULL AND visible.release_at <= :now) "
        )
        params: dict[str, Any] = {"area": area_id, "now": now_utc()}
        if pass_id in (None, "A"):
            artifact = conn.execute(
                text(
                    "SELECT a.id, a.run_id FROM radar_artifacts a "
                    + area_match
                    + "AND a.before_acquired_at < '2026-06-01' "
                    + eligible
                    + "ORDER BY a.after_acquired_at DESC, a.id DESC LIMIT 1"
                ),
                params,
            ).first()
        else:
            params["d"] = pass_id
            artifact = conn.execute(
                text(
                    "SELECT a.id, a.run_id FROM radar_artifacts a "
                    + area_match
                    + "AND CAST(a.after_acquired_at AS date) = CAST(:d AS date) "
                    "AND a.before_acquired_at >= '2026-06-01' "
                    + eligible
                    + "ORDER BY a.after_acquired_at DESC, a.id DESC LIMIT 1"
                ),
                params,
            ).first()
        if artifact is None:
            return {"synthetic": False, "items": [], "next_cursor": None}
        rows = conn.execute(
            text(
                "SELECT r.area_id, r.classification, r.anomaly_score, r.reason_codes, a.run_id, r.release_at "
                "FROM radar_area_results r JOIN radar_artifacts a ON a.id = r.artifact_id "
                "JOIN areas c ON c.area_id = r.area_id "
                "WHERE r.artifact_id = :artifact "
                "AND (c.area_id = :area OR c.parent_id = :area) ORDER BY r.area_id"
            ),
            {"artifact": artifact.id, "area": area_id},
        ).all()
    items = [
        {
            "area_id": r.area_id,
            "candidate_class": r.classification,
            "score": float(r.anomaly_score) if r.anomaly_score is not None else None,
            "reason_codes": list(r.reason_codes),
            "run_id": r.run_id,
        }
        for r in rows
        if _visible(r.release_at, identity)
    ]
    return {"synthetic": False, "items": items, "next_cursor": None}


def series(
    engine: Any,
    layer_id: str,
    area_id: str,
    date_from: str | None,
    date_to: str | None,
    identity: Identity | None,
) -> dict | None:
    """Per-pass candidate counts for an r8 area (MetricValue records), plus known gaps."""
    from sqlalchemy import text

    layer = get_layer(layer_id, identity)
    if layer is None:
        return None
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT record FROM metric_values WHERE area_id = :area "
                "AND metric = 'radar_candidate_change_cells' ORDER BY observed_at"
            ),
            {"area": area_id},
        ).all()
    points = []
    for (rec,) in rows:
        if not _visible(rec["release_at"], identity):
            continue
        if (date_from and rec["date"] < date_from) or (date_to and rec["date"] > date_to):
            continue
        points.append(
            {
                "date": rec["date"],
                "metric": rec["metric"],
                "low": rec["low"],
                "high": rec["high"],
                "unit": rec["unit"],
                "label": rec["label"],
                "source": rec["source"],
                "run_id": rec["processing_run_id"],
                "release_at": rec["release_at"],
                "limitations": rec["limitations"],
            }
        )
    return {
        "synthetic": False,
        "area_id": area_id,
        "points": points,
        "missing_intervals": layer["missing_intervals"],
    }


def trace(engine: Any, value_id: str, identity: Identity | None) -> dict | None:
    """A value with the source records and model runs behind it (Trace contract)."""
    from backend.app.policy.scope import area_in_scope
    from sqlalchemy import text

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT record FROM metric_values WHERE value_id = :v"), {"v": value_id}
        ).first()
    if row is None or identity is None:
        return None
    rec = row[0]
    if not is_released(rec["release_at"]) or not area_in_scope(
        rec["area_id"], identity.area_scopes
    ):
        return None
    root = data_root()
    sources_file = root / "local" / "radar_contract" / "sources.json"
    sources = json.loads(sources_file.read_text(encoding="utf-8")) if sources_file.exists() else []
    used = [s for s in sources if s["source_id"] in rec["source"]]
    tests_file = root / "manifests" / "model_tests.json"
    tests = json.loads(tests_file.read_text(encoding="utf-8")) if tests_file.exists() else {}
    run_tests: list = []
    if tests.get("run_id") == rec["processing_run_id"]:
        run_tests = [
            {
                "holdout_false_alarms": tests.get("holdout_false_alarms"),
                "eye_check": tests.get("eye_check"),
                "strike_context": tests.get("strike_context"),
                "sentinel1_check": tests.get("sentinel1_check"),
            }
        ]
    else:
        for s in tests.get("time_slider", []):
            if s.get("run_id") == rec["processing_run_id"]:
                run_tests = [{"holdout_false_alarms": s.get("holdout_false_alarms")}]
    redactions = [
        "Single-cell (H3 r9) results and exact building locations are not part of this trace."
    ]
    if len(used) < len(rec["source"]):
        redactions.append("Some source records are not loaded on this server.")
    return {
        "synthetic": False,
        "value": rec,
        "sources": used,
        "runs": [{"run_id": rec["processing_run_id"], "model_tests": run_tests}],
        "redactions": redactions,
    }
