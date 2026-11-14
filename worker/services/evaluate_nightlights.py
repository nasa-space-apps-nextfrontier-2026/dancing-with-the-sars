"""Run the night-light rule on the real per-cell history and measure its false-alarm rate.

Input: the gzip CSV from blackmarble_history.py. Standard library only, runs anywhere.
    python -m worker.services.evaluate_nightlights bm_history.csv.gz [out.json]

Two outputs:
  * hold-out: slide the rule over the last nights. Almost every cell is quiet, so the share of
    assessable cells flagged is a direct estimate of the false-alarm rate.
  * latest: what the rule says today for each satellite (counts of possible_power_loss, no_change,
    unknown) and which cells were flagged.
"""
from __future__ import annotations

import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from worker.services.nightlights import Night, assess

CLEAR_SHARE = 0.5      # a cell night is clear when at least half its pixels are clear
HOLDOUT_NIGHTS = 45


def load(path: str) -> dict[tuple[str, str], list[Night]]:
    series: dict[tuple[str, str], list[Night]] = defaultdict(list)
    with gzip.open(path, "rt", newline="") as f:
        for row in csv.DictReader(f):
            n_pix, n_clear = int(row["n_pixels"]), int(row["n_clear"])
            clear = n_pix > 0 and n_clear / n_pix >= CLEAR_SHARE and row["mean_radiance"] != ""
            radiance = float(row["mean_radiance"]) if row["mean_radiance"] != "" else None
            series[(row["satellite"], row["cell"])].append(Night(row["date"], radiance, clear))
    for nights in series.values():
        nights.sort(key=lambda n: n.date)
    return series


def evaluate(series: dict[tuple[str, str], list[Night]], holdout: int = HOLDOUT_NIGHTS) -> dict:
    out: dict = {}
    for satellite in sorted({s for s, _ in series}):
        counts, latest, flagged = Counter(), Counter(), []
        runs = 0
        for (sat, cell), nights in series.items():
            if sat != satellite or len(nights) < 4:
                continue
            for i in range(max(2, len(nights) - holdout), len(nights) + 1):
                result = assess(nights[:i - 2], nights[i - 2:i])
                counts[result.status] += 1
                runs += 1
                if i == len(nights):
                    latest[result.status] += 1
                    if result.status == "possible_power_loss":
                        flagged.append({"cell": cell, "confidence": result.confidence,
                                        "ratio": round(result.ratio, 3), "baseline": round(result.baseline, 2)})
        assessable = counts["possible_power_loss"] + counts["no_change"]
        out[satellite] = {
            "cells": len({c for s, c in series if s == satellite}),
            "holdout_assessments": runs, "holdout_counts": dict(counts),
            "holdout_false_alarm_rate": (counts["possible_power_loss"] / assessable) if assessable else None,
            "latest_counts": dict(latest), "latest_flagged": sorted(flagged, key=lambda x: x["ratio"])[:25],
        }
    return out


def main(argv: list[str]) -> int:
    result = evaluate(load(argv[1]))
    text = json.dumps(result, indent=2)
    if len(argv) > 2:
        Path(argv[2]).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
