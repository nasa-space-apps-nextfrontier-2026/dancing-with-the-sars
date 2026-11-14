# Backend: running with real NISAR data

Owner: Udula (backend handover from Rashiru, 14 Nov 2026). With `DEMO_SYNTHETIC=true` (the default) nothing below changes: the API keeps serving Rashiru's synthetic fixtures. With `DEMO_SYNTHETIC=false` the radar routes serve the real M1 results.

## 1. Database (PostGIS in Docker)

```powershell
docker compose up -d db                      # or: $env:CIVISAR_DB_PORT=5433 if PostgreSQL already uses 5432
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
```

Migrations: `0001_initial_postgis` (Rashiru), `0002_metric_value_records` (contract value id, release time and full record), `0003_alerts_and_source_status` (worker alerts and per-source fetch status) and `0004_briefs` (stored briefs). Every upgrade and downgrade were tested on `postgis/postgis:16-3.4`.

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
| `GET /values/{value_id}/trace` | analyst+ | The value, its source records and the model tests of its run |
| `GET /areas/{area_id}/summary` | analyst+ | AreaSummary: people ranges, services, hazards, evidence. **503 until the population file is loaded** (see 4a). |
| `POST /briefs` | analyst+, CSRF | Body `{area_id, as_of}`. Freezes the summary into a brief (expires after 8 hours). |
| `GET /briefs/{report_id}` | signed in | The brief, re-checked on every read: area scope, expiry, role sections |
| `GET /briefs/{report_id}/print` | signed in | Plain printable HTML with a RESTRICTED banner and source footnotes; loads nothing from outside |

## 4a. Area summary and briefs

- **People** come only from `DATA_ROOT/local/population.csv.gz` (Kisara, K-04): columns `cell_id` (H3 r9), `pop_low`, `pop_high`, `pop_year`. The contract needs whole-number ranges, so without this file the summary and briefs answer 503 instead of inventing numbers. **Team note:** the contract has no way to say "people Unknown"; raise at H2 if the file will be late.
- Residents = all cells in the neighbourhood; potentially affected = cells with a radar candidate; potentially displaced uses the UNOSAT housing shares (destroyed/severe 100%, moderate 50%, possible 20%). Derived values take the weakest label of their inputs. All are pre-displacement estimates, not people there now.
- Services: power from released "Possible power loss" alerts; water, health and comms stay Unknown. No severity rank until facilities, services and roads are loaded. Route options and shelter candidates are empty and listed as omitted.
- Briefs never include records still on the 72-hour hold. Route and shelter sections are removed again at read time for roles below officer / coordinator. Out-of-scope or expired briefs answer 404.
- The WorldPop source record is not in `sources.json` yet, so brief footnotes list only the radar sources.

## 5. Safety rules in the server

- **Area scope** (`backend/app/policy/scope.py`): `south-lebanon-demo` covers every H3 cell whose centre is in the demo box; an H3 cell covers its finer children; fixture ids match exactly. Areas outside the scope get 403.
- **72-hour hold** (`backend/app/policy/release.py`): records whose `release_at` has not passed are hidden from every role. Admin is not a bypass for the hold or for area scope (doc 07).
- **Files**: tiles are read only from `DATA_ROOT/private/nisar/change/`; any other path in a manifest is refused.
- Logged-out users never get radar layers, tiles, damage or series.

Tests: `tests/security/` (scope, hold, roles, tiles, file allow-list, summary and briefs) and `backend/tests/test_load_radar_results.py`.
