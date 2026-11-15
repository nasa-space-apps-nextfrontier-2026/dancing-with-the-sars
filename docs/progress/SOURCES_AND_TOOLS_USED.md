# Sources, APIs and tools used

What CIVISAR uses, for the submission and the citations (15 November 2026). Details per dataset (concept IDs, versions, limits) are in [DATASETS.md](../DATASETS.md) and [DATASET_RECORDS_THANOBAN.md](DATASET_RECORDS_THANOBAN.md). Items marked **VERIFY** need their terms or citation text read before the submission.

## 1. From the challenge Resources tab

Tab: [Dancing with the SARs, Resources tab](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=resources)

| Resource on the tab | How CIVISAR uses it |
|---|---|
| NASA Earthdata Search | CMR search for the NASA datasets below; Earthdata Login token for downloads |
| ASF Data Search Vertex | NISAR and OPERA RTC-S1 scenes, found with the ASF Search API (336 NISAR granules over south Lebanon) |
| NISAR Data User Guide | Product definitions, processing versions and limits for the radar model |

NASA data found and downloaded through these tools:

| Dataset | Use |
|---|---|
| NISAR L2 GCOV (track 151 descending, frame 72) | Radar change and the damage-candidate model |
| OPERA RTC-S1 (Sentinel-1) | Second-sensor check on the radar candidates |
| Black Marble VJ146A2 / VJ246A2 (and near real time) | Night-light history and "possible power loss" alerts |
| FIRMS VIIRS 375 m active fire | Live fire points (public CSV feed, no map key) |

## 2. Other data

| Data | Use | Terms |
|---|---|---|
| OpenStreetMap buildings, roads and facilities | Building footprints (268,536 in the demo box), types, facilities, roads | ODbL; credit "© OpenStreetMap contributors" |
| GHSL building height (GHS-OBAT, EU JRC) | Building height and floors as a range | CC BY 4.0 |
| Esri World Imagery and "Streets & labels" tiles | Satellite ground imagery and labels in the map | **VERIFY** |
| OpenStreetMap raster tiles | Streets base map | **VERIFY** tile usage policy |
| WorldPop 2020 Lebanon (constrained and unconstrained) | People ranges per H3 r9 cell | CC BY 4.0 |
| OCHA COD-AB Lebanon boundaries (HDX) | Area names and the Lebanon boundary for facilities | CC BY-IGO |
| World Bank damage and needs assessment (Syria, Aug 2025) | Anchor for the rebuild cost per m2 | Public report; cite it |

## 3. APIs and services

| Service | Use | Key or login |
|---|---|---|
| ASF Search API | Find NISAR and OPERA scenes | none to search |
| NASA CMR search | Find NASA datasets by concept ID | none to search |
| Earthdata Login, LAADS DAAC, LANCE | Download NASA files, including near-real-time Black Marble | free account token; the "LANCE" Earthdata application authorised |
| FIRMS public CSV feed | Live fire points | none |
| Cesium ion (World Terrain, OSM Buildings) | 3D terrain and buildings in the map | free Community token in `VITE_CESIUM_ION_TOKEN`; **VERIFY** free-tier terms |
| Supabase (hosted PostgreSQL with PostGIS) | Database for all real data served to the dashboard | project account; `DATABASE_URL` only in `.env` and the host's secrets; Supabase's public Data API roles revoked |
| Overpass API (OpenStreetMap) | Download of OSM facilities (health, schools, water, power) | none |
| OSRM public demo server | Road routes in the map | none; **VERIFY** demo-use terms |

Key names are in `.env.example` and `docs/progress/KEYS.md` (names and expiry dates, never values).

## 4. Software

| Part | Tools |
|---|---|
| Frontend | React 19, Vite 7, React Router 7, TypeScript, Vitest |
| 3D and 2D map | CesiumJS 1.121.0 (free, open source), including its particle system for fire and smoke |
| Radar and night-light ML | Python, `asf_search`, H3 grid cells, Isolation Forest anomaly model |
| Backend | Python API, PostGIS, scheduled worker, role-based sign-in |
| Compute | Google Colab (Colab CLI from WSL2 Ubuntu) |
| Quality | GitHub Actions CI, ruff, pytest, planning checker, secrets scan |

### AI tools used (state this in the submission)

Claude (Claude Design for the UI prototype and mockups, Claude Code for development help and review) was used to help plan, write and check code and documents. People made the decisions and wrote the commits under their own names.

## 5. Before the submission

1. Read and record the terms marked **VERIFY**. Black Marble and FIRMS also need exact citation text from the DAAC pages.
2. Keep one record per dataset (`DATASETS.md` section 7), including the Resources-tab link it came from.
