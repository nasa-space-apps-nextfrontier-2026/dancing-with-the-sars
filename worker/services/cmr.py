"""Find Black Marble granules for the demo box with NASA's CMR search API.

Standard library only, so the same file runs on a laptop and on Google Colab without installs.
Search needs no login. Downloading the files later needs an Earthdata Login token.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass

CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
# South Lebanon demo box: west, south, east, north (decimal degrees).
DEMO_BBOX = (35.0, 33.0, 36.0, 33.6)
# Daily gap-filled night-light products: NOAA-20 and NOAA-21, near real time and archive.
BLACK_MARBLE = ("VJ146A2_NRT", "VJ246A2_NRT", "VJ146A2", "VJ246A2")


@dataclass(frozen=True)
class Granule:
    short_name: str
    granule_id: str
    title: str
    time_start: str
    time_end: str
    download_url: str | None


def build_query(short_name: str, bbox=DEMO_BBOX, start: str | None = None,
                end: str | None = None, page_size: int = 200, page_num: int = 1) -> str:
    params = {
        "short_name": short_name,
        "bounding_box": ",".join(str(v) for v in bbox),
        "page_size": page_size,
        "page_num": page_num,
        "sort_key": "-start_date",
    }
    if start or end:
        params["temporal"] = f"{_day(start, 'T00:00:00Z')},{_day(end, 'T23:59:59Z')}"
    return CMR_URL + "?" + urllib.parse.urlencode(params)


def _day(value: str | None, suffix: str) -> str:
    """Accept YYYY-MM-DD or a full timestamp; empty stays empty (open-ended)."""
    if not value:
        return ""
    return value + suffix if len(value) == 10 else value


def parse_response(short_name: str, payload: dict) -> list[Granule]:
    rows = []
    for item in payload.get("feed", {}).get("entry", []):
        links = [x.get("href") for x in item.get("links", [])
                 if x.get("rel", "").endswith("/data#") and x.get("href", "").startswith("https")]
        rows.append(Granule(short_name, item.get("id", ""), item.get("title", ""),
                            item.get("time_start", ""), item.get("time_end", ""),
                            links[0] if links else None))
    return rows


def search(short_name: str, bbox=DEMO_BBOX, start: str | None = None, end: str | None = None,
           max_pages: int = 10, fetch=None) -> list[Granule]:
    """Return granules newest first. `fetch(url) -> dict` can be replaced in tests."""
    fetch = fetch or _fetch
    out: list[Granule] = []
    for page in range(1, max_pages + 1):
        rows = parse_response(short_name, fetch(build_query(short_name, bbox, start, end, 200, page)))
        out.extend(rows)
        if len(rows) < 200:
            break
    return out


def _fetch(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def manifest(granules: list[Granule]) -> dict:
    by_product: dict[str, list[str]] = {}
    for g in granules:
        by_product.setdefault(g.short_name, []).append(g.time_start[:10])
    return {
        "bbox_w_s_e_n": list(DEMO_BBOX),
        "counts": {k: len(v) for k, v in by_product.items()},
        "newest": {k: max(v) for k, v in by_product.items() if v},
        "oldest": {k: min(v) for k, v in by_product.items() if v},
        "granules": [asdict(g) for g in granules],
    }
