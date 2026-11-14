"""Publish the ML outputs as small JSON artifacts the backend can serve (ML wiring step).

Reads Udula's NISAR damage table and Thanoban's night-light history and FIRMS feed, and writes
`damage.json`, `values.json`, `alerts.json` and `manifest.json` into one directory (default
`data/published`, outside Git). The backend never computes anything per request; it only reads
these files. Nothing is invented: a missing input is recorded as unavailable in the manifest.

    python -m worker.main --publish --damage damage_cells.parquet --history bm_history.csv.gz [--fires]
"""
from __future__ import annotations

import csv
import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

CANDIDATE_CLASSES = ("possible_candidate", "moderate_candidate", "destroyed_or_severe_candidate")
LABELS = {"observed": "Observed", "reported": "Reported", "corroborated": "Corroborated"}
RADAR_HOLD_HOURS = 72
VERSION = "m1-v2"
WARNING = "Candidate signal from satellite data; not confirmed and never a cause. Check before acting."


def _clean(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    return value.item() if hasattr(value, "item") else value


def _read_table(path: str) -> list[dict]:
    if path.endswith(".parquet"):
        import pandas as pd
        return pd.read_parquet(path).to_dict("records")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _end_date(pair: str) -> datetime:
    """`2026-06-24..2026-07-18` gives the end of the after period, midnight UTC."""
    return datetime.fromisoformat(pair.split("..")[-1]).replace(tzinfo=UTC)


def _flag(value) -> bool:
    return str(_clean(value)).lower() == "true"


def damage_artifacts(rows: list[dict], processed_at: datetime) -> tuple[dict, dict]:
    """Return (damage.json, values.json) from the NISAR damage table. Scores are anomaly scores."""
    items, values = [], []
    run_id = str(rows[0]["run_id"]) if rows else "none"
    release = None
    for row in rows:
        raw = _clean(row.get("score"))
        score = float(raw) if raw not in (None, "") else None
        label = LABELS.get(str(_clean(row.get("evidence_label")) or "").lower(), "Unknown")
        acquired = _end_date(str(row["pair_after"]))
        release = acquired + timedelta(hours=RADAR_HOLD_HOURS)
        area = str(row["h3_r9"])
        reasons = [r for r in str(_clean(row.get("reasons")) or "").split(",") if r]
        items.append({"area_id": area, "parent_r8": str(row["h3_r8"]),
                      "candidate_class": str(row["damage_class"]), "score": score,
                      "reason_codes": reasons, "run_id": str(row["run_id"]), "label": label,
                      "confidence": _clean(row.get("confidence")),
                      "second_sensor_agrees": _flag(row.get("s1_agrees")),
                      "version_confounded": _flag(row.get("version_confounded"))})
        if score is not None:
            values.append({
                "synthetic": False, "value_id": f"{run_id}:{area}:anomaly", "area_id": area,
                "metric": "damage_anomaly_score", "low": score, "high": score, "unit": "anomaly_score",
                "label": label, "source": ["nisar-l2-gcov", "opera-rtc-s1"],
                "date": acquired.date().isoformat(), "safety_tag": "restricted_aggregate",
                "lineage_ids": [run_id], "processing_run_id": run_id, "processing_version": VERSION,
                "confidence": None, "acquired_at": _iso(acquired),
                "processed_at": _iso(processed_at), "release_at": _iso(release),
                "freshness": "Aging", "cached": False,
                "limitations": ["Anomaly score, not a calibrated damage probability.",
                                "Radar candidate change only; not confirmed damage.",
                                (f"Model confidence: {_clean(row.get('confidence')) or 'not rated'} "
                                 "(text class; the contract's numeric confidence is not defined yet).")]})
    meta = {"run_id": run_id, "release_at": _iso(release) if release else None, "synthetic": False}
    return {**meta, "items": items}, {**meta, "items": values}


def alert_record(kind: str, area: str, detected: str, satellites: list[str], product: str,
                 sources: int, processed_at: datetime, run: str, title: str) -> dict:
    stamp = detected.replace(":", "").replace("-", "")[:15]
    return {"synthetic": False, "alert_id": f"{kind}-{area}-{stamp}", "area_id": area, "type": kind,
            "title": title, "detected_at": detected, "processed_at": _iso(processed_at),
            "satellite": "+".join(satellites), "product": product, "label": "Observed",
            "source": [product], "lineage_ids": [run], "independent_source_count": sources,
            "freshness": "Fresh", "cached": False, "release_at": _iso(processed_at),
            "safety_tag": "restricted_alert", "rings": [], "facilities": [], "services": [],
            "route_options_url": "", "review_status": "unreviewed", "cause": "not determined",
            "warning": WARNING}


def power_loss_alerts(history_path: str, processed_at: datetime) -> list[dict]:
    from worker.services.evaluate_nightlights import load
    from worker.services.power_loss import power_loss_events
    run = f"blackmarble-{processed_at:%Y%m%d}"
    out = []
    for e in power_loss_events(load(history_path)):
        title = "Possible power loss" + ("" if e["corroborated"] else " (one satellite, low confidence)")
        out.append(alert_record("possible_power_loss", e["area"], f"{e['time']}T00:00:00Z",
                                e["satellites"], "Black Marble VJ146A2/VJ246A2",
                                2 if e["corroborated"] else 1, processed_at, run, title))
    return out


def fire_alerts(processed_at: datetime) -> list[dict]:
    import h3

    from worker.services.firms_feed import current_events
    events, _ = current_events()
    run = f"firms-{processed_at:%Y%m%d}"
    return [alert_record("fire_detected", h3.latlng_to_cell(e.lat, e.lon, 8),
                         _iso(datetime.fromisoformat(e.start)), list(e.satellites),
                         "FIRMS VIIRS 375 m", len(e.satellites), processed_at, run, "Fire detected")
            for e in events]


def publish(out_dir: str = "data/published", damage: str | None = None, history: str | None = None,
            fires: bool = False, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sources: list[dict] = []
    alerts: list[dict] = []

    def source(name: str, acquired: str | None, ok: bool, failure: str = "") -> None:
        sources.append({"id": name, "acquired_at": acquired, "processed_at": _iso(now),
                        "last_success_at": _iso(now) if ok else None,
                        "freshness": "Fresh" if ok else "Unknown", "cached": False, "failure": failure})

    if damage:
        dmg, vals = damage_artifacts(_read_table(damage), now)
        (out / "damage.json").write_text(json.dumps(dmg), encoding="utf-8")
        (out / "values.json").write_text(json.dumps(vals), encoding="utf-8")
        source("nisar-damage", dmg["release_at"], True)
    else:
        source("nisar-damage", None, False, "no damage table given")
    if history:
        alerts += power_loss_alerts(history, now)
        source("black-marble", None, True)
    else:
        source("black-marble", None, False, "no night-light history given")
    if fires:
        try:
            alerts += fire_alerts(now)
            source("firms", None, True)
        except (OSError, ValueError, ImportError) as error:  # a failed live source is recorded
            source("firms", None, False, f"{type(error).__name__}: {str(error)[:80]}")
    else:
        source("firms", None, False, "fire feed not requested")
    (out / "alerts.json").write_text(json.dumps({"items": alerts}), encoding="utf-8")
    manifest = {"published_at": _iso(now), "synthetic": False, "sources": sources, "alerts": len(alerts)}
    (out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest
