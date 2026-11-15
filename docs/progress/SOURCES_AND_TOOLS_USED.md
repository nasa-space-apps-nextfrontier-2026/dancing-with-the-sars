# Sources, APIs and tools used (status on 15 November 2026)

One page for the submission and the citations: which data, APIs and software CIVISAR uses, and which of them come from the challenge **Resources tab**. Details per dataset (concept IDs, versions, limits) stay in [DATASETS.md](../DATASETS.md) and [DATASET_RECORDS_THANOBAN.md](DATASET_RECORDS_THANOBAN.md). Status words: **Used** (already run or in the app), **Planned** (decided, not built or not loaded yet), **Dropped** (checked and rejected). Licence or terms marked **VERIFY** must be read before the submission.

## 1. From the challenge Resources tab (separate list)

Source: [Dancing with the SARs, Resources tab](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=resources). I read the page on 15 November 2026. It has **14 links** and no data download of its own. The required "at least one Resources-tab resource" is met through links 1 to 3: NISAR is the challenge's mission and its files are found and downloaded through those three.

| # | Resource on the tab | Status | How CIVISAR uses it |
|---|---|---|---|
| 1 | NASA Earthdata Search | **Used** | CMR search for every NASA dataset (NISAR, OPERA, Black Marble, FIRMS, NASADEM); Earthdata Login token for downloads |
| 2 | ASF Data Search Vertex | **Used** | NISAR L2 GCOV and GSLC, and OPERA RTC-S1, found with the ASF Search API (336 NISAR granules over south Lebanon; track 151 descending is the time series) |
| 3 | NISAR Data User Guide | **Used** | Product definitions, processing versions and limits for the radar model |
| 4 | Intro to Remote Sensing | Learning only | Team background |
| 5 | Intro to Synthetic Aperture Radar (SAR) | Learning only | Team background, explanation text |
| 6 | NASA ARSET Trainings | Learning only | Team background |
| 7 | NISAR StoryMaps | Learning only | Presentation ideas |
| 8 | NISAR Applications White Papers | Learning only | Use-case framing |
| 9 | UAVSAR Postcards | Learning only | Presentation ideas |
| 10 | Radarsat Constellation Mission (RCM) data | **Dropped** | No open data over Lebanon |
| 11 | SAR Python tutorial (CSA) | Learning only | Code reference only; no code copied |
| 12 | RADARSAT-1 data | **Dropped** | No open data over Lebanon |
| 13 | SAOCOM catalogue | **Dropped** | Needs registration; coverage not confirmed |
| 14 | SAOCOM catalogue registration | **Dropped** | Same as 13 |

NASA datasets reached through tools 1 and 2 (they are not listed on the tab by name):

| Dataset | Status | Notes |
|---|---|---|
| NISAR L2 GCOV / GSLC | **Used** | Radar damage model (Udula), merged in PRs #15 to #17. Results are candidates, not confirmed damage |
| OPERA RTC-S1 (Sentinel-1) | **Used** | Second-sensor check: 13 cells where a second radar agrees |
| Black Marble VJ146A2 / VJ246A2 (+ NRT) | **Used** | Night-light history and "possible power loss" alerts (Thanoban) |
| FIRMS VIIRS 375 m | **Used** | Live fire points from the public CSV feed, no map key needed |
| NASADEM | **Planned** | Slope check for open-land shelter sites |

**Wording fixed (15 November 2026):** `DATASETS.md` no longer says NISAR is "named directly on the tab". The tab does not name the NISAR dataset; it links ASF Vertex, Earthdata Search and the NISAR user guide. Do not repeat the earlier "five or six" count.

## 2. Other data (not from the Resources tab)

| Data | Status | Use | Terms |
|---|---|---|---|
| OpenStreetMap / HOTOSM buildings, roads, facilities | **Used** (268,536 buildings in the demo box) | Footprints, building types, facilities, roads | ODbL; credit "© OpenStreetMap contributors" |
| GHSL building height (GHS-OBAT, EU JRC) | **Used** | Building height when OSM has no floor count; gives a range | CC BY 4.0 |
| Esri World Imagery and "Streets & labels" tiles | **Used** in the map | Satellite ground imagery, capture dates vary | **VERIFY** Esri terms and credit line |
| OpenStreetMap raster tiles | **Used** in the map (Streets base) | Streets base map | **VERIFY** the OSM tile usage policy (light use only) |
| World Bank damage and needs assessment (Syria, Aug 2025) | **Used** | Anchor for rebuild cost per m2, widened for Lebanon | Public report; cite it |
| World Bank Lebanon assessment (2025) | **Planned** | Check of the budget's cost per m2 | Public report |
| WorldPop | **Planned** (waits for the population file, K-04) | People ranges per H3 r9 cell | CC BY 4.0, **VERIFY** |
| OCHA administrative boundaries (HDX) | **Planned** (K-01) | Area names and joins | **VERIFY** |
| Facilities, shelters, roads | **Planned** (K-03, M2-04, M2-05) | Impact, shelters and routes | Follows OSM |
| UCDP GED | **Planned**, not downloaded | Strike context for the strike tests | **VERIFY** on download |
| IODA, IOM DTM, Meta movement maps, Insecurity Insight | **Planned** in `DATASETS.md`, not started | Outages, displacement, reported attacks | **VERIFY** |
| GIBS map layers | **Planned**, not in the app yet | Dated true-colour and night-light backgrounds | NASA open data |
| ACLED | **Dropped** | Its terms bar use for ML testing | n/a |
| 3D-GloBFP | **Dropped** | All authors at Chinese institutions (our rule) and 40 GB | n/a |

All map content is **sample data** until the incident endpoints (U-06) are merged and the frontend switches to real data.

## 3. APIs and services

| Service | Status | Key or login |
|---|---|---|
| ASF Search API (`asf_search`) | Used | none to search |
| NASA CMR search | Used | none to search |
| Earthdata Login and `earthaccess` | Used | free account token; the near-real-time Black Marble service also needs the Earthdata application "LANCE" authorised |
| LAADS DAAC and LANCE downloads | Used | Earthdata token |
| FIRMS public CSV feed | Used | none; the FIRMS map key is optional (long fire history) |
| Cesium ion (World Terrain, OSM Buildings) | Used in the map | free Community token in `VITE_CESIUM_ION_TOKEN`; **VERIFY** free-tier terms and limits |
| OSRM public demo server (road routes) | Used in the map | none; **VERIFY** it is demo use only, and plan a self-hosted or fallback route service for the real product |
| Esri and OpenStreetMap tile servers | Used in the map | none |
| Overpass, HDX CKAN, WorldPop REST, UCDP API | Planned | UCDP needs a free access token |
| GIBS WMTS | Planned | none |

Key names are in `.env.example` and `docs/progress/KEYS.md` (names and expiry dates, never values).

## 4. Software

| Part | Tools | Status |
|---|---|---|
| Frontend | React 19, Vite 7, React Router 7, TypeScript, Vitest | Used |
| 3D / 2D map | **CesiumJS 1.121.0** (free, open source; engine 11.0.0, widgets 8.0.0). MapLibre was replaced by Cesium on 15 November. Fire, smoke and embers use Cesium's own particle system. three.js is **not used** | Used |
| Radar and night-light ML | Python, `asf_search`, `earthaccess`, H3 grid, pandas, scikit-learn (Isolation Forest), rasterio, geopandas | Used |
| Backend | Python API, PostGIS, scheduled worker, role-based sign-in | Built by Udula, backend PR not opened yet |
| Compute | Google Colab (Colab CLI from WSL2 Ubuntu) | Used |
| Quality | GitHub Actions CI, ruff, pytest, planning checker, secrets scan | Used |
| Hosting | Static host for the frontend; Ubuntu with Docker Compose for API, PostGIS and worker (no paid service) | Planned |

### AI tools used (state this in the submission)

Claude (Claude Design for the UI prototype and mockups, Claude Code for development help and review) was used to help plan, write and check code and documents. People made the decisions and wrote the commits under their own names. The model's outputs are described as candidates, not confirmed damage.

## 5. To do before the submission

1. Read and record the terms and the citation text marked **VERIFY** above. Black Marble and FIRMS also need exact citation text from the DAAC pages.
2. Confirm the Cesium ion free-tier terms cover the competition demo, and keep the token out of Git.
3. Replace the OSRM demo server and the heavy use of public tile servers if the product goes beyond the demo.
4. Keep one record per dataset (`DATASETS.md` section 7), including the Resources-tab link it came from.
