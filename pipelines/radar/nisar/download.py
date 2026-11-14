"""M1-01: get the selected NISAR GCOV scenes for chosen tiers and crop them to the demo box.

Two modes:
  --mode remote   read only the AOI window over HTTPS (earthaccess.open); no full download
  --mode full     download the whole .h5 file, verify its size, then crop

Needs a free Earthdata Login in the user's netrc file. Never prompts for a password.

    python -m pipelines.radar.nisar.download --tiers A-before A-after --dry-run
    python -m pipelines.radar.nisar.download --tiers A-before A-after --mode remote
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from .crop import crop_file
from .discover import CONFIG_PATH, load_config

RAW_DIR = Path("data/raw/nisar")
CROP_DIR = Path("data/private/nisar/crops")
CROP_INDEX = Path("data/manifests/nisar_crops.json")


def selected_scenes(manifest: dict[str, Any], tiers: list[str],
                    products: tuple[str, ...] = ("GCOV",)) -> list[dict[str, Any]]:
    return [s["selected"] | {"tier": s["tier"]} for s in manifest["scenes"]
            if s["tier"] in tiers and s["product"] in products]


def login() -> Any:
    import earthaccess
    from earthaccess.exceptions import LoginStrategyUnavailable

    for strategy in ("environment", "netrc"):
        try:
            auth = earthaccess.login(strategy=strategy, persist=False)
        except LoginStrategyUnavailable as exc:
            print(f"Earthdata login via {strategy}: not set up ({exc.args[0] if exc.args else exc})")
            continue
        if auth and getattr(auth, "authenticated", False):
            return earthaccess
    raise SystemExit(
        "Earthdata login not found. Set EARTHDATA_TOKEN (or EARTHDATA_USERNAME and "
        "EARTHDATA_PASSWORD), or add a 'machine urs.earthdata.nasa.gov' line to your netrc file."
    )


def fetch_full(ea: Any, scene: dict[str, Any]) -> Path:
    final = RAW_DIR / scene["file_name"]
    if final.exists() and final.stat().st_size == scene["h5_bytes"]:
        return final
    partial = RAW_DIR / ".partial"
    partial.mkdir(parents=True, exist_ok=True)
    paths = ea.download([scene["url"]], local_path=str(partial))
    got = Path(paths[0])
    if scene["h5_bytes"] and got.stat().st_size != scene["h5_bytes"]:
        raise RuntimeError(f"Size mismatch for {scene['scene']}: {got.stat().st_size} != {scene['h5_bytes']}")
    shutil.move(str(got), final)
    return final


def load_index() -> dict[str, Any]:
    if CROP_INDEX.exists():
        return json.loads(CROP_INDEX.read_text(encoding="utf-8"))
    return {"schema_version": "0.1", "kind": "nisar_crop_index", "synthetic": False, "crops": {}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=Path("data/manifests/nisar.json"))
    ap.add_argument("--config", type=Path, default=CONFIG_PATH)
    ap.add_argument("--tiers", nargs="+", default=["A-before", "A-after", "B"])
    ap.add_argument("--mode", choices=["remote", "full"], default="full",
                    help="full is the tested default; remote timed out on 14 Nov 2026")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="only the first N scenes (for a test)")
    ap.add_argument("--delete-raw", action="store_true", help="delete each full file after cropping")
    ap.add_argument("--raw-only", action="store_true",
                    help="download full files of any product (GSLC, GUNW) without cropping")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    products = ("GCOV", "GSLC", "GUNW") if args.raw_only else ("GCOV",)
    scenes = selected_scenes(manifest, args.tiers, products)
    if args.limit:
        scenes = scenes[: args.limit]
    total = sum(s["h5_bytes"] or 0 for s in scenes)
    print(f"{len(scenes)} scenes, full files {total / 1e9:.2f} GB")
    for s in scenes:
        print(f"  {s['tier']:<9} {s['date']} {s['maturity']:<11} {s['file_name']}")
    if args.dry_run:
        return 0

    ea = login()
    if args.raw_only:
        for s in scenes:
            t0 = time.time()
            path = fetch_full(ea, s)
            print(f"downloaded {path.name} ({s['h5_bytes'] / 1e9:.2f} GB) in {time.time() - t0:.0f} s")
        return 0

    index = load_index()
    for s in scenes:
        if s["scene"] in index["crops"]:
            print("skip (already cropped):", s["scene"])
            continue
        t0 = time.time()
        if args.mode == "remote":
            fobj = ea.open([s["url"]])[0]
            try:
                summary = crop_file(fobj, CROP_DIR, s["scene"], cfg["bbox_wgs84"])
            finally:
                fobj.close()
        else:
            path = fetch_full(ea, s)
            summary = crop_file(path, CROP_DIR, s["scene"], cfg["bbox_wgs84"])
            if args.delete_raw:
                path.unlink()
        index["crops"][s["scene"]] = {
            "tier": s["tier"], "date": s["date"], "maturity": s["maturity"], "crid": s["crid"],
            "mode": args.mode, "seconds": round(time.time() - t0, 1),
            "cropped_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            **{k: summary[k] for k in ("epsg", "pixel_spacing_m", "shape", "bounds", "outputs")},
        }
        CROP_INDEX.parent.mkdir(parents=True, exist_ok=True)
        CROP_INDEX.write_text(json.dumps(index, indent=2), encoding="utf-8")
        print(f"cropped {s['scene']} in {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
