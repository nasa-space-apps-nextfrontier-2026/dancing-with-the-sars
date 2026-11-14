"""Event point loaders for the strike tests (task M1-04, model C). Standard library only.

The event source is UCDP GED (open conflict events), not ACLED: ACLED's terms do not allow using its
data to test ML models. The UCDP API needs a free access token, so this module also reads a plain
CSV export, so the tests can run once someone downloads the Lebanon events.
"""
from __future__ import annotations

import csv
import json
from collections.abc import Iterable

from worker.evaluation.strike_tests import Event


def from_ucdp_json(payload: dict | str, start: str | None = None, end: str | None = None) -> list[Event]:
    """Parse a UCDP GED API response (`{"Result": [{...}]}`); keep events inside [start, end] dates."""
    data = json.loads(payload) if isinstance(payload, str) else payload
    out = []
    for row in data.get("Result", []):
        day = str(row.get("date_start", ""))[:10]
        if (start and day < start) or (end and day > end):
            continue
        if row.get("latitude") is None or row.get("longitude") is None:
            continue
        out.append(Event(float(row["latitude"]), float(row["longitude"])))
    return out


def from_csv(lines: Iterable[str], lat: str = "latitude", lon: str = "longitude",
             date: str | None = "date_start", start: str | None = None,
             end: str | None = None) -> list[Event]:
    """Parse a CSV export with latitude/longitude columns (UCDP GED download or similar)."""
    out = []
    for row in csv.DictReader(lines):
        if date and (start or end):
            day = row.get(date, "")[:10]
            if (start and day < start) or (end and day > end):
                continue
        try:
            out.append(Event(float(row[lat]), float(row[lon])))
        except (KeyError, ValueError):
            continue
    return out
