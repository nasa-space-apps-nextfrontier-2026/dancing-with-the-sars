"""M1-02: unsupervised anomaly model for candidate damage per H3 cell.

Isolation Forest (primary) and robust Mahalanobis / MinCovDet (comparison), trained
only on quiet built-up cells in training blocks. Thresholds are quantiles of the
training quiet scores. Classes are provisional anomaly classes, not probabilities
and not proof of collapse (docs/04, steps 6-9).
"""

from __future__ import annotations

import dataclasses
from typing import Any

import numpy as np
import pandas as pd
from h3.api import basic_str as h3s
from sklearn.covariance import MinCovDet
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import BallTree
from sklearn.preprocessing import RobustScaler

MODEL_VERSION = "0.1"
BASE_FEATURES = ["d_hh", "d_hv", "d_pol", "strong_drop_share", "built_density"]
OPTIONAL_FEATURES = ["incidence", "coh_drop"]
QUANTILES = {"possible": 0.95, "moderate": 0.99, "severe": 0.999}
MIN_TRAIN_FOR_TAIL = 2000  # fewer quiet cells cannot support a 0.1% tail estimate
EARTH_RADIUS_KM = 6371.0088


@dataclasses.dataclass
class FitResult:
    features: list[str]
    method: str
    thresholds: dict[str, float]
    n_train: int
    n_holdout: int
    seed: int
    train_blocks: list[str]
    holdout_blocks: list[str]
    tail_reliable: bool
    params: dict[str, Any]


def quiet_cells(cells: pd.DataFrame, events: pd.DataFrame, radius_km: float = 2.0) -> np.ndarray:
    """True where no reported event (lat, lon) lies within radius_km of the cell centre.

    Missing reports do not prove quiet; this only selects training controls.
    """
    if events.empty:
        return np.ones(len(cells), dtype=bool)
    centres = np.radians([h3s.cell_to_latlng(c) for c in cells["h3_r9"]])
    tree = BallTree(np.radians(events[["lat", "lon"]].to_numpy()), metric="haversine")
    counts = tree.query_radius(centres, r=radius_km / EARTH_RADIUS_KM, count_only=True)
    return counts == 0


def spatial_blocks(cells: pd.DataFrame, block_res: int = 6) -> pd.Series:
    return cells["h3_r9"].map(lambda c: h3s.cell_to_parent(c, block_res))


def split_blocks(blocks: pd.Series, seed: int, holdout_share: float = 0.2) -> tuple[list[str], list[str]]:
    uniq = np.array(sorted(blocks.unique()))
    rng = np.random.default_rng(seed)
    rng.shuffle(uniq)
    n_hold = max(1, round(len(uniq) * holdout_share))
    return sorted(uniq[n_hold:].tolist()), sorted(uniq[:n_hold].tolist())


def usable_features(cells: pd.DataFrame) -> list[str]:
    extra = [f for f in OPTIONAL_FEATURES if f in cells and cells[f].notna().mean() > 0.9]
    return BASE_FEATURES + extra


def fit_and_score(cells: pd.DataFrame, quiet: np.ndarray, seed: int = 42,
                  method: str = "isolation_forest") -> tuple[pd.DataFrame, FitResult]:
    cells = cells.copy()
    feats = usable_features(cells)
    ok = ~cells["low_coverage"].to_numpy() & cells[feats].notna().all(axis=1).to_numpy()

    blocks = spatial_blocks(cells)
    train_blocks, hold_blocks = split_blocks(blocks[ok & quiet], seed)
    in_train = blocks.isin(train_blocks).to_numpy()
    in_hold = blocks.isin(hold_blocks).to_numpy()
    train = ok & quiet & in_train
    holdout = ok & quiet & in_hold
    if train.sum() < 50:
        raise ValueError(f"Only {int(train.sum())} quiet training cells; cannot fit")

    scaler = RobustScaler().fit(cells.loc[train, feats])
    X = np.full((len(cells), len(feats)), np.nan)
    X[ok] = scaler.transform(cells.loc[ok, feats])

    params: dict[str, Any] = {"scaler": "RobustScaler"}
    score = np.full(len(cells), np.nan)
    if method == "isolation_forest":
        iforest = IsolationForest(n_estimators=300, max_samples="auto", contamination="auto",
                                  random_state=seed).fit(X[train])
        score[ok] = -iforest.score_samples(X[ok])
        params.update(n_estimators=300, max_samples="auto")
        try:
            mcd = MinCovDet(random_state=seed).fit(X[train])
            cells.loc[ok, "score_mahalanobis"] = np.sqrt(mcd.mahalanobis(X[ok]))
        except ValueError:
            cells["score_mahalanobis"] = np.nan
    elif method == "zscore":
        score[ok] = np.nanmax(np.abs(X[ok]), axis=1)
    else:
        raise ValueError(method)
    cells["score"] = score

    thresholds = {k: float(np.quantile(score[train], q)) for k, q in QUANTILES.items()}
    tail_ok = int(train.sum()) >= MIN_TRAIN_FOR_TAIL
    cells["split"] = np.where(train, "train", np.where(holdout, "holdout", "scored"))
    cells = classify(cells, X, feats, thresholds, tail_ok)

    fit = FitResult(feats, method, thresholds, int(train.sum()), int(holdout.sum()), seed,
                    train_blocks, hold_blocks, tail_ok, params)
    return cells, fit


def classify(cells: pd.DataFrame, X: np.ndarray, feats: list[str],
             thresholds: dict[str, float], tail_ok: bool) -> pd.DataFrame:
    s = cells["score"].to_numpy()
    collapse = cells["d_hh"].to_numpy() < 0
    if "coh_drop" in feats:
        collapse = collapse | (cells["coh_drop"].to_numpy() > 0)

    unknown = cells["low_coverage"].to_numpy() | ~np.isfinite(s)
    level = np.select(
        [s > thresholds["severe"], s > thresholds["moderate"], s > thresholds["possible"]],
        ["severe", "moderate", "possible"], default="none")
    level = np.where(unknown, "unknown", level)

    cls = np.select(
        [level == "unknown", level == "none", ~collapse],
        ["unknown", "no_detected_change", "other_change"],
        default=np.char.add(level.astype(str), "_candidate"))
    cls = np.where(cls == "severe_candidate", "destroyed_or_severe_candidate", cls)
    cells["damage_class"] = cls

    conf = {"destroyed_or_severe_candidate": "higher" if tail_ok else "medium",
            "moderate_candidate": "medium", "possible_candidate": "low"}
    cells["confidence"] = [conf.get(c, None) for c in cls]

    z = {f: X[:, i] for i, f in enumerate(feats)}
    reasons = []
    for i in range(len(cells)):
        r = []
        if unknown[i]:
            r.append("low_coverage")
        elif level[i] != "none":
            if z["d_hh"][i] < -3 or z["strong_drop_share"][i] > 3:
                r.append("strong_hh_drop")
            if abs(z["d_hv"][i]) > 3:
                r.append("hv_shift")
            if abs(z["d_pol"][i]) > 3:
                r.append("polarization_shift")
            if not collapse[i]:
                r.append("other_change")
        reasons.append("|".join(r))
    cells["reasons"] = reasons
    return cells


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def holdout_false_alarms(cells: pd.DataFrame, fit: FitResult) -> dict[str, Any]:
    """Share of untouched quiet hold-out cells above each training threshold."""
    h = cells[cells["split"] == "holdout"]
    out: dict[str, Any] = {"n": len(h)}
    for name, q in QUANTILES.items():
        k = int((h["score"] > fit.thresholds[name]).sum())
        out[name] = {"expected": round(1 - q, 4), "observed": k / len(h) if len(h) else None,
                     "count": k, "ci95": wilson(k, len(h))}
    return out
