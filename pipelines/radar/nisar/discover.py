"""M1-01: find every NISAR scene for the demo track/frame and write a versioned manifest.

Metadata only: uses the public ASF Search API, needs no login and downloads no data.

    python -m pipelines.radar.nisar.discover --out data/manifests/nisar.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1"
ASF_SEARCH = "https://api.daac.asf.alaska.edu/services/search/param"
CONFIG_PATH = Path(__file__).parent / "config" / "demo_aoi.json"
REPEAT_DAYS = 12
MATURITY_RANK = {"BETA": 0, "PROVISIONAL": 1, "V1": 2}


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def maturity_of(collection_name: str) -> str:
    """BETA / PROVISIONAL / V1 from the CMR collection name."""
    name = collection_name.upper()
    if "_BETA_" in name:
        return "BETA"
    if "_PROVISIONAL_" in name:
        return "PROVISIONAL"
    if name.endswith("_V1"):
        return "V1"
    raise ValueError(f"Unknown NISAR product maturity: {collection_name}")


def search_asf(cfg: dict[str, Any], product: str, timeout: int = 180) -> list[dict[str, Any]]:
    """Raw ASF features for one product level over the AOI box."""
    b = cfg["bbox_wgs84"]
    params = {
        "dataset": "NISAR",
        "processingLevel": product,
        "bbox": f"{b['west']},{b['south']},{b['east']},{b['north']}",
        "output": "geojson",
        "maxResults": 2000,
    }
    url = f"{ASF_SEARCH}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "civisar-nisar-discover"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)["features"]


def to_record(feature: dict[str, Any]) -> dict[str, Any]:
    p = feature["properties"]
    h5_name = p.get("fileName") or f"{p['sceneName']}.h5"
    h5_bytes = (p.get("bytes") or {}).get(h5_name, {}).get("bytes")
    return {
        "scene": p["sceneName"],
        "product": p["processingLevel"],
        "collection": p["collectionName"],
        "concept_id": p.get("conceptID"),
        "maturity": maturity_of(p["collectionName"]),
        "crid": p.get("crid"),
        "pge_version": p.get("pgeVersion"),
        "track": p.get("pathNumber"),
        "frame": p.get("frameNumber"),
        "direction": p.get("flightDirection"),
        "start": p["startTime"],
        "stop": p.get("stopTime"),
        "date": p["startTime"][:10],
        "processing_date": p.get("processingDate"),
        "frame_coverage": p.get("frameCoverage"),
        "range_bandwidth": p.get("rangeBandwidth"),
        "polarizations": p.get("mainBandPolarization"),
        "url": p.get("url"),
        "file_name": h5_name,
        "h5_bytes": h5_bytes,
        "footprint": feature.get("geometry"),
    }


def on_demo_track(rec: dict[str, Any], cfg: dict[str, Any]) -> bool:
    return (
        rec["track"] == cfg["track"]
        and rec["frame"] == cfg["frame"]
        and (rec["direction"] or "").upper() == cfg["direction"]
    )


def _in(date: str, window: dict[str, str]) -> bool:
    return window["start"] <= date <= window["end"]


def assign_tier(rec: dict[str, Any], cfg: dict[str, Any]) -> str | None:
    tiers = cfg["tiers"]
    d, product = rec["date"], rec["product"]
    if product == "GCOV":
        if _in(d, tiers["A"]["before"]):
            return "A-before"
        if _in(d, tiers["A"]["after"]):
            return "A-after"
        if _in(d, tiers["B"]["window"]):
            return "B"
    if product == "GSLC" and d in tiers["C"]["gslc_dates"]:
        return "C"
    if product == "GUNW" and d in tiers["C"]["gunw_dates"]:
        return "C"
    return None


def pick_version(versions: list[dict[str, Any]]) -> dict[str, Any]:
    """Highest maturity, then newest processing. All versions stay in the manifest."""
    return max(versions, key=lambda r: (MATURITY_RANK[r["maturity"]], r["processing_date"] or ""))


def missing_passes(dates: Iterable[str]) -> list[str]:
    """Expected 12-day repeat dates between the first and last pass with no product."""
    have = sorted({dt.date.fromisoformat(d) for d in dates})
    if not have:
        return []
    out, day = [], have[0]
    present = set(have)
    while day <= have[-1]:
        if day not in present:
            out.append(day.isoformat())
        day += dt.timedelta(days=REPEAT_DAYS)
    return out


def build_manifest(features: list[dict[str, Any]], cfg: dict[str, Any]) -> dict[str, Any]:
    records = [to_record(f) for f in features]
    rejected = [r["scene"] for r in records if not on_demo_track(r, cfg)]
    records = [r for r in records if on_demo_track(r, cfg)]

    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        groups[(r["product"], r["date"])].append(r)

    scenes = []
    for (product, date), versions in sorted(groups.items()):
        chosen = pick_version(versions)
        scenes.append({
            "product": product,
            "date": date,
            "tier": assign_tier(chosen, cfg),
            "selected": chosen,
            "other_versions": [v["scene"] for v in versions if v is not chosen],
        })

    warnings = []
    by_tier: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for s in scenes:
        if s["tier"]:
            by_tier[s["tier"]].append(s)
    before = {s["selected"]["maturity"] for s in by_tier.get("A-before", [])}
    after = {s["selected"]["maturity"] for s in by_tier.get("A-after", [])}
    if before and after and before != after:
        warnings.append(
            f"version_confounded: tier A before={sorted(before)} vs after={sorted(after)}; "
            "stable-area normalization and QA required before any comparison"
        )
    for tier in ("A-before", "A-after", "B"):
        if not by_tier.get(tier):
            warnings.append(f"tier {tier} has no scenes")
        crids = sorted({s["selected"]["crid"] or "?" for s in by_tier.get(tier, [])})
        if len(crids) > 1:
            warnings.append(f"mixed_crid: tier {tier} uses {crids}; check processing differences within the tier")

    gcov_dates = [s["date"] for s in scenes if s["product"] == "GCOV"]
    totals = {
        tier: {
            "scenes": len(items),
            "bytes": sum(i["selected"]["h5_bytes"] or 0 for i in items),
        }
        for tier, items in sorted(by_tier.items())
    }
    body = {
        "schema_version": SCHEMA_VERSION,
        "kind": "nisar_scene_manifest",
        "synthetic": False,
        "aoi": cfg["name"],
        "bbox_wgs84": cfg["bbox_wgs84"],
        "track": cfg["track"],
        "frame": cfg["frame"],
        "direction": cfg["direction"],
        "source": ASF_SEARCH,
        "licence": "NASA/ISRO NISAR data, open (cite NISAR and ASF DAAC)",
        "tiers": totals,
        "missing_gcov_passes": missing_passes(gcov_dates),
        "rejected_other_tracks": len(rejected),
        "warnings": warnings,
        "scenes": scenes,
    }
    key = json.dumps([s["selected"]["scene"] for s in scenes], sort_keys=True)
    body["run_id"] = hashlib.sha256(key.encode()).hexdigest()[:16]
    body["generated_at"] = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
    return body


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", type=Path, default=CONFIG_PATH)
    ap.add_argument("--out", type=Path, default=Path("data/manifests/nisar.json"))
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    features: list[dict[str, Any]] = []
    for product in cfg["products"]:
        features += search_asf(cfg, product)
    manifest = build_manifest(features, cfg)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for tier, t in manifest["tiers"].items():
        print(f"tier {tier}: {t['scenes']} scenes, {t['bytes'] / 1e9:.2f} GB")
    print("missing GCOV passes:", ", ".join(manifest["missing_gcov_passes"]) or "none")
    for w in manifest["warnings"]:
        print("WARNING:", w)
    print(f"wrote {args.out} (run {manifest['run_id']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
