# Backend: running with real NISAR data

Owner: Udula (backend handover from Rashiru, 14 Nov 2026). With `DEMO_SYNTHETIC=true` (the default) nothing below changes: the API keeps serving Rashiru's synthetic fixtures. With `DEMO_SYNTHETIC=false` the radar routes serve the real M1 results.

## 1. Database (PostGIS in Docker)

```powershell
docker compose up -d db                      # or: $env:CIVISAR_DB_PORT=5433 if PostgreSQL already uses 5432
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
```

Migrations: `0001_initial_postgis` (Rashiru) and `0002_metric_value_records` (contract value id, release time and full record). Both upgrade and downgrade were tested on `postgis/postgis:16-3.4`.

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
CIVISAR_DEMO_USERS_JSON=...   # from python -m scripts.create_demo_user; give demo users the scope south-lebanon-demo
```

## 4. Real-data routes

| Route | Role | Returns |
|---|---|---|
| `GET /layers` | public (filtered) | Layer records the user's role may see and whose `release_at` has passed. Logged out: empty list. |
| `GET /layers/{layer_id}` | analyst+ | One Layer, or 404 |
| `GET /layers/{layer_id}/tiles/{z}/{x}/{y}` | analyst+ | 256 px PNG (EPSG:3857). Change layers: red = drop, blue = rise (±6 dB); mean layers: grey. 404 outside the layer, 422 for bad coordinates. |
| `GET /layers/{layer_id}/timeseries?area_id=<H3 r8>&from&to` | analyst+ | Per-pass candidate counts for the area (MetricValue fields), plus missing passes |
| `GET /areas/{area_id}/damage?pass_id=A\|YYYY-MM-DD` | analyst+ | r9 results inside the area for the before/after run (`A`) or one later pass |

## 5. Safety rules in the server

- **Area scope** (`backend/app/policy/scope.py`): `south-lebanon-demo` covers every H3 cell whose centre is in the demo box; an H3 cell covers its finer children; fixture ids match exactly. Areas outside the scope get 403.
- **72-hour hold** (`backend/app/policy/release.py`): records whose `release_at` has not passed are hidden from everyone except admin (for review).
- **Files**: tiles are read only from `DATA_ROOT/private/nisar/change/`; any other path in a manifest is refused.
- Logged-out users never get radar layers, tiles, damage or series.

Tests: `tests/security/` (scope, hold, roles, tiles, file allow-list) and `backend/tests/test_load_radar_results.py`.
