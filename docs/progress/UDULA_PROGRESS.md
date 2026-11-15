# Udula: work log (M1 radar ML, M3 backend, U-01 to U-07)

Read this to see what Udula has finished, what is waiting, and what needs a team decision. Tasks: [Member 1](../tasks/MEMBER_1_UDULA_NISAR_ML.md) (M1-01 to M1-03); since 14 November 2026 the backend part of [Member 3](../tasks/MEMBER_3_RASHIRU_FRONTEND_BACKEND.md) (M3-01 to M3-04; Rashiru keeps the frontend); and the new-plan tasks U-01 to U-07 in doc 25 (`docs/25_NEW_PLAN_TASKS.md`). Backend guide: [31](../31_BACKEND_REAL_DATA.md). Last updated 15 November 2026.

## 1. Summary

| Area | State |
|---|---|
| Radar ML (M1-01 to M1-03) | **Merged** (#15, #16, #17) |
| Backend (M3-01 to M3-04) | Built; `origin/dev` merged locally; **no backend PR yet** |
| U-01 to U-05 (buildings, heights, height check, building table, four agents) | Built, tested, pushed; PRs not opened yet |
| U-06 contract | **PR #24 open**, CI green, waiting for Rashiru's review |
| U-06 publish step | Built, tested, pushed |
| U-06 API endpoints | **Not started**: waits for PR #24 |
| U-07 key names | Built and pushed |

All recorded commits are under Udula's name with no AI co-author line.

## 2. Radar ML (M1-01 to M1-03): merged

| Item | PR |
|---|---|
| NISAR scene search and crop (track 151D, frame 72; BETA before, PROVISIONAL/V1 after) | [#15](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/15) |
| H3 r9 change features, Isolation Forest candidates, hold-out/eye/strike/time-slider tests | [#15](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/15) |
| Sentinel-1 cross-check (13 cells corroborated by a second radar) | [#16](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/16) |
| Contract export: 41,508 MetricValue, 38 Layer, 7 SourceRecord | [#17](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/17) |

Radar results are **candidates, not confirmed damage**. There is no independent damage assessment for Lebanon (no UNOSAT release), so validation is unavailable. Radar could not assess 46% of cells: no result there does not mean no damage. Private tables and contract rows were shared privately and never committed to this public repository.

## 3. Backend (M3-01 to M3-04): `feature/m3-01-backend-foundation`

With `DEMO_SYNTHETIC=true` the synthetic scaffold remains active. With `false`, implemented real-data routes use PostGIS.

| Task | Done |
|---|---|
| M3-01 database and loaders | Migrations 0002-0005 (contract values, alerts/source status, briefs, audit/reviews/roles/jobs); upgrades and downgrades were previously checked on PostGIS 16. Transactional loader record: 13,669 areas, 9 runs, 52,786 cell results, 41,508 values. |
| M3-02 sign-in and safety | Area scopes; 72-hour hold for every role; exact private-file allowlist; 5 failed sign-ins per 15 minutes; role changes end sessions; sign-in fails closed without the database; coordinate/password-free audit records. |
| M3-03 API | Layers, tiles, manifest-allowlisted files with Range requests, time series, damage, trace, alerts, status, areas, values, people, services, validation, summaries, briefs, reviews, sources, admin audit, roles and job retry. |
| M3-04 worker | FIRMS every 30 minutes; night lights and cleanup daily; audit retained 30 days; expired briefs removed; local PostGIS port configurable with `CIVISAR_DB_PORT`. |

Historical verification before the completion and synchronization passes was 128 passing tests with 1 skipped. Later pre-merge results are recorded in section 9; they are not a substitute for post-merge validation.

## 4. PR #21 overlap resolution

Resolved locally on 14 November 2026 and synchronized with `origin/dev` in merge commit `c6b89f2`. PostGIS remains the sole authoritative real-data API path for `/areas`, `/areas/{id}/damage`, `/areas/{id}/values`, `/alerts`, `/status` and `/public/map`, consistent with [doc 21](../21_ML_BACKEND_FRONTEND_INTEGRATION.md). PR #21's JSON-backed API `Store`, `PUBLISHED_DIR` fallback, authenticated JSON route dispatch and `*` scope semantics were not retained.

The retained safe behavior from PR #21 is suppression of the public map. Publication is now permanently hard-disabled in this implementation: `PUBLIC_RELEASE_APPROVED=true` cannot enable it, and a suppressed request does not construct a database engine or query PostGIS. This PR does not publish H3 identifiers, counts, scores, geometries, artifacts or private files.

Artifact-bound approval and humanitarian protection review are future requirements. A later design must review licence/QA state, small, unique and high-risk concentrations, spatial cohorts, snapshot differencing/re-identification risk and the active-conflict context under [doc 07](../07_SECURITY_PRIVACY_AND_RBAC.md). H3 r8 aggregation or a three-cell threshold is not sufficient protection.

## 5. New plan (doc 25)

| Task | Branch | Result |
|---|---|---|
| U-01 buildings | `feature/u-01-buildings-base` | 268,536 OSM buildings; 97% untyped remains `unknown`; 421 ruin/destroyed/construction tags retained as information only |
| U-02 heights | `feature/u-02-building-heights` | OSM levels, then GHSL/GHS-OBAT, then type default; 90% GHSL, 9.8% default, 0.16% OSM; 3D-GloBFP not used |
| U-03 height check | `feature/u-03-height-check` | 57% within one storey (70% target not met); 83% range coverage; towers about 18 m too low |
| U-04 building table | `feature/u-04-building-table` | Heights, floors, use, cell result and second-sensor flag; 12,414 buildings in candidate cells; residents empty until population loads |
| U-05 ranking | `feature/u-05-agent-ranking` | 131 incidents; seven named score parts; missing data never pushes an incident upward |
| U-05 budget | `feature/u-05-agent-budget` | US$0.4-4.3 billion and 0.5-14 years, explicitly a planning indication with assumptions |
| U-05 insights | `feature/u-05-agent-insights` | Template statements; every number comes from computed values |
| U-05 assistant | `feature/u-05-agent-assistant` | Options, not orders; role limits; evacuation only for a current fire |
| U-06 contract | `feature/u-06-contract-incidents`, [PR #24](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/24) | `/incidents`, `/incidents/{id}`, `/areas/{id}/budget`, `/buildings`; existing endpoints unchanged; CI green |
| U-06 publish | `feature/u-06-publish-agents` | Agent incidents, insights, role recommendations, budgets and 2,201 building files validated against PR #24 |
| U-07 keys | `feature/u-07-keys` | Key names only in `.env.example`; ownership and expiry documented without values |

## 6. Decisions and safety review still required

1. **Public-map humanitarian review and artifact-bound approval:** the endpoint is hard-suppressed. A future implementation must bind approval to an immutable artifact and address unique/high-risk cells, spatial cohorts and snapshot differencing before any publication path is added.
2. **Height target:** 57% within one storey rather than 70%; proposed wording is a satellite-estimated range with a tower underestimation warning.
3. **People unknown:** AreaSummary requires whole-number ranges and cannot express an unknown people value; contract change may be needed if population remains late.
4. **Fire delay:** `FIRE_RELEASE_DELAY_HOURS=0` shows fires to signed-in roles immediately; decide whether a delay is required.
5. **Rebuild scope:** `PROJECT_PLAN.md` says no rebuilding while doc 24 adopted a budget feature; reconcile scope.
6. **Full-AOI COG access:** decide whether broad `south-lebanon-demo` users should retain downloads; cell-scoped users fail closed.

Safety points: no residents per building are exposed; people stay at cell level. The 3D view uses grey for unknown cells, and building damage is always the enclosing cell result. Building heights describe the approximately 2018 stock, before the war.

## 7. Remaining and dependencies

**Backend:** review the synchronized working tree before a PR; configure Docker Compose for real-data API/worker operation; implement U-06 endpoints only after PR #24; keep the public map hard-suppressed pending section 6. This backend is not production-ready.

| Needs | From | State | Unlocks |
|---|---|---|---|
| Population per H3 r9 cell | Kisara (K-04) | PR #28 open | People ranges, summary, briefs, residents and ranking people part |
| Facilities | Kisara (K-03) | PR #27 open | Facilities route, alert rings and ranking facility part |
| Night-light history (`NIGHTLIGHT_HISTORY`) | Thanoban | Not sent | Possible power-loss alerts |
| Contract PR #24 review | Rashiru | Open, CI green | U-06 endpoints |
| Roads and shelters | M2-04, M2-05 | Not started | Routes, closures and shelters |
| Frontend real-data switch | Rashiru | Not done | Real data displayed in the frontend |

Housekeeping: the WorldPop source record is absent from `sources.json`; alert rings/facilities/services remain incomplete until their inputs load; `backend/tests/test_api.py` uses an empty data folder for deterministic behavior. The repository Contributors box may still show an old removed co-author and may require a GitHub Support refresh.

## 8. Backend completion pass (14 November 2026)

Completed without changing database integration or schema:

- Added real-mode `GET /layers/{layer_id}/files/{file_id}` dispatch with exact manifest matching, directory containment, role/release/AOI-scope checks, private no-store caching and HTTP Range support.
- Resolved exported `data/...` paths consistently under configured `DATA_ROOT`; included the root in the catalogue cache key.
- Applied brief `as_of` to artifact, release, alert and value selection; future snapshots are rejected so they cannot bypass the 72-hour hold.
- Scoped damage and summary artifact selection to the requested area's artifact parent.
- Moved bbox filtering to indexed PostGIS `&&` and `ST_Intersects` predicates.
- Returned explicit 503 unavailable states for missing road, closure and shelter inputs.

Final correctness and safety pass on 15 November 2026:

- Hard-disabled public-map publication. Environment configuration cannot enable it, and suppressed requests never construct an engine or query PostGIS.
- Made radar-summary missing data explicit: no eligible artifact, held-only evidence or an artifact with no released area evidence returns unavailable instead of a false zero. A numerical zero is returned only when eligible released evidence supports it.
- Made radar artifact selection area-scoped and release-aware. Newer held artifacts do not hide older eligible artifacts, and results are fetched by `artifact_id`, so duplicate run IDs cannot mix artifacts.
- Applied historical `as_of` cutoffs to summary, values, people, services and brief creation. Observations or releases after the cutoff are excluded.
- Made role changes and alert reviews commit their audit event in the same transaction as the privileged mutation. Manual job retries require a durable start audit before execution, and raised job exceptions are persisted as failed rather than left running.
- Documented that a database outage during final job-status persistence still needs operational stale-run recovery, and that process-local sessions, revocation and login-rate limiting require shared storage before multi-worker deployment.

## 9. Verification history and blockers

The pre-merge completion run recorded **138 passed, 1 skipped**. The first post-merge run recorded **146 passed, 1 skipped**. After the final correctness and safety fixes, the complete suite recorded **153 passed, 1 skipped, 1 warning**. Ruff, planning-contract validation, scaffold validation, secret scanning, the conflict-marker scan, and CRLF-aware staged and unstaged diff checks passed.

The skipped test requires a disposable PostGIS database supplied through `CIVISAR_TEST_DATABASE_URL`; it was not run against Supabase or any production database. No live PostGIS integration verification has been completed. The warning is the existing Starlette TestClient/httpx deprecation warning. No real NISAR ingestion or end-to-end empirical data validation has been completed, so passing mocked/unit/security tests do not establish empirical correctness or production readiness.

No loader, migration, seed, schema operation or live database write was performed during the completion, synchronization or final safety work. Remaining limitations are: humanitarian review and immutable artifact-bound public approval; shared multi-worker session/revocation/rate-limit storage; disposable live-PostGIS integration verification; real NISAR inputs and end-to-end empirical validation; operational stale-job recovery after database outages; population, facilities, roads, shelters and night-light inputs; and the U-06 dependency on PR #24. The public map remains hard-suppressed.
