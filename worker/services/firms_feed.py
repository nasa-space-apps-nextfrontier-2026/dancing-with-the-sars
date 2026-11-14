"""Live fire points from NASA FIRMS public CSV files (task M1-04, model B input).

No map key is needed: FIRMS publishes global VIIRS 375 m files for the last 24 hours, 48 hours and
7 days. A key is only needed for the history API (a longer baseline for permanent hot spots).
Standard library only. The files are about 60 MB, so they are streamed and filtered to the demo box.
"""
from __future__ import annotations

import csv
import io
import urllib.request
from collections.abc import Iterable
from datetime import datetime

from worker.services.fires import FireEvent, FirePoint, fire_events

BASE = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/"
FEEDS = {
    "NOAA-20": "noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_{window}.csv",
    "NOAA-21": "noaa-21-viirs-c2/csv/J2_VIIRS_C2_Global_{window}.csv",
}
WINDOWS = ("24h", "48h", "7d")
DEMO_BBOX = (35.0, 33.0, 36.0, 33.6)   # west, south, east, north


def feed_url(satellite: str, window: str = "24h") -> str:
    if satellite not in FEEDS or window not in WINDOWS:
        raise ValueError(f"unknown feed {satellite!r} / {window!r}")
    return BASE + FEEDS[satellite].format(window=window)


def _time(row: dict) -> str:
    hhmm = row["acq_time"].zfill(4)
    return f"{row['acq_date']}T{hhmm[:2]}:{hhmm[2:]}:00+00:00"


def parse_points(lines: Iterable[str], satellite: str, bbox=DEMO_BBOX) -> list[FirePoint]:
    west, south, east, north = bbox
    out = []
    for row in csv.DictReader(lines):
        lat, lon = float(row["latitude"]), float(row["longitude"])
        if west <= lon <= east and south <= lat <= north:
            out.append(FirePoint(lat, lon, _time(row), row["confidence"], satellite))
    return out


def fetch_points(satellite: str, window: str = "24h", bbox=DEMO_BBOX, opener=None) -> list[FirePoint]:
    """Download one feed and keep only the points inside `bbox` (streamed, not stored)."""
    request = urllib.request.Request(feed_url(satellite, window), headers={"User-Agent": "civisar/0.1"})
    with (opener or urllib.request.urlopen)(request, timeout=300) as response:
        return parse_points(io.TextIOWrapper(response, encoding="utf-8"), satellite, bbox)


def current_events(bbox=DEMO_BBOX, fetch=fetch_points) -> tuple[list[FireEvent], dict]:
    """Fire events for the latest day in the 7-day feeds, with the 7-day points as the baseline."""
    points: list[FirePoint] = []
    for satellite in FEEDS:
        points += fetch(satellite, "7d", bbox)
    if not points:
        return [], {"points": 0, "latest_day": None, "note": "no detections in the demo box"}
    latest = max(datetime.fromisoformat(p.time).date() for p in points).isoformat()
    today = [p for p in points if p.time[:10] == latest]
    events = fire_events(today, points)
    return events, {"points": len(points), "latest_day": latest, "points_latest_day": len(today),
                    "note": "baseline is only 7 days, so permanent hot spots need 5 days of detections"}
