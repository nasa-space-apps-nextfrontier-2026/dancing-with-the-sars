"""M1-03: collect the NISAR model's test results and write the hand-off manifests.

    python -m pipelines.radar.nisar.evaluate --events data/raw/ucdp/GEDEvent_v26_01_26_09.csv

Writes:
  data/manifests/model_tests.json   hold-out, eye check, strike-context check, limits
  data/manifests/radar_run.json     M1 -> M2/M3 hand-off: artifacts, schema, CRS, checksums
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from h3.api import basic_str as h3s
from sklearn.neighbors import BallTree

from .crop import sha256
from .model import wilson
from .process import OUT_DIR, load_ucdp_events

MANIFESTS = Path("data/manifests")
EARTH_KM = 6371.0088


def strike_context(cells: pd.DataFrame, events: pd.DataFrame) -> dict[str, Any]:
    """Candidate rate near vs far from recorded events. Association only, not ground truth."""
    a = cells[~cells["sparse_cell"] & ~cells["low_coverage"] & cells["damage_class"].ne("unknown")].copy()
    tree = BallTree(np.radians(events[["lat", "lon"]].to_numpy()), metric="haversine")
    dist, _ = tree.query(np.radians([h3s.cell_to_latlng(c) for c in a["h3_r9"]]), k=1)
    a["km"] = dist[:, 0] * EARTH_KM
    a["cand"] = a["damage_class"].str.endswith("_candidate")
    out: dict[str, Any] = {"n_events": len(events), "n_cells": len(a)}
    for name, sel in (("near_lt_1km", a["km"] < 1), ("far_ge_5km", a["km"] >= 5)):
        k, n = int(a.loc[sel, "cand"].sum()), int(sel.sum())
        out[name] = {"cells": n, "candidates": k, "rate": k / n if n else None, "ci95": wilson(k, n)}
    near, far = out["near_lt_1km"]["rate"], out["far_ge_5km"]["rate"]
    out["rate_ratio"] = near / far if near is not None and far else None
    baseline = float((a["km"] < 1).mean())
    out["top_cells_within_1km"] = {str(n): float((a.nlargest(n, "score")["km"] < 1).mean())
                                   for n in (20, 50, 100)}
    out["all_cells_within_1km"] = baseline
    out["note"] = ("Preliminary check by M1 for M1-04 (Thanoban) to formalise with controls. "
                   "Events = UCDP candidate GED (CC BY 4.0); a recorded event is not a confirmed collapse.")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--events", type=Path, required=True)
    args = ap.parse_args(argv)

    run = json.loads((OUT_DIR / "run.json").read_text(encoding="utf-8"))
    cells = pd.read_parquet(OUT_DIR / "damage_cells.parquet")
    eye = json.loads((MANIFESTS / "nisar_eyecheck.json").read_text(encoding="utf-8"))
    events = load_ucdp_events(args.events)

    slider = []
    for p in sorted(glob.glob(str(OUT_DIR / "slider" / "*" / "run.json"))):
        r = json.loads(Path(p).read_text(encoding="utf-8"))
        slider.append({"after_date": Path(p).parent.name, "run_id": r["run_id"],
                       "class_counts": r["class_counts"],
                       "holdout_false_alarms": r["holdout_false_alarms"], "limits": r["limits"]})

    now = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    tests = {
        "schema_version": "0.1", "kind": "nisar_model_tests", "synthetic": False, "created_at": now,
        "run_id": run["run_id"], "method": run["method"], "quiet_controls": run["quiet_controls"],
        "n_train": run["n_train"], "n_holdout": run["n_holdout"], "tail_reliable": run["tail_reliable"],
        "holdout_false_alarms": run["holdout_false_alarms"],
        "eye_check": eye["rounds"][-1] | {"history": eye["rounds"][:-1]},
        "strike_context": strike_context(cells, events),
        "qa": {k: run["qa"][k] for k in ("water", "banding_before_correction", "banding_after_correction")},
        "time_slider": slider,
        "sentinel1_check": (json.loads((OUT_DIR / "s1_check.json").read_text(encoding="utf-8"))
                            if (OUT_DIR / "s1_check.json").exists() else None),
        "claims_allowed": ["candidate change in dense built-up areas", "known false-alarm rate on quiet hold-out"],
        "claims_not_allowed": ["confirmed damage or collapse", "precision/recall or accuracy",
                               "destroyed vs severe distinction", "damage counts as totals (minimums only)"],
    }
    (MANIFESTS / "model_tests.json").write_text(json.dumps(tests, indent=2, default=str), encoding="utf-8")

    change_index = json.loads((MANIFESTS / "nisar_change_index.json").read_text(encoding="utf-8"))
    handoff = {
        "schema_version": "0.1", "kind": "nisar_radar_run", "synthetic": False, "created_at": now,
        "run_id": run["run_id"], "owner": "M1 (Udula)", "receivers": ["M2 (Chames)", "M3 (Rashiru)"],
        "damage_cells": {
            "path": (OUT_DIR / "damage_cells.parquet").as_posix(),
            "sha256": sha256(OUT_DIR / "damage_cells.parquet"),
            "key": "h3_r9 (lowercase hex string); h3_r8 parent for display",
            "columns": list(cells.columns),
            "classes": sorted(cells["damage_class"].unique().tolist()),
            "safety_tag": "restricted (building-level inference); publish r8 aggregates only, 72 h delay",
        },
        "time_slider_cells": [f"{(OUT_DIR / 'slider' / s['after_date'] / 'damage_cells.parquet').as_posix()}"
                              for s in slider],
        "change_images": {"index": (MANIFESTS / "nisar_change_index.json").as_posix(),
                          "layers": len(change_index["layers"]), "crs_epsg": change_index["crs_epsg"],
                          "storage": change_index["storage"], "safety_tag": change_index["safety_tag"]},
        "tests": (MANIFESTS / "model_tests.json").as_posix(),
        "licences": {"NISAR": "NASA/ISRO open data via ASF DAAC", "OSM buildings": "ODbL (HOTOSM export)",
                     "UCDP events": "CC BY 4.0"},
        "reproduce": [
            "python -m pipelines.radar.nisar.discover",
            "python -m pipelines.radar.nisar.download --tiers A-before A-after B",
            "python -m pipelines.radar.nisar.process --buildings <hotosm parquet> --events <ucdp csv>",
            "python -m pipelines.radar.nisar.change_images",
            "python -m pipelines.radar.nisar.evaluate --events <ucdp csv>",
        ],
    }
    (MANIFESTS / "radar_run.json").write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    sc = tests["strike_context"]
    print(f"strike context: near {sc['near_lt_1km']['rate']:.3f} vs far {sc['far_ge_5km']['rate']:.3f}; "
          f"top20 within 1 km {sc['top_cells_within_1km']['20']:.0%} vs all {sc['all_cells_within_1km']:.0%}")
    print(f"time slider runs: {len(slider)}; wrote model_tests.json and radar_run.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
