"""M1-03 hand-off: NISAR results as the team's contract records (docs/contracts/openapi.yaml).

Reads the private M1 outputs and writes three lists, each record validated against its schema:
  MetricValue   per H3 resolution-8 area only (never per r9 cell), restricted aggregate
  Layer         one per change image (map tiles), analyst role and up
  SourceRecord  NISAR (BETA, PROVISIONAL, V1), Sentinel-1 RTC, OSM buildings, UCDP, NASADEM

Nothing here edits another member's code or the contracts. Output goes to data/local/ (ignored);
a short manifest with counts and checksums goes to data/manifests/radar_contract.json.

    python -m pipelines.radar.nisar.export_contract
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from jsonschema import Draft202012Validator

from .model import MODEL_VERSION

ROOT = Path(__file__).resolve().parents[3]
SPEC_PATH = ROOT / "docs/contracts/openapi.yaml"  # JSON text despite the extension
MODEL_DIR = Path("data/private/nisar/model")
MANIFESTS = Path("data/manifests")
OUT_DIR = Path("data/local/radar_contract")
RELEASE_DELAY = dt.timedelta(hours=72)  # safety rule: public results 72 h after the pass
AREA_KEY = "south-lebanon-demo"

LIMITS = [
    "Candidate change, not confirmed damage",
    "Counts are minimums",
    "See docs/model_validation.md",
]


def load_spec() -> dict[str, Any]:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def validator(spec: dict[str, Any], name: str) -> Draft202012Validator:
    return Draft202012Validator({"components": spec["components"],
                                 "$ref": f"#/components/schemas/{name}"})


def iso(ts: str | dt.datetime) -> str:
    t = dt.datetime.fromisoformat(ts) if isinstance(ts, str) else ts
    return t.astimezone(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def plus_delay(ts: str) -> str:
    return iso(dt.datetime.fromisoformat(ts) + RELEASE_DELAY)


def area_metrics(cells: pd.DataFrame, *, metric_date: str, acquired_at: str, processed_at: str,
                 run_id: str, source_ids: list[str], with_s1: bool, tag: str) -> list[dict[str, Any]]:
    """MetricValue rows per H3 r8 area from r9 cells (aggregation only, never single cells)."""
    c = cells.copy()
    c["assessed"] = ~c["sparse_cell"] & ~c["low_coverage"] & c["damage_class"].ne("unknown")
    c["candidate"] = c["assessed"] & c["damage_class"].str.endswith("_candidate")
    if with_s1 and "evidence_label" in c:
        c["corroborated"] = c["candidate"] & (c["evidence_label"] == "corroborated")
    else:
        c["corroborated"] = False
    g = c.groupby("h3_r8").agg(assessed=("assessed", "sum"), candidates=("candidate", "sum"),
                               corroborated=("corroborated", "sum"))
    rows = []
    common = {
        "synthetic": False, "unit": "H3 r9 cells", "source": source_ids, "date": metric_date,
        "safety_tag": "restricted_aggregate", "lineage_ids": [run_id], "processing_run_id": run_id,
        "processing_version": f"nisar-anomaly-{MODEL_VERSION}", "confidence": None,
        "acquired_at": acquired_at, "processed_at": processed_at,
        "release_at": plus_delay(acquired_at), "freshness": "Stale", "cached": True,
    }
    for area, r in g.iterrows():
        assessed, cand, corr = int(r["assessed"]), int(r["candidates"]), int(r["corroborated"])
        if assessed == 0:
            low = high = None
            label = "Unknown"
        else:
            low, high = (corr, cand) if with_s1 else (cand, cand)
            label = "Corroborated" if corr > 0 else "Observed"
        note = ("Low: NISAR and Sentinel-1; high: NISAR" if with_s1 else "NISAR only")
        rows.append(common | {
            "value_id": f"nisar-{run_id}-{tag}-{area}-candidates", "area_id": area,
            "metric": "radar_candidate_change_cells", "low": low, "high": high, "label": label,
            "limitations": [*LIMITS, note]})
        rows.append(common | {
            "value_id": f"nisar-{run_id}-{tag}-{area}-assessed", "area_id": area,
            "metric": "radar_assessed_cells", "low": assessed if assessed else None,
            "high": assessed if assessed else None, "label": "Observed" if assessed else "Unknown",
            "limitations": ["Built-up cells with enough valid radar pixels"]})
    return rows


def missing_intervals(dates: list[str], step_days: int = 12) -> list[dict[str, str]]:
    """Group missing 12-day passes into intervals (never interpolated)."""
    days = sorted(dt.date.fromisoformat(d) for d in dates)
    out: list[dict[str, str]] = []
    for d in days:
        if out and (d - dt.date.fromisoformat(out[-1]["end"])).days == step_days:
            out[-1]["end"] = d.isoformat()
        else:
            out.append({"start": d.isoformat(), "end": d.isoformat(),
                        "reason": "No NISAR acquisition over this frame (source catalogue); not interpolated"})
    return out


def layer_records(change_index: dict[str, Any], crops: dict[str, Any], scenes: dict[str, Any],
                  source_ids: list[str]) -> list[dict[str, Any]]:
    acq = {v["date"]: next(s["selected"]["start"] for s in scenes["scenes"]
                           if s["product"] == "GCOV" and s["date"] == v["date"])
           for v in crops["crops"].values()}
    all_acq = sorted(iso(t) for t in acq.values())
    gaps = missing_intervals(scenes["missing_gcov_passes"])
    lon_lat = change_index["bounds_wgs84"]
    out = []
    for layer in change_index["layers"]:
        dates = sorted(layer["dates"])
        last = dates[-1]
        acquired = iso(acq[last]) if last in acq else iso(f"{last}T00:00:00Z")
        flagged = f" (flagged: {'; '.join(layer['flags'])})" if layer["flags"] else ""
        out.append({
            "synthetic": False, "layer_id": f"nisar-{layer['name'].lower().replace('_', '-')}",
            "title": f"NISAR {layer['kind'].replace('_', ' ')} {layer['polarization']} "
                     f"{dates[0]} to {last}{flagged}",
            "kind": "raster", "product": "NISAR GCOV",
            "analytical": layer["kind"].startswith("change"),
            "polarizations": [layer["polarization"]], "available_acquisitions": all_acq,
            "missing_intervals": gaps,
            "default_comparison": {"before": dates[0], "after": last},
            "tile_url": f"/api/v1/layers/nisar-{layer['name'].lower().replace('_', '-')}/tiles/{{z}}/{{x}}/{{y}}",
            "min_role": "analyst", "source_ids": source_ids, "label": "Observed", "date": last,
            "acquired_at": acquired, "processed_at": iso(change_index["created_at"]),
            "release_at": plus_delay(acquired), "freshness": "Stale", "cached": True,
            "public_resolution": 8, "safety_tag": "restricted_until_review",
            "extent": lon_lat,
            "attribution": "NISAR data NASA/ISRO via ASF DAAC; processing CIVISAR M1 (candidate change only)",
        })
    return out


def source_records(scenes: dict[str, Any], crops: dict[str, Any], s1: dict[str, Any] | None,
                   accessed: str) -> list[dict[str, Any]]:
    by_mat: dict[str, list[dict[str, Any]]] = {}
    for s in scenes["scenes"]:
        sel = s["selected"]
        if s["product"] == "GCOV" and s["tier"]:
            by_mat.setdefault(sel["maturity"], []).append(sel)
    base = {"synthetic": False, "accessed_at": accessed, "checksum": None, "live_tested": True}
    nisar_cov = {"area_id": AREA_KEY, "geometry": None, "track": 151, "frame": 72}
    out = []
    for mat, items in sorted(by_mat.items()):
        crids = sorted({i["crid"] for i in items})
        out.append(base | {
            "source_id": f"nisar-gcov-{mat.lower()}-151d72", "dataset_id": f"NISAR_L2_GCOV_{mat}",
            "name": f"NISAR L2 GCOV ({mat})", "provider": "NASA/ISRO via ASF DAAC",
            "product_level": "L2", "cmr_concept_id": items[0]["concept_id"],
            "challenge_provenance": "Tab", "source_url": "https://search.asf.alaska.edu/",
            "acquisition_start": iso(min(i["start"] for i in items)),
            "acquisition_end": iso(max(i["start"] for i in items)),
            "processing_version": f"{mat} (CRID {', '.join(crids)})",
            "spatial_coverage": nisar_cov, "resolution_m": 20,
            "licence": "NASA/ISRO NISAR open data; cite NISAR and ASF DAAC",
            "api": "ASF Search API + earthaccess", "independence_family": "nisar",
            "limits": [f"{len(items)} passes used; BETA products are not fully calibrated"]
                      if mat == "BETA" else [f"{len(items)} passes used"],
        })
    if s1:
        dates = sorted([*s1["before"], *s1["after"]])
        out.append(base | {
            "source_id": "s1-rtc-t021d", "dataset_id": "OPERA_L2_RTC-S1_V1",
            "name": "Sentinel-1 RTC (OPERA), track 21 descending", "provider": "ESA Copernicus, processed by NASA OPERA, via ASF DAAC",
            "product_level": "L2", "cmr_concept_id": s1["collection"], "challenge_provenance": "Tab tool",
            "source_url": "https://search.asf.alaska.edu/",
            "acquisition_start": f"{dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:]}T00:00:00Z",
            "acquisition_end": f"{dates[-1][:4]}-{dates[-1][4:6]}-{dates[-1][6:]}T00:00:00Z",
            "processing_version": "OPERA RTC-S1 v1.0",
            "spatial_coverage": {"area_id": AREA_KEY, "geometry": None, "track": 21, "frame": 0},
            "resolution_m": 30, "licence": "Copernicus Sentinel data (open; Sentinel EULA)",
            "api": "CMR + earthaccess", "independence_family": "sentinel-1",
            "limits": ["Used only as an independent cross-check; frame 0 = not applicable (bursts)"],
        })
    for sid, did, name, prov, lic, api, fam, res, lim in (
        ("osm-buildings-lbn", "hotosm_lbn_buildings", "OpenStreetMap buildings (HOTOSM export)",
         "OpenStreetMap contributors via HOTOSM / HDX", "ODbL; credit OpenStreetMap contributors",
         "HDX download", "osm", None, "Built-up mask only (buildings + 30 m); OSM coverage is incomplete"),
        ("ucdp-ged-candidate-2026", "GEDEvent_v26_01_26_09", "UCDP Candidate Events 2026 (Jan-Sep)",
         "Uppsala Conflict Data Program", "CC BY 4.0", "Download (ucdp.uu.se)", "ucdp", None,
         "Used only to choose quiet training areas and for the strike-context check"),
        ("nasadem-hgt", "NASADEM_HGT", "NASADEM elevation", "NASA/JPL via LP DAAC", "Open",
         "CMR + earthaccess", "nasadem", 30, "Terrain mask (layover, shadow, slope > 25 deg) only"),
    ):
        out.append(base | {
            "source_id": sid, "dataset_id": did, "name": name, "provider": prov,
            "product_level": "n/a", "cmr_concept_id": "n/a", "challenge_provenance": "Other",
            "source_url": {"osm": "https://data.humdata.org/dataset/hotosm_lbn_buildings",
                           "ucdp": "https://ucdp.uu.se/downloads/",
                           "nasadem": "https://lpdaac.usgs.gov/products/nasadem_hgtv001/"}[fam],
            "acquisition_start": "n/a", "acquisition_end": "n/a", "processing_version": "n/a",
            "spatial_coverage": {"area_id": AREA_KEY, "geometry": None, "track": 0, "frame": 0},
            "resolution_m": res, "licence": lic, "api": api, "independence_family": fam,
            "limits": [lim, "track/frame 0 = not applicable"],
        })
    return out


def validate_all(spec: dict[str, Any], name: str, records: list[dict[str, Any]]) -> None:
    v = validator(spec, name)
    for r in records:
        v.validate(r)


def write(path: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(records, separators=(",", ":"), ensure_ascii=False)
    path.write_text(data, encoding="utf-8", newline="\n")
    return {"path": path.as_posix(), "records": len(records),
            "sha256": hashlib.sha256(data.encode("utf-8")).hexdigest()}


def main() -> int:
    spec = load_spec()
    run = json.loads((MODEL_DIR / "run.json").read_text(encoding="utf-8"))
    scenes = json.loads((MANIFESTS / "nisar.json").read_text(encoding="utf-8"))
    crops = json.loads((MANIFESTS / "nisar_crops.json").read_text(encoding="utf-8"))
    change = json.loads((MANIFESTS / "nisar_change_index.json").read_text(encoding="utf-8"))
    s1_path = MANIFESTS / "s1_rtc.json"
    s1 = json.loads(s1_path.read_text(encoding="utf-8")) if s1_path.exists() else None
    cells = pd.read_parquet(MODEL_DIR / "damage_cells.parquet")
    with_s1 = "evidence_label" in cells.columns and s1 is not None

    from pyproj import Transformer
    b = change["bounds"]
    tr = Transformer.from_crs(change["crs_epsg"], 4326, always_xy=True)
    (w, s), (e, n) = tr.transform(b[0], b[1]), tr.transform(b[2], b[3])
    change["bounds_wgs84"] = [round(w, 4), round(s, 4), round(e, 4), round(n, 4)]

    accessed = iso(min(v["cropped_at"] for v in crops["crops"].values()))
    sources = source_records(scenes, crops, s1, accessed)
    nisar_ids = [x["source_id"] for x in sources if x["independence_family"] == "nisar"]
    maturity_of = {v["date"]: v["maturity"] for v in crops["crops"].values()}

    def used(dates: list[str]) -> list[str]:
        return [f"nisar-gcov-{m.lower()}-151d72" for m in sorted({maturity_of[d] for d in dates})]

    a_dates = [s["date"] for s in scenes["scenes"] if s["product"] == "GCOV" and s["tier"] in ("A-before", "A-after")]
    june = [s["date"] for s in scenes["scenes"] if s["product"] == "GCOV" and s["tier"] == "A-after"]
    s1_ids = [x["source_id"] for x in sources if x["independence_family"] == "sentinel-1"]

    after_acq = max(s["selected"]["start"] for s in scenes["scenes"]
                    if s["tier"] == "A-after" and s["product"] == "GCOV")
    values = area_metrics(cells, metric_date=after_acq[:10], acquired_at=iso(after_acq),
                          processed_at=iso(run["created_at"]), run_id=run["run_id"],
                          source_ids=used(a_dates) + (s1_ids if with_s1 else []), with_s1=with_s1,
                          tag="a")
    for p in sorted((MODEL_DIR / "slider").glob("*/damage_cells.parquet")):
        date = p.parent.name
        srun = json.loads((p.parent / "run.json").read_text(encoding="utf-8"))
        acq = next(s["selected"]["start"] for s in scenes["scenes"]
                   if s["product"] == "GCOV" and s["date"] == date)
        values += area_metrics(pd.read_parquet(p), metric_date=date, acquired_at=iso(acq),
                               processed_at=iso(srun["created_at"]), run_id=srun["run_id"],
                               source_ids=used([*june, date]), with_s1=False, tag=date)
    layers = layer_records(change, crops, scenes, nisar_ids)

    validate_all(spec, "MetricValue", values)
    validate_all(spec, "Layer", layers)
    validate_all(spec, "SourceRecord", sources)

    files = {"metric_values": write(OUT_DIR / "metric_values.json", values),
             "layers": write(OUT_DIR / "layers.json", layers),
             "sources": write(OUT_DIR / "sources.json", sources)}
    manifest = {
        "schema_version": "0.1", "kind": "radar_contract_export", "synthetic": False,
        "created_at": iso(dt.datetime.now(dt.UTC)), "run_id": run["run_id"],
        "contract": "docs/contracts/openapi.yaml components MetricValue, Layer, SourceRecord",
        "validated": True, "area_level": "H3 resolution 8 only",
        "safety": "MetricValue restricted_aggregate; Layer restricted_until_review (analyst+); "
                  "release_at = acquisition + 72 h",
        "files": files,
    }
    (MANIFESTS / "radar_contract.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8",
                                                   newline="\n")
    print(json.dumps({k: v["records"] for k, v in files.items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
