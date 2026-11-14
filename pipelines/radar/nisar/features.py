"""M1-02: per-cell radar change features from cropped GCOV GeoTIFFs.

Rules (docs/04 "Radar algorithm and failure gates"):
- average calibrated *linear* power over valid dates, then convert to dB;
- store valid-date counts; non-positive or NaN power is nodata;
- features per H3 resolution 9 built-up cell; few valid pixels -> low_coverage (Unknown).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from h3.api import basic_int as h3i
from pyproj import CRS, Transformer

STRONG_DROP_DB = -3.0
H3_RES = 9
MIN_VALID_PIXELS = 8
MIN_VALID_SHARE = 0.5
H3_R9_AREA_M2 = 105_332.5  # average hexagon area at resolution 9


def read_grid(path: str | Path) -> tuple[np.ndarray, rasterio.Affine, CRS]:
    with rasterio.open(path) as r:
        return r.read(1).astype("float32"), r.transform, CRS.from_user_input(r.crs)


def check_same_grid(paths: Sequence[str | Path]) -> None:
    """All dates must share one grid. Registration offsets are checked separately."""
    ref = None
    for p in paths:
        with rasterio.open(p) as r:
            key = (r.shape, tuple(round(v, 6) for v in r.transform[:6]), r.crs.to_epsg())
        if ref is None:
            ref = key
        elif key != ref:
            raise ValueError(f"Grid differs from the first date: {p}")


def mean_power(paths: Sequence[str | Path]) -> tuple[np.ndarray, np.ndarray]:
    """Mean linear power over valid dates, and the count of valid dates per pixel."""
    check_same_grid(paths)
    total = count = None
    for p in paths:
        a, _, _ = read_grid(p)
        valid = np.isfinite(a) & (a > 0)
        a = np.where(valid, a, 0.0)
        total = a if total is None else total + a
        count = valid.astype("int16") if count is None else count + valid
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = np.where(count > 0, total / np.maximum(count, 1), np.nan)
    return mean.astype("float32"), count


def to_db(power: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(power > 0, 10.0 * np.log10(power), np.nan).astype("float32")


def pixel_features(before_hh: np.ndarray, before_hv: np.ndarray,
                   after_hh: np.ndarray, after_hv: np.ndarray) -> dict[str, np.ndarray]:
    """Inputs are mean linear power. Outputs are dB differences (after minus before)."""
    bh, bv, ah, av = (to_db(x) for x in (before_hh, before_hv, after_hh, after_hv))
    d_hh = ah - bh
    d_hv = av - bv
    d_pol = (ah - av) - (bh - bv)
    valid = np.isfinite(d_hh) & np.isfinite(d_hv)
    return {"d_hh": d_hh, "d_hv": d_hv, "d_pol": d_pol, "valid": valid}


def _smooth_profile(values: np.ndarray, window: int) -> np.ndarray:
    """Fill gaps by interpolation, then a centred running median."""
    idx = np.arange(values.size)
    ok = np.isfinite(values)
    if ok.sum() < 2:
        return np.zeros_like(values)
    filled = np.interp(idx, idx[ok], values[ok])
    return pd.Series(filled).rolling(window, center=True, min_periods=1).median().to_numpy()


def destripe(change: np.ndarray, sample: np.ndarray, window: int = 101) -> tuple[np.ndarray, dict]:
    """Remove smooth column-wise then row-wise trends in a change image.

    BETA products show radiometric banding from incomplete calibration; a slowly varying
    column/row bias in the change would otherwise look like damage along stripes. Trends are
    estimated only on `sample` pixels (valid built-up), so local damage barely moves the medians.
    """
    d = np.where(sample, change, np.nan)
    with np.errstate(all="ignore"):
        col = _smooth_profile(np.nanmedian(d, axis=0), window)
        d2 = change - col[None, :]
        row = _smooth_profile(np.nanmedian(np.where(sample, d2, np.nan), axis=1), window)
    out = (d2 - row[:, None]).astype("float32")
    info = {"column_trend_range_db": float(np.nanmax(col) - np.nanmin(col)),
            "row_trend_range_db": float(np.nanmax(row) - np.nanmin(row))}
    return out, info


def pixel_cells(transform: rasterio.Affine, shape: tuple[int, int], crs: CRS,
                where: np.ndarray, res: int = H3_RES) -> np.ndarray:
    """H3 cell (as uint64) for each pixel centre where `where` is True; 0 elsewhere."""
    rows, cols = np.nonzero(where)
    xs, ys = rasterio.transform.xy(transform, rows, cols, offset="center")
    lon, lat = Transformer.from_crs(crs, 4326, always_xy=True).transform(np.asarray(xs), np.asarray(ys))
    ids = np.zeros(shape, dtype="uint64")
    ids[rows, cols] = [h3i.latlng_to_cell(la, lo, res) for la, lo in zip(lat, lon)]
    return ids


def cell_table(cells: np.ndarray, built: np.ndarray, feats: dict[str, np.ndarray],
               pixel_area_m2: float, incidence: np.ndarray | None = None) -> pd.DataFrame:
    """One row per built-up H3 cell with median features and coverage counts."""
    sel = built & (cells > 0)
    df = pd.DataFrame({
        "h3_int": cells[sel],
        "valid": feats["valid"][sel],
        "d_hh": feats["d_hh"][sel],
        "d_hv": feats["d_hv"][sel],
        "d_pol": feats["d_pol"][sel],
    })
    df["strong_drop"] = (df["d_hh"] < STRONG_DROP_DB) & df["valid"]
    if incidence is not None:
        df["incidence"] = incidence[sel]
    v = df[df["valid"]]
    agg = v.groupby("h3_int").agg(
        d_hh=("d_hh", "median"), d_hv=("d_hv", "median"), d_pol=("d_pol", "median"),
        strong_drop_share=("strong_drop", "mean"),
        **({"incidence": ("incidence", "median")} if incidence is not None else {}),
    )
    counts = df.groupby("h3_int").agg(n_built_px=("valid", "size"), n_valid_px=("valid", "sum"))
    out = counts.join(agg, how="left").reset_index()
    out["built_density"] = (out["n_built_px"] * pixel_area_m2 / H3_R9_AREA_M2).clip(upper=1.0)
    out["low_coverage"] = (out["n_valid_px"] < MIN_VALID_PIXELS) | (
        out["n_valid_px"] / out["n_built_px"] < MIN_VALID_SHARE)
    out["h3_r9"] = [h3i.int_to_str(int(i)) for i in out["h3_int"]]
    out["h3_r8"] = [h3i.int_to_str(h3i.cell_to_parent(int(i), 8)) for i in out["h3_int"]]
    return out.drop(columns="h3_int")
