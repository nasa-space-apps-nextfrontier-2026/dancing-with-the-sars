"""Read the ML artifacts published by `worker.publish` (ML wiring, API side).

The API never computes anything per request: it reads small JSON files, withholds anything whose
`release_at` is still in the future, and filters by the caller's area scopes. A missing file means
"not available", never an invented value.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

CANDIDATE_CLASSES = ("possible_candidate", "moderate_candidate", "destroyed_or_severe_candidate")
MIN_PUBLIC_CELLS = 3      # a public r8 cell needs at least this many candidate cells


class Store:
    def __init__(self, directory: str | Path):
        self.dir = Path(directory)
        self._cache: dict[str, tuple[float, dict]] = {}

    def _load(self, name: str) -> dict | None:
        path = self.dir / name
        if not path.is_file():
            return None
        mtime = path.stat().st_mtime
        hit = self._cache.get(name)
        if hit and hit[0] == mtime:
            return hit[1]
        data = json.loads(path.read_text(encoding="utf-8"))
        self._cache[name] = (mtime, data)
        return data

    @staticmethod
    def _released(item: dict, now: datetime) -> bool:
        stamp = item.get("release_at")
        return bool(stamp) and datetime.fromisoformat(stamp) <= now

    @staticmethod
    def _in_scope(item: dict, scopes: tuple[str, ...]) -> bool:
        return "*" in scopes or item.get("area_id") in scopes or item.get("parent_r8") in scopes

    def status(self) -> dict:
        manifest = self._load("manifest.json")
        if not manifest:
            return {"synthetic": True, "sources": [], "message": "No published artifacts"}
        return {"synthetic": False, "sources": manifest["sources"]}

    def areas(self, scopes: tuple[str, ...], limit: int, offset: int) -> dict:
        damage = self._load("damage.json")
        if not damage or not self._released(damage, datetime.now(UTC)):
            return {"synthetic": False, "items": [], "next_cursor": None}
        rows = [i for i in damage["items"] if self._in_scope(i, scopes)]
        page = rows[offset:offset + limit]
        nxt = str(offset + limit) if offset + limit < len(rows) else None
        return {"synthetic": False, "next_cursor": nxt,
                "items": [{"area_id": r["area_id"], "h3_id": r["area_id"], "cadaster_code": None}
                          for r in page]}

    def damage(self, area_id: str) -> dict:
        damage = self._load("damage.json")
        items = []
        if damage and self._released(damage, datetime.now(UTC)):
            for r in damage["items"]:
                if r["area_id"] == area_id:
                    items.append({"area_id": r["area_id"], "candidate_class": r["candidate_class"],
                                  "score": r["score"], "reason_codes": r["reason_codes"],
                                  "run_id": r["run_id"]})
        return {"synthetic": False, "items": items, "next_cursor": None}

    def values(self, area_id: str) -> dict:
        data = self._load("values.json")
        now = datetime.now(UTC)
        items = [v for v in (data or {}).get("items", [])
                 if v["area_id"] == area_id and self._released(v, now)]
        return {"synthetic": False, "items": items, "next_cursor": None}

    def alerts(self, scopes: tuple[str, ...]) -> dict:
        data = self._load("alerts.json") or {"items": []}
        now = datetime.now(UTC)
        items = [a for a in data["items"] if self._released(a, now) and self._in_scope(a, scopes)]
        items.sort(key=lambda a: a["detected_at"], reverse=True)
        return {"synthetic": False, "items": items, "next_cursor": None}

    def alert(self, alert_id: str, scopes: tuple[str, ...]) -> dict | None:
        for a in self.alerts(scopes)["items"]:
            if a["alert_id"] == alert_id:
                return a
        return None

    def public_map(self, approved: bool) -> dict:
        """Delayed r8 aggregates only, and only after a person approved the release."""
        base = {"synthetic": False, "resolution": 8, "layers": [], "suppressed": True,
                "release_policy": "72h_and_review"}
        damage = self._load("damage.json")
        if not approved or not damage or not self._released(damage, datetime.now(UTC)):
            return base
        counts: dict[str, int] = {}
        for r in damage["items"]:
            if r["candidate_class"] in CANDIDATE_CLASSES:
                counts[r["parent_r8"]] = counts.get(r["parent_r8"], 0) + 1
        cells = [{"h3_id": cell, "candidate_cells": "3-5" if n <= 5 else "6-10" if n <= 10 else "11+"}
                 for cell, n in sorted(counts.items()) if n >= MIN_PUBLIC_CELLS]
        layer = {"layer_id": "public-damage-r8", "label": "Candidate radar change, delayed, area level",
                 "evidence": "Unknown", "cells": cells}
        return {**base, "layers": [layer], "suppressed": False}
