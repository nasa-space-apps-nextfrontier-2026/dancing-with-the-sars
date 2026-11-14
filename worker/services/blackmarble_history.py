"""Build the per-cell night-light history for the demo box (task M1-04, model A input).

Runs on Google Colab (needs h5py, numpy, h3 and an Earthdata token in /content/.earthdata_token).
For each recent night (NOAA-20 and NOAA-21, archive plus near real time) it downloads the h21v05
tile (about 20 MB), crops it to the demo box, keeps only the small per-cell numbers and deletes the
tile. Output: a gzip CSV with one row per satellite, night and H3 res-8 cell:
    date, satellite, cell, mean_radiance, n_pixels, n_clear

A pixel is "clear" when Mandatory_Quality_Flag is 0, cloud detection (QF_Cloud_Mask bits 6-7) is 0
(confident clear) and the radiance is valid. Usage on Colab:  python bm_history.py [days]
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

BBOX = (35.0, 33.0, 36.0, 33.6)           # west, south, east, north
PRODUCTS = {"NOAA-20": ("VJ146A2", "VJ146A2_NRT"), "NOAA-21": ("VJ246A2", "VJ246A2_NRT")}
H3_RES = 8
TOKEN_FILE = "/content/.earthdata_token"
WORK = "/content/bm"
OUT = "/content/out/bm_history.csv.gz"


def cmr_granules(short_name: str, start: str) -> list[dict]:
    query = urllib.parse.urlencode({
        "short_name": short_name, "bounding_box": ",".join(map(str, BBOX)),
        "temporal": f"{start}T00:00:00Z,", "page_size": 200, "sort_key": "start_date"})
    with urllib.request.urlopen("https://cmr.earthdata.nasa.gov/search/granules.json?" + query,
                                timeout=60) as response:
        entries = json.load(response)["feed"]["entry"]
    out = []
    for e in entries:
        links = [x["href"] for x in e.get("links", [])
                 if x.get("rel", "").endswith("/data#") and x["href"].startswith("https")
                 and x["href"].endswith(".h5")]
        if links:
            out.append({"date": e["time_start"][:10], "title": e["title"], "url": links[0]})
    return out


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def download(url: str, path: str, token: str) -> None:
    """Fetch with the Earthdata bearer token; follow a signed redirect without the token."""
    opener = urllib.request.build_opener(_NoRedirect)
    target = url
    try:
        response = opener.open(urllib.request.Request(url, headers={"Authorization": "Bearer " + token}),
                               timeout=120)
    except urllib.error.HTTPError as error:
        if error.code not in (301, 302, 303, 307, 308):
            raise
        target = error.headers["Location"]
        response = urllib.request.urlopen(target, timeout=300)
    with response, open(path, "wb") as f:
        while chunk := response.read(1 << 20):
            f.write(chunk)


def crop_rows(path: str, cell_index, n_cells: int, window) -> list[tuple]:
    import h5py
    import numpy as np
    rows, cols = window
    with h5py.File(path, "r") as h:
        def field(name):
            found = []
            h.visititems(lambda n, o: found.append(n) if n.split("/")[-1] == name else None)
            return h[found[0]][rows, cols]
        ntl = field("DNB_BRDF-Corrected_NTL").astype("float64")
        quality = field("Mandatory_Quality_Flag")
        cloud = (field("QF_Cloud_Mask") >> 6) & 3
    valid = np.isfinite(ntl) & (ntl >= 0) & (ntl < 60000)
    clear = valid & (quality == 0) & (cloud == 0)
    flat = cell_index.ravel()
    n_pix = np.bincount(flat, minlength=n_cells)
    n_clear = np.bincount(flat, weights=clear.ravel(), minlength=n_cells)
    total = np.bincount(flat, weights=np.where(clear, ntl, 0).ravel(), minlength=n_cells)
    mean = np.divide(total, n_clear, out=np.full(n_cells, np.nan), where=n_clear > 0)
    return [(i, mean[i], int(n_pix[i]), int(n_clear[i])) for i in range(n_cells) if n_pix[i] > 0]


def main(days: int = 120) -> None:
    import h3
    import h5py
    import numpy as np
    with open(TOKEN_FILE) as token_file:
        token = token_file.read().strip()
    os.makedirs(WORK, exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    start = (date.today() - timedelta(days=days)).isoformat()
    jobs = []
    for satellite, (archive, nrt) in PRODUCTS.items():
        seen = {}
        for g in cmr_granules(archive, start) + cmr_granules(nrt, start):
            seen.setdefault(g["date"], g)      # archive first: it wins when both exist
        jobs += [(satellite, g) for g in seen.values()]
    print("granules", len(jobs), flush=True)
    first = os.path.join(WORK, "first.h5")
    download(jobs[0][1]["url"], first, token)
    with h5py.File(first, "r") as h:
        found = []
        h.visititems(lambda n, o: found.append(n) if n.split("/")[-1] in ("lat", "lon") else None)
        lat = h[next(n for n in found if n.endswith("lat"))][:]
        lon = h[next(n for n in found if n.endswith("lon"))][:]
    r = np.where((lat >= BBOX[1]) & (lat <= BBOX[3]))[0]
    c = np.where((lon >= BBOX[0]) & (lon <= BBOX[2]))[0]
    window = (slice(r.min(), r.max() + 1), slice(c.min(), c.max() + 1))
    cells, index = {}, np.zeros((len(r), len(c)), dtype=np.int64)
    for i, la in enumerate(lat[r]):
        for j, lo in enumerate(lon[c]):
            index[i, j] = cells.setdefault(h3.latlng_to_cell(float(la), float(lo), H3_RES), len(cells))
    names = {v: k for k, v in cells.items()}
    print("pixels", index.size, "cells", len(cells), flush=True)

    def work(job):
        satellite, g = job
        path = os.path.join(WORK, g["title"] + ".h5")
        for attempt in range(3):
            try:
                download(g["url"], path, token)
                rows = crop_rows(path, index, len(cells), window)
                os.remove(path)
                return [(g["date"], satellite, names[i], m, n, k) for i, m, n, k in rows]
            except Exception as error:               # noqa: BLE001  keep going, report at the end
                last = f"{type(error).__name__}: {str(error)[:80]}"
        return ("failed", g["date"], satellite, last)

    results, failed, done = [], [], 0
    with ThreadPoolExecutor(4) as pool:
        for res in pool.map(work, jobs):
            done += 1
            if res and res[0] == "failed":
                failed.append(res[1:])
            else:
                results += res
            if done % 20 == 0:
                print(f"progress {done}/{len(jobs)} failed={len(failed)}", flush=True)
    with gzip.open(OUT, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "satellite", "cell", "mean_radiance", "n_pixels", "n_clear"])
        w.writerows((d, s, cell, "" if math.isnan(m) else round(m, 4), n, k) for d, s, cell, m, n, k in results)
    print("rows", len(results), "failed", failed[:5], "done", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 120)
