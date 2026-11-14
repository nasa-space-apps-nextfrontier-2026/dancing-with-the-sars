# Tasks for Kisara and Chames (small backend and data tasks)

[Blueprint index](README.md) · [Team assignment and branches](17_TEAM_ASSIGNMENT_AND_BRANCHES.md)

Decided 14 November 2026. Kisara and Chames join the project and take **small, independent backend and data tasks** from Rashiru's list. Udula and Thanoban keep the ML. Rashiru keeps sign-in and safety, routes, shelters, alert logic, the frontend, and merging all PRs.

**Rules for every task here**
- **Each task stands alone.** It names its input, its output file and its test. It never waits for another task. If it needs sample data, the task says where to get it or uses the synthetic fixtures in `docs/contracts/`.
- **One task, one branch, one PR.** Branch `feature/<task-id>-<short-name>` created from `dev`. PR into `dev` using the PR template in doc 17. Do not push to `main` or `dev`. No force push.
- **Small output only.** Files in Git must stay under 5 MB. Bigger files go to `data/local/` (ignored by Git) and a short manifest in `data/manifests/` says how to rebuild them.
- **Never write secrets** into code or Git. Keys go in `.env` (not committed). A key name is listed in `.env.example`.
- **Safety wording** (the same in every task): never write "safe"; unknown stays `Unknown`; population is a range; facility status is `Unknown` unless a source says otherwise; no live vehicle or phone data.
- **Done means:** the code runs from a clean checkout, the test passes, the manifest or README line is written, the PR description is filled in, and a reviewer approved.
- Everything is **demo area only**: south Lebanon, 35.0 to 36.0 E, 33.0 to 33.6 N (`docs/DATA_AND_API_PLAN.md`). Put these numbers in one place, `worker/loaders/config.py`, and import them everywhere.
- Ask in the team chat if blocked for more than 30 minutes. Do not guess a data rule.

## Kisara: data loaders (Python, no web code)

Folder: `worker/loaders/` (new). Tests: `worker/tests/loaders/`. Python 3.12, `pip install -r backend/requirements-dev.txt`, and add any new package to `backend/requirements.txt` with a pinned version. Reviewer for all Kisara tasks: **Thanoban**.

### K-01: Lebanon boundaries (about 2 h)
| Item | Detail |
|---|---|
| Goal | Districts and governorates for south Lebanon as one small file the rest of the system can use. |
| Input | OCHA / CEDARE administrative boundaries for Lebanon on HDX (search "Lebanon administrative boundaries cod-ab" on https://data.humdata.org). Download the GeoJSON or shapefile by hand or with the HDX API. Do not commit the raw download. |
| Steps | 1. Create `worker/loaders/config.py` with the demo box constants and the HDX dataset names. 2. Write `worker/loaders/boundaries.py` with `load_boundaries() -> GeoDataFrame` that reads the download, keeps admin level 1 and 2 (governorate, district), clips to the demo box, and keeps fields `admin_id`, `name_en`, `name_ar`, `level`, `parent_id`, `geometry`. 3. Write the result to `data/local/boundaries.geojson` (simplify geometry to under 1 MB). 4. Write `data/manifests/boundaries.json` with source URL, download date, licence text and row count. |
| Output | `data/local/boundaries.geojson` and `data/manifests/boundaries.json` |
| Test | `worker/tests/loaders/test_boundaries.py` on a tiny made-up GeoJSON in the test folder: clipping works, every district has a parent, no empty geometry. |
| Done when | Running `python -m worker.loaders.boundaries` writes both files; the test passes; the manifest holds the licence. |
| Branch | `feature/k-01-boundaries` |

### K-02: The H3 grid (about 2 h)
| Item | Detail |
|---|---|
| Goal | One row per H3 resolution-9 cell in the demo box, with its district. Everyone joins their data to this grid. |
| Input | The boundaries file from K-01 (if it is not merged yet, use a small fake polygon in the test and run the real file later). |
| Steps | 1. Add `h3` to requirements (pinned). 2. Write `worker/loaders/grid.py` with `build_grid() -> DataFrame`: all res-9 cells whose centre is inside the demo box, columns `cell_id` (H3 string), `parent_r8`, `lat`, `lon`, `district_id`, `governorate_id` (join by cell centre point inside a polygon). Cells outside every district get `district_id = None`, not a guess. 3. Save `data/local/grid_r9.csv.gz` and a manifest `data/manifests/grid.json` (cell count, resolution, box, h3 library version, date). |
| Output | `data/local/grid_r9.csv.gz` and `data/manifests/grid.json` |
| Test | `worker/tests/loaders/test_grid.py`: cell ids are valid H3 (`h3.is_valid_cell`), no duplicates, every `parent_r8` equals `h3.cell_to_parent(cell, 8)`, count is stable for a small test box. |
| Done when | The test passes; the real run writes the file; the manifest states the cell count. |
| Branch | `feature/k-02-h3-grid` |

### K-03: Facilities from OpenStreetMap (about 3 h)
| Item | Detail |
|---|---|
| Goal | A table of health, school, water and power sites in the demo box, each with type, source and an Unknown status. |
| Input | HOT OSM Lebanon export on HDX (`hotosm_lbn_*`) or the Overpass API (https://overpass-api.de). Tag filters: `amenity=hospital`, `amenity=clinic`, `healthcare=*`, `amenity=school`, `man_made=water_tower`, `man_made=water_well`, `power=substation`, `power=plant`. |
| Steps | 1. `worker/loaders/facilities.py` with `load_facilities() -> DataFrame`. 2. Columns: `facility_id` (`osm:<type><id>`), `type` (`hospital`, `clinic`, `school`, `water`, `power`), `name`, `lat`, `lon`, `cell_id` (H3 res 9, use `h3.latlng_to_cell`), `source` (`OpenStreetMap contributors`), `osm_timestamp`, `status` (always `Unknown`), `status_source` (`null`). 3. **Leave out** anything military, police, prisons and government security sites (do not load tags `military=*`, `amenity=police`, `amenity=prison`). Write the excluded tag list in the file's header comment. 4. Write `data/local/facilities.csv` and `data/manifests/facilities.json` (query, date, count per type, licence ODbL and the credit line). |
| Output | `data/local/facilities.csv` and manifest |
| Test | `worker/tests/loaders/test_facilities.py` on a small saved Overpass response in the test folder: types map correctly, status is always `Unknown`, excluded tags never appear. |
| Done when | The test passes; the manifest lists counts per type; the ODbL credit is in the manifest. |
| Branch | `feature/k-03-facilities` |

### K-04: Population per cell, as a range (about 3 h)
| Item | Detail |
|---|---|
| Goal | For every grid cell, a low and a high population estimate. Never one exact number. |
| Input | WorldPop Lebanon 100 m raster for 2020, both products: the **constrained** and the **unconstrained** (https://www.worldpop.org/). Do not commit the rasters. |
| Steps | 1. `worker/loaders/population.py` with `load_population() -> DataFrame`. 2. Sum each raster inside each H3 res-9 cell (use `rasterio` and the cell boundaries from `h3.cell_to_boundary`). 3. `pop_low = min(constrained, unconstrained)`, `pop_high = max(constrained, unconstrained)`, and `pop_year = 2020`. Round to whole people. 4. Write `data/local/population.csv.gz` (columns `cell_id`, `pop_low`, `pop_high`, `pop_year`) and `data/manifests/population.json` (product names, versions, licence CC BY 4.0, total low and total high for the box). |
| Output | `data/local/population.csv.gz` and manifest |
| Test | `worker/tests/loaders/test_population.py` on a tiny synthetic raster: low is not above high, a cell fully outside the raster returns `null` not 0, the total of the cells matches the raster total within 1%. |
| Done when | The test passes; manifest totals are in the PR description; both WorldPop products are credited. |
| Branch | `feature/k-04-population` |

### K-05: Source register (about 2 h)
| Item | Detail |
|---|---|
| Goal | One JSON file that lists every dataset the app uses, in the format of `docs/contracts/SourceRecord.json`. The Sources screen and the `/sources` endpoint read it. |
| Input | `docs/DATASETS.md` (the 15 datasets), `docs/contracts/SourceRecord.json` (the format). Use **UCDP** (Uppsala Conflict Data Program, CC BY 4.0, cite the Journal of Peace Research paper on its downloads page) for strike events. ACLED is **not** used for any model or test; list it only as "context, pending terms". |
| Steps | 1. Write `data/manifests/sources.json`: a list with one record per dataset, with `source_id`, `dataset_id`, `name`, `provider`, `source_url`, `licence`, `api`, `update_frequency`, `limits`, and `live_tested` (`false` unless someone tested it). Copy facts from the docs; write `"VERIFY"` where the docs say to verify. Never invent a licence. 2. Add `worker/loaders/sources.py` with `load_sources()` that reads the file and checks each record against the fields in `SourceRecord.json`. |
| Output | `data/manifests/sources.json` |
| Test | `worker/tests/loaders/test_sources.py`: the file loads, every record has all required fields, `source_id` values are unique, there are 15 records. |
| Done when | The test passes; each record's `source_url` opens in a browser (check by hand and say so in the PR). |
| Branch | `feature/k-05-source-register` |

**Kisara total: about 12 h.** The tasks can be done in any order, and each can start now.

## Chames: read-only API endpoints (Python, FastAPI)

Folder: `backend/app/handlers/` (new). Tests: `backend/tests/handlers/`. Reviewer for all Chames tasks: **Rashiru**. The API is already registered from `docs/contracts/openapi.yaml`; each path returns HTTP 501 until a handler exists. Sign-in, roles and access checks already run before a handler (do not change them: that is Rashiru's `backend/app/core/` and `backend/app/api/v1.py` access logic). Each handler returns **fixture data** from `docs/contracts/*.json` with `"synthetic": true` until real files exist. Run: `python -m pytest backend/tests`.

### C-01: Handler registry (about 2 h) — do this first
| Item | Detail |
|---|---|
| Goal | One place where endpoint handlers are registered, so later tasks add a handler without editing shared code. |
| Steps | 1. Create `backend/app/handlers/__init__.py` with `HANDLERS: dict[tuple[str, str], Callable] = {}` and a decorator `@handler('GET', '/areas')` that adds a function to it. Handler signature: `def fn(request, path_params) -> dict` returning JSON-able data. 2. In `backend/app/api/v1.py`, **right after the access check** (`denial = authorize(...)`) and before the 501 return, look up `(method, path)` in `HANDLERS` and return its result. This is the only change to `v1.py`, and Rashiru must approve it. 3. Create `backend/app/handlers/fixtures.py` with `load_fixture(name)` that reads `docs/contracts/<name>.json`. |
| Test | `backend/tests/handlers/test_registry.py`: a registered test handler is called; a path with no handler still returns 501; a logged-out user still gets 401 for a private path (the registry never skips the access check). |
| Done when | The three tests pass and the existing `backend/tests/test_api.py` still passes unchanged. |
| Branch | `feature/c-01-handler-registry` |

### C-02: `/status` and `/sources` (about 2 h)
| Item | Detail |
|---|---|
| Goal | The Sources and data-age screens get real content. |
| Endpoints | `GET /status`, `GET /sources` (with `cursor` and `limit`), `GET /sources/{source_id}` |
| Steps | 1. Handlers in `backend/app/handlers/sources.py`. Read `data/manifests/sources.json` if it exists (Kisara's K-05); otherwise return `docs/contracts/SourceRecord.json` as a one-item list. 2. `/status`: `synthetic`, a list of `{source_id, last_success, age_hours}` (use `null` when unknown), no secrets, no internal paths or hostnames. 3. Follow the response shapes in `docs/contracts/openapi.yaml`. |
| Test | `test_sources.py`: pagination works, unknown `source_id` returns 404 with the `Error` shape, nothing in the response contains `http://localhost`, a file path or an API key name. |
| Done when | Tests pass; the three routes no longer return 501 in the running app. |
| Branch | `feature/c-02-status-sources` |

### C-03: Areas, summary and values (about 3 h)
| Item | Detail |
|---|---|
| Endpoints | `GET /areas`, `GET /areas/{area_id}/summary`, `GET /areas/{area_id}/values` |
| Steps | 1. `backend/app/handlers/areas.py`. `/areas` lists areas from `data/local/grid_r9.csv.gz` grouped by district (Kisara's K-02) when the file exists; otherwise one fixture area `demo-area-01`. 2. `/summary` returns `docs/contracts/AreaSummary.json` for the requested area. 3. `/values` returns a list of `MetricValue` items (see `MetricValue.json`), filtered by the `metric` query parameter. 4. Every number carries a range or `Unknown`, a label (Observed, Reported, Corroborated or Unknown), a source and a date. A missing value is `null` with label `Unknown`, never 0. |
| Test | `test_areas.py`: unknown area returns 404; the `metric` filter works; no value has a label outside the four allowed; no value is a bare number without a range or `null`. |
| Done when | Tests pass; routes return fixture data instead of 501. |
| Branch | `feature/c-03-areas-summary-values` |

### C-04: People, services and facilities (about 3 h)
| Item | Detail |
|---|---|
| Endpoints | `GET /areas/{area_id}/people`, `GET /areas/{area_id}/services`, `GET /areas/{area_id}/facilities` (with `type` and `cursor`) |
| Steps | 1. `backend/app/handlers/people_facilities.py`. 2. `/facilities` reads `data/local/facilities.csv` (Kisara's K-03) if present, else returns two fixture rows marked synthetic. Facility `status` is always `Unknown` in the API unless a field says otherwise. 3. `/people` reads `data/local/population.csv.gz` (K-04) if present and returns `pop_low` and `pop_high` summed for the area; otherwise a fixture range. Never return one exact population number. 4. `/services` returns an empty list with `"message": "No service-loss data yet"` until the night-light model output exists (do not fake it). |
| Test | `test_people_facilities.py`: type filter works, pagination works, people always has low and high with low not above high, sensitive facilities never listed (tags from K-03 excluded list). |
| Done when | Tests pass; the three routes return data instead of 501. |
| Branch | `feature/c-04-people-facilities` |

### C-05: Alerts (read-only) (about 2 h)
| Item | Detail |
|---|---|
| Endpoints | `GET /alerts` (filters `area_id`, `type`, `since`, `cursor`, `limit`), `GET /alerts/{alert_id}` |
| Steps | 1. `backend/app/handlers/alerts.py`. Return `docs/contracts/AlertDetail.json` as the single fixture alert, plus a fire alert and a possible-power-loss alert made by copying that fixture and changing `type`. 2. Wording on every alert: "Fire detected" or "Possible power loss". Never state a cause. Each alert carries source, date, confidence and the evidence label. 3. Do **not** write `POST /alerts/{id}/reviews` (Rashiru's, it needs sign-in logic). |
| Test | `test_alerts.py`: filters work; `since` rejects a bad date with the `Error` shape; no alert text contains the words "safe", "caused by" or "blackout". |
| Done when | Tests pass; both routes return data instead of 501. |
| Branch | `feature/c-05-alerts-read` |

### C-06: Run guide and contract tests (about 2 h)
| Item | Detail |
|---|---|
| Goal | A new teammate runs the whole app from the README alone, and a test proves each handler matches the contract. |
| Steps | 1. On a clean clone, follow `README.md` and `.env.example` line by line. Write every missing or wrong step into a PR that fixes the README (do not change code in this PR). 2. Add `backend/tests/handlers/test_contract_shapes.py` that calls each implemented endpoint and validates the response against the matching JSON schema in `docs/contracts/` using `jsonschema` (add to `requirements-dev.txt`, pinned). Skip endpoints that still return 501. |
| Done when | The README has no step that fails on a clean machine (say which OS you used); the shape test passes. |
| Branch | `feature/c-06-run-guide-contract-tests` |

**Chames total: about 14 h.** C-01 first; C-02 to C-05 start after C-01 is merged (they use its registry; until then write the function and test it by calling it directly). C-06 can start any time.

## Order, reviews and PRs

| Task | Person | Reviewer | Needs | Branch |
|---|---|---|---|---|
| K-01 boundaries | Kisara | Thanoban | nothing | `feature/k-01-boundaries` |
| K-02 grid | Kisara | Thanoban | K-01 only for the real run | `feature/k-02-h3-grid` |
| K-03 facilities | Kisara | Thanoban | nothing | `feature/k-03-facilities` |
| K-04 population | Kisara | Thanoban | K-02 only for the real run | `feature/k-04-population` |
| K-05 source register | Kisara | Thanoban | nothing | `feature/k-05-source-register` |
| C-01 handler registry | Chames | Rashiru | nothing | `feature/c-01-handler-registry` |
| C-02 status, sources | Chames | Rashiru | C-01 | `feature/c-02-status-sources` |
| C-03 areas, summary, values | Chames | Rashiru | C-01 | `feature/c-03-areas-summary-values` |
| C-04 people, facilities | Chames | Rashiru | C-01 | `feature/c-04-people-facilities` |
| C-05 alerts read | Chames | Rashiru | C-01 | `feature/c-05-alerts-read` |
| C-06 run guide, contract tests | Chames | Rashiru | nothing | `feature/c-06-run-guide-contract-tests` |

Real files from Kisara's tasks (`data/local/…`) are read by Chames's handlers when present; otherwise fixtures are used, so neither person waits for the other.

### Step by step for each task (same for everyone)
1. `git switch dev && git pull`.
2. `git switch -c feature/<task-id>-<short-name>`.
3. Write the code and the test. Run `python -m pytest` and `python -I docs/contracts/validate_planning.py` (must show `"errors": []`).
4. Commit with your own name and one task ID in the message, for example `K-03: load OSM facilities`. No AI co-author line.
5. `git push -u origin feature/<task-id>-<short-name>` and open a PR into `dev` using the PR template.
6. Fix review comments with new commits (no force push). Rashiru merges (squash) after one approval.
7. Delete the branch after merge, then `git switch dev && git pull`.

### What is not in these tasks
Sign-in, roles, access checks, closures, routes, shelters, briefs, admin endpoints, alert reviews, the worker timer, the frontend and every ML model. Ask Rashiru before touching `backend/app/core/`, `backend/app/api/v1.py` (except the one change in C-01), `docs/contracts/` or `frontend/`.
