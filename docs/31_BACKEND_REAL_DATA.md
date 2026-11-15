# Backend: running with real NISAR data

Owner: Udula (backend handover from Rashiru, 14 Nov 2026). With `DEMO_SYNTHETIC=true` (the default) nothing below changes: the API keeps serving Rashiru's synthetic fixtures. With `DEMO_SYNTHETIC=false` the radar routes serve the real M1 results.

## 0. One command

```powershell
$env:CIVISAR_DB_PORT=5433   # only if PostgreSQL already uses 5432
.\.venv\Scripts\python.exe -m scripts.demo_setup              # --no-docker, --offline, --dry-run
```

Runs sections 1 to 4c in order: PostGIS, migrations, radar results, building table, publish (damage and live fires), agents, agent outputs, facilities, one worker run. A step whose private input files are not on the machine is skipped with the reason; loads are replaceable, so it can be run again. Checked on 15 Nov 2026: all eight steps done, building table identical on re-run. It then prints how to make a sign-in user and start the API and the frontend.

## 1. Database (PostGIS in Docker)

```powershell
docker compose up -d db                      # or: $env:CIVISAR_DB_PORT=5433 if PostgreSQL already uses 5432
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
```

Migrations: `0001_initial_postgis` (Rashiru), `0002_metric_value_records` (contract value id, release time and full record), `0003_alerts_and_source_status` (worker alerts and per-source fetch status), `0004_briefs` (stored briefs), `0005_audit_reviews_access_jobs` (audit log, alert reviews, admin role changes, manual job runs), `0006_agent_outputs` (restricted incident ranking, recommendation, insight, budget and building-context outputs loaded by `scripts/load_agent_outputs.py`) and `0007_facilities` (K-03 facilities inside Lebanon, loaded by `scripts/load_facilities.py`). Upgrade, downgrade and upgrade of every revision through `0007` were checked on `postgis/postgis:16-3.4` on 15 Nov 2026.

## 2. Load the radar results

Needs the private M1 files (`data/private/nisar/...`, from the backend zip) and the contract rows (`data/local/radar_contract/`, from the contract-rows zip), plus the radar packages (`pipelines/radar/nisar/requirements.txt`):

```powershell
.\.venv\Scripts\python.exe -m scripts.load_radar_results --replace
```

One transaction; re-running replaces the same runs; a failure leaves the database unchanged. Result on 14 Nov 2026: 13,669 areas, 9 runs, 52,786 cell results, 41,508 metric values.

Schema notes: `radar_area_results.classification` allows only `Unknown`, `candidate_change`, `other_change`. The M1 level (destroyed/severe, moderate, possible) is kept as the reason code `level:<class>`. Cells with no detected change are not stored: a missing row means "nothing detected", never "no damage".

## 3. Run the API in real-data mode

`.env` (never committed):

```
DEMO_SYNTHETIC=false
DATABASE_URL=postgresql+psycopg://civisar:civisar_local_only@localhost:5433/civisar
DATA_ROOT=data
CIVISAR_DEMO_USERS_JSON=...   # from python -m scripts.create_demo_user (default scopes: demo-area-01,south-lebanon-demo)
```

## 3a. Worker (alerts)

```powershell
.\.venv\Scripts\python.exe -m worker.scheduler --once   # one run of every job
.\.venv\Scripts\python.exe -m worker.scheduler          # forever: fires every 30 min, night lights daily
```

- **Fires**: Thanoban's `worker.services.firms_feed.current_events()` (public FIRMS feed, no key) -> "Fire detected" alerts. First real run (14 Nov 2026): 2 detections in the demo box over 7 days, latest 12 Nov.
- **Possible power loss**: Thanoban's `power_loss_events()` on the per-cell night-light history set in `NIGHTLIGHT_HISTORY`; reports "unavailable" when the file is not on the machine.
- Alerts keep only the H3 r8 neighbourhood (no coordinates). Same event -> same alert id. A failed fetch keeps the last good alerts and records the failure (shown as Cached).
- **Clean-up** (daily): deletes audit rows older than 30 days and briefs past their expiry (doc 07 retention).
- `FIRE_RELEASE_DELAY_HOURS` (default 0): fire alerts go to signed-in roles at once; the team can set a delay.

## 4. Real-data routes

| Route | Role | Returns |
|---|---|---|
| `GET /layers` | public (filtered) | Layer records the user's role may see and whose `release_at` has passed. Logged out: empty list. |
| `GET /layers/{layer_id}` | analyst+ | One Layer, or 404 |
| `GET /layers/{layer_id}/tiles/{z}/{x}/{y}` | analyst+ | 256 px PNG (EPSG:3857). Change layers: red = drop, blue = rise (±6 dB); mean layers: grey. 404 outside the layer, 422 for bad coordinates. |
| `GET /layers/{layer_id}/timeseries?area_id=<H3 r8>&from&to` | analyst+ | Per-pass candidate counts for the area (MetricValue fields), plus missing passes |
| `GET /areas/{area_id}/damage?pass_id=A\|YYYY-MM-DD` | analyst+ | r9 results inside the area for the before/after run (`A`) or one later pass |
| `GET /alerts?area_id&type&since&cursor&limit` | analyst+ | Alerts in the user's scopes whose release time has passed (AlertDetail). `rings`, `facilities` and `services` stay empty until population and facility data are loaded. |
| `GET /alerts/{alert_id}` | analyst+ | One alert, or 404 (also when outside the user's scope) |
| `GET /status` | public | Last success, freshness and Cached flag per source (FIRMS, NISAR). Never shows error text. |
| `GET /public/map?bbox` | public | Always suppressed in this release and never queries PostGIS. Future publication requires immutable artifact-bound approval, licence/QA review, high-risk-cell and spatial-cohort controls, and snapshot-differencing analysis. H3 r8 and a minimum count are not sufficient protection. |
| `GET /values/{value_id}/trace` | analyst+ | The value, its source records and the model tests of its run |
| `GET /areas?bbox&cursor&limit` | analyst+ | H3 r8 neighbourhoods in the user's scope (bbox = minLon,minLat,maxLon,maxLat) |
| `GET /areas/{area_id}/values?metric&as_of` | analyst+ | Released MetricValue records for the area. Optional `as_of` is an ISO date or datetime; records observed or released after that historical cutoff are excluded. |
| `GET /areas/{area_id}/people?as_of` | analyst+ | The three people ranges at the optional ISO date/datetime cutoff; observations or releases after `as_of` are excluded. 503 until population and eligible released radar evidence are available. |
| `GET /areas/{area_id}/services?as_of` | analyst+ | Power from released power-loss alerts at the optional ISO date/datetime cutoff; alerts detected or released later are excluded. Water, health and comms remain Unknown. |
| `GET /areas/{area_id}/validation` | analyst+ | Empty list with `availability: unavailable...`: no independent damage assessment exists yet |
| `GET /areas/{area_id}/facilities?type&cursor&limit` | analyst+ | Facilities in the area (`<H3 r8>`, `<H3 r9>` or `south-lebanon-demo`) and the user's scope (section 4c). Analysts: type, operating status and damage status, no location; officer and above also get the point. 503 until loaded (never an empty "no facilities") |
| `GET /sources`, `GET /sources/{id}` | public | Source records from the radar contract export, then the source register `data/manifests/sources.json` (Black Marble, FIRMS, WorldPop, GHS-OBAT, OSM facilities, HDX boundaries; checked against `SourceRecord` by `worker/loaders/sources.py`). Records marked synthetic are never served. 503 when the radar export is not loaded |
| `POST /alerts/{alert_id}/reviews` | analyst+, CSRF | Body `{status, note}`, status `reviewed` / `needs_follow_up` / `not_relevant`. Only on alerts the reviewer may see. |
| `GET /admin/audit?from&to&cursor` | admin | Last 30 days: actor, action, coarse resource type, outcome, time |
| `PATCH /admin/users/{user_id}/roles` | admin, CSRF | Body `{role, area_scopes, reason}`. Ends that user's sessions; applies at their next sign-in. An admin cannot remove their own admin role (409). |
| `POST /admin/jobs/{job_id}/retry` | admin, CSRF | `fires` or `night_lights`, body `{idempotency_key}`. The same key never runs twice; reused for another job -> 409. |
| `GET /areas/{area_id}/summary?as_of` | analyst+ | AreaSummary at the optional ISO date/datetime cutoff: people ranges, services, hazards and evidence. Later observations and later-released records are excluded. **503 until population and eligible released radar evidence are available** (see 4a). |
| `POST /briefs` | analyst+, CSRF | Required body `{area_id, as_of}`, where `as_of` is an ISO date or datetime and cannot be in the future. Freezes the historically filtered summary into a brief (expires after 8 hours). |
| `GET /briefs/{report_id}` | signed in | The brief, re-checked on every read: area scope, expiry, role sections |
| `GET /briefs/{report_id}/print` | signed in | Plain printable HTML with a RESTRICTED banner and source footnotes; loads nothing from outside |

## 4a. Area summary and briefs

- **People** come only from `DATA_ROOT/local/population.csv.gz` (Kisara, K-04): columns `cell_id` (H3 r9), `pop_low`, `pop_high`, `pop_year`. The contract needs whole-number ranges, so without this file the summary and briefs answer 503 instead of inventing numbers. **Team note:** the contract has no way to say "people Unknown"; raise at H2 if the file will be late.
- Residents = all cells in the neighbourhood; potentially affected = cells with a radar candidate; potentially displaced uses the UNOSAT housing shares (destroyed/severe 100%, moderate 50%, possible 20%). Derived values take the weakest label of their inputs. All are pre-displacement estimates, not people there now.
- Services: power from released "Possible power loss" alerts; water, health and comms stay Unknown. No severity rank until facilities, services and roads are loaded. Route options and shelter candidates are empty and listed as omitted.
- Historical cutoff: summary, values, people and services accept optional `as_of=<ISO date or datetime>`; without it they use current visibility. Brief creation requires the same `as_of` value in its JSON body and rejects future values. Observations, detections and records after the cutoff, including records whose `release_at` is later than the cutoff, are excluded.
- Briefs never include records still on the 72-hour hold. Route and shelter sections are removed again at read time for roles below officer / coordinator. Out-of-scope or expired briefs answer 404.
- The WorldPop source record is not in `sources.json` yet, so brief footnotes list only the radar sources.

## 4b. Agent outputs: incidents, budgets, buildings (U-06)

Migration `0006_agent_outputs` adds `agent_runs`, `agent_incidents`, `agent_recommendations`, `agent_insights`, `agent_budgets` and `agent_buildings` (GiST index on the footprint). Load them after the building table and the publish step:

```powershell
.\.venv\Scripts\python.exe -m worker.main --agents --table data/local/building_table.parquet --out data/published
.\.venv\Scripts\python.exe -m scripts.load_agent_outputs
```

One transaction; a reload replaces the previous one; a building with residents is refused.

| Route | Role | Returns |
|---|---|---|
| `GET /incidents?area_id&cursor&limit` | analyst+ | Ranked incidents the user may see (in scope, released), ranked 1..n within that view |
| `GET /incidents/{incident_id}` | analyst+ | Incident, insights (only for users scoped to the whole demo box) and the recommendation for the caller's role (admin reads the coordinator version) |
| `GET /areas/{area_id}/budget` | analyst+ | Budget ranges, "Planning indication only"; `south-lebanon-demo` gives the whole box |
| `GET /buildings?bbox&limit` | analyst+ | GeoJSON buildings for the 3D view; bbox at most 0.05 square degrees, limit 1-5000, `truncated` when cut; cell damage result; no residents |

All four answer 503 until the agent outputs are loaded, and 404 for anything held or outside the user's scope.

## 4c. Facilities (K-03)

Migration `0007_facilities` adds `facility_runs` and `facilities` (point, H3 r9 and r8; names are not stored). Load Kisara's files (from her K-01 and K-03 scripts, never from Git):

```powershell
.\.venv\Scripts\python.exe -m scripts.load_facilities --facilities data/local/facilities.csv --boundaries data/local/boundaries.geojson
```

One transaction; a reload replaces the previous one. Only clinics, hospitals, schools, water and power sites **inside the Lebanon boundary** are kept: the demo box also covers part of northern Israel, while buildings and population cover Lebanon only. Result on 15 Nov 2026: 383 loaded (11 clinics, 41 hospitals, 81 schools, 137 water, 113 power), 160 outside Lebanon dropped.

Rules (doc 07): operating status is always `Unknown` (no source says a site is open); damage status is the released radar result of the facility's H3 r9 cell, and a cell with no detected change reads "No radar change detected in this cell. Not confirmed undamaged or open."; label `Reported` (OpenStreetMap). In synthetic mode the people, facilities and areas handlers serve the sample records only and never read local data files.

## 5. Safety rules in the server

- **Sign-in**: 5 failed attempts per username and client in 15 minutes -> 429 with `Retry-After`. Roles set by an admin are read from the database at sign-in; if the database is down, sign-in fails (503) rather than falling back to an old role. `/roles` lists the role's capabilities (doc 07 matrix).
- **Audit** (`audit_events`): sign-in (failed ones as `anonymous`, never the typed name), sign-out, 403 denials, brief creation, alert reviews, role changes, job runs. Only actor, action, coarse resource type, outcome, time and request id: no coordinates, tokens, passwords or request bodies.
- **Durable privileged audit**: role changes and alert reviews write their audit event in the same database transaction as the mutation. A manual job must commit a `job_retry` start event before the worker is invoked; raised job exceptions are recorded as failed rather than left running.
- **Production process limitation**: sessions, user-session revocation and login-failure counters are process-local. Run this hackathon backend as a single API process. A multi-worker or horizontally scaled deployment requires a shared server-side session/revocation/rate-limit store while retaining the custom cookie and CSRF design.

- **Area scope** (`backend/app/policy/scope.py`): `south-lebanon-demo` covers every H3 cell whose centre is in the demo box; an H3 cell covers its finer children; fixture ids match exactly. Areas outside the scope get 403.
- **72-hour hold** (`backend/app/policy/release.py`): records whose `release_at` has not passed are hidden from every role. Admin is not a bypass for the hold or for area scope (doc 07).
- **Missing radar evidence**: no eligible artifact, or an artifact with no released area evidence at the requested `as_of`, returns unavailable rather than a false numerical zero. A zero is returned only after an eligible released observation exists.
- **Files**: tiles are read only from `DATA_ROOT/private/nisar/change/`; any other path in a manifest is refused.
- Logged-out users never get radar layers, tiles, damage or series.

Tests: `tests/security/` (scope, hold, roles, tiles, file allow-list, summary and briefs) and `backend/tests/test_load_radar_results.py`.

## 6. Hosted database (Supabase) and rebuilding the inputs

**Database (15 Nov 2026).** The real data is loaded into a Supabase project (free plan, Seoul region, PostgreSQL 17, PostGIS 3.3). Same schema as section 1; only `DATABASE_URL` changes.

- In `.env` (never committed): `DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<password>@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres`. Use the **Session pooler** string (IPv4), change the scheme to `postgresql+psycopg://`, and URL-encode special characters in the password (`#` = `%23`, `@` = `%40`).
- Supabase serves every table in `public` through its own Data API. Block it before loading anything: `REVOKE ALL ON ALL TABLES, SEQUENCES and FUNCTIONS IN SCHEMA public FROM anon, authenticated`, the same with `ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public` so new tables stay closed, and keep Row Level Security on for every table. Our API connects as `postgres` and is the only reader.
- The free plan pauses after some days without activity and has a small size cap: open the project before a demo.
- Reset the database password if it was ever shared, then update `.env` and the host's secret.

**Rebuilding the inputs from public downloads** (all outside Git, under `data/raw/` and `data/local/`):

| Input | Download |
|---|---|
| OSM buildings | HDX `hotosm_lbn_buildings`, GeoParquet, saved as `data/raw/hotosm/lbn_buildings.parquet` |
| Heights | JRC GHS-OBAT `GHS_OBAT_CSV_LBN_E2020_R2024A_V1_0.zip`, unzipped to `data/raw/ghsl/obat_lbn/` |
| Population | WorldPop 2020 Lebanon constrained and unconstrained rasters in `data/raw/worldpop/` |
| Boundaries | HDX OCHA COD-AB Lebanon GeoJSON zip, unzipped to `data/raw/lbn_admin/` |
| Facilities | Overpass API (fetched by the loader) |

```bash
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")   # if Python's own CA store is out of date
python -m worker.loaders.boundaries
python -m worker.loaders.grid
python -m worker.loaders.population
python -m worker.loaders.facilities          # Overpass can answer 502 when busy: run again
python -m pipelines.buildings.base
python -m pipelines.buildings.heights
python -m pipelines.buildings.table
python -m alembic -c backend/alembic.ini upgrade head
python -m pipelines.radar.nisar.export_contract
python -m scripts.load_radar_results --replace
python -m worker.main --publish --damage data/private/nisar/model/damage_cells.parquet --history data/local/bm_history.csv.gz --fires
python -m worker.main --agents --table data/local/building_table.parquet --population data/local/population.csv.gz
python -m scripts.load_agent_outputs
python -m scripts.load_facilities
python -m worker.scheduler --once
```

Result on 15 Nov 2026: 52,786 radar cell results and 41,508 values; 268,536 buildings; 52,053 grid and population cells; 179 incidents, 537 recommendations, 6 insights, 131 budgets; 383 facilities inside Lebanon (of 543); 50 alerts (49 possible power loss, 1 fire). The public dashboard reads this data with no sign-in (decision D30, doc 12).
