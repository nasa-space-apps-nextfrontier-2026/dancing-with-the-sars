# Udula: work log (M1 radar ML, then M3 backend)

Read this to see what Udula has finished, what is waiting, and what needs a team decision. Tasks: [Member 1](../tasks/MEMBER_1_UDULA_NISAR_ML.md) (M1-01 to M1-03) and, since 14 November 2026, the backend part of [Member 3](../tasks/MEMBER_3_RASHIRU_FRONTEND_BACKEND.md) (M3-01 to M3-04; Rashiru keeps the frontend). Backend guide: [31](../31_BACKEND_REAL_DATA.md). Last updated 14 November 2026.

## 1. Radar ML (M1-01 to M1-03): done

| Item | State | PR |
|---|---|---|
| NISAR scene search, download and crop to the demo box (track 151D, frame 72; BETA before, PROVISIONAL/V1 after) | Merged | [#15](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/15) |
| Change features on H3 r9 cells, Isolation Forest anomaly model, candidate classes (possible / moderate / destroyed-or-severe) | Merged | [#15](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/15) |
| Tests: hold-out false alarms, eye check, strike context (UCDP, not ACLED), time slider passes | Merged | [#15](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/15) |
| Sentinel-1 (OPERA RTC) cross-check: candidates seen by a second, independent radar get the label Corroborated | Merged | [#16](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/16) |
| Export as contract records: 41,508 MetricValue, 38 Layer, 7 SourceRecord | Merged | [#17](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/17) |
| Share zips for the team (tables, backend files, contract rows) | Made; shared privately, never in Git (the repo is public) | |

Limits that stay visible: radar results are **candidates, not confirmed damage**. There is no independent damage assessment for Lebanon to validate against (no UNOSAT release), so validation is reported as unavailable.

## 2. Backend (M3-01 to M3-04): built, pushed, no PR yet

Branch `feature/m3-01-backend-foundation`, pushed 14 November 2026. Starts from Rashiru's backend (copied from `feature/lead-fullstack-app`, credited to him). With `DEMO_SYNTHETIC=true` nothing changes; with `false` the routes below serve real data from PostGIS.

| Task | Done |
|---|---|
| M3-01 database and loaders | Migrations 0002 to 0005 (contract value records, alerts and source status, briefs, audit/reviews/roles/job runs); all upgrade and downgrade on PostGIS 16. Transactional, repeatable loader: 13,669 areas, 9 runs, 52,786 cell results, 41,508 values. |
| M3-02 sign-in and safety | Area scope rule; 72-hour hold for **every role** (admin is not a bypass, doc 07); tiles only from the change-layer folder; sign-in limit (5 failures in 15 min); roles changed by an admin end old sessions; sign-in fails closed if the database is down; audit log without coordinates, passwords or request bodies. |
| M3-03 API | Layers, tiles, time series, area damage, trace a value, alerts, status, area list, values, people, services, validation, area summary, briefs (create, read, print), alert reviews, sources, admin audit, role changes, job retry. All checked against the OpenAPI schemas, also live on the real database. |
| M3-04 worker | Timer: fires every 30 min (Thanoban's FIRMS feed), night lights and clean-up daily (audit kept 30 days, expired briefs deleted). Port for local PostGIS configurable (`CIVISAR_DB_PORT`). |

Tests: 128 passing (1 skipped), lint, planning, scaffold and secrets checks clean.

## 3. Needs a team decision before the backend PR

**Two real-data paths now exist for the same routes.** Thanoban's [#21](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/21) (merged into dev) serves `/areas`, `/areas/{id}/damage`, `/areas/{id}/values`, `/alerts`, `/status` and `/public/map` from JSON files written by `worker.main --publish`. The backend branch serves them from PostGIS, as [21](../21_ML_BACKEND_FRONTEND_INTEGRATION.md) line 28 describes (checked, transactional PostGIS load). Merging the branch into dev conflicts in `backend/app/api/v1.py`, `core/config.py` and `core/permissions.py`.

Suggestion: keep one path (PostGIS, per doc 21), and keep from #21 what the branch does not have yet: the night-light publish step and the approved, bucketed public map (`PUBLIC_RELEASE_APPROVED`). Also decide on #21's `*` "all areas" scope; the branch uses the `south-lebanon-demo` scope for the same need.

## 4. Remaining

**Udula, next:**

- Resolve the overlap with #21 (section 3), then open the backend PR into dev.
- Docker Compose for real-data mode: `api` and `worker` still start with `DEMO_SYNTHETIC=true`, and the worker container runs `worker.main`, not the new timer (`worker.scheduler`).
- Public map: still suppressed on the branch (#21 has the approval-gated version).
- Layer file downloads (`/layers/{id}/files/{file_id}`): not built; raw radar files are sensitive, so this needs a decision first.

**Waiting on other people's data:**

| Needs | From | Unlocks |
|---|---|---|
| Population per H3 r9 cell (`population.csv.gz`: cell_id, pop_low, pop_high, pop_year) | Kisara (K-04) | People ranges, area summary, briefs (503 until then) |
| Facilities | Kisara | `/areas/{id}/facilities`, alert rings and facilities, severity rank |
| Road data (M2-04) | | Routes and closures |
| Shelter data (M2-05; owner unclear: the task file says Udula after H24, doc 17 says Rashiru) | | Shelters, capacity, field checks |
| Night-light history file (`NIGHTLIGHT_HISTORY`) | Thanoban | Possible power loss alerts in the timer |
| Frontend switch to `DEMO_SYNTHETIC=false` | Rashiru | Real data on screen |

## 5. Notes for the team

- **Contract:** AreaSummary people ranges must be whole numbers, so there is no way to say "people Unknown". Raise at H2 if population will be late.
- **Fire alerts:** `FIRE_RELEASE_DELAY_HOURS` defaults to 0 (shown to signed-in roles at once). Decide if fires should wait.
- **Sources:** the WorldPop source record is not in `sources.json` yet, so brief footnotes list only the radar sources.
- **Tests:** one of Rashiru's tests (`backend/tests/test_api.py`) now uses an empty data folder, so it gives the same result on every machine.
- Alert `rings`, `facilities` and `services` stay empty until Kisara's data is loaded.
