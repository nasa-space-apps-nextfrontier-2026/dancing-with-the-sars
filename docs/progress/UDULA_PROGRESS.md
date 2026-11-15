# Udula: work log (M1 radar ML, M3 backend, U-01 to U-07)

Read this to see what Udula has finished, what is waiting, and what needs a team decision. Tasks: [Member 1](../tasks/MEMBER_1_UDULA_NISAR_ML.md) (M1-01 to M1-03); since 14 November 2026 the backend part of [Member 3](../tasks/MEMBER_3_RASHIRU_FRONTEND_BACKEND.md) (M3-01 to M3-04; Rashiru keeps the frontend); and the new-plan tasks U-01 to U-07 in doc 25 (`docs/25_NEW_PLAN_TASKS.md`). Backend guide: [31](../31_BACKEND_REAL_DATA.md). Last updated 15 November 2026.

## 1. Summary

**Everything is merged into `dev`.** No pull request is open (15 November 2026, `dev` at `7b1eec2`, which also includes Rashiru's `bc5b122`: `/map/context` and the frontend map bundle built on the U-06 tables).

| Area | State | PR |
|---|---|---|
| Radar ML (M1-01 to M1-03) | Merged | [#15](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/15), [#16](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/16), [#17](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/17) |
| Backend on PostGIS (M3-01 to M3-04) | Merged | [#38](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/38) |
| U-01 to U-04 (buildings, heights, height check, building table) | Merged | [#37](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/37) |
| U-05 (ranking, budget, insights, assistant) | Merged | [#41](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/41) |
| U-06 contract | Merged | [#24](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/24) |
| U-06 publish step (`worker.main --agents`) | Merged | [#42](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/42) |
| U-06 API endpoints on PostGIS | Merged | [#43](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/43) |
| U-07 key names | Merged | [#36](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/36) |
| Session `expires_at` fix (found in the end-to-end check) | Merged | [#44](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/44) |

Udula also fixed and merged the team pull requests that had to land with the backend (section 6). All recorded commits are under Udula's name with no AI co-author line.

## 2. Radar ML (M1-01 to M1-03): merged

| Item | PR |
|---|---|
| NISAR scene search and crop (track 151D, frame 72; BETA before, PROVISIONAL/V1 after) | [#15](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/15) |
| H3 r9 change features, Isolation Forest candidates, hold-out/eye/strike/time-slider tests | [#15](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/15) |
| Sentinel-1 cross-check (13 cells corroborated by a second radar) | [#16](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/16) |
| Contract export: 41,508 MetricValue, 38 Layer, 7 SourceRecord | [#17](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/17) |

Radar results are **candidates, not confirmed damage**. There is no independent damage assessment for Lebanon (no UNOSAT release), so validation is unavailable. Radar could not assess 46% of cells: no result there does not mean no damage. Private tables and contract rows were shared privately and never committed to this public repository.

## 3. Backend (M3-01 to M3-04): merged in #38

With `DEMO_SYNTHETIC=true` the synthetic scaffold stays active. With `false`, the real-data routes use PostGIS.

| Task | Done |
|---|---|
| M3-01 database and loaders | Migrations 0002-0006 (contract values, alerts/source status, briefs, audit/reviews/roles/jobs, agent outputs). Transactional loaders: 13,669 areas, 9 runs, 52,786 cell results, 41,508 values; agent outputs (section 5). |
| M3-02 sign-in and access rules | Area scopes; 72-hour hold for every role (admin is not a bypass); exact private-file allowlist; 5 failed sign-ins per 15 minutes; role changes end sessions; sign-in fails closed without the database; audit records without coordinates or passwords. |
| M3-03 API | Layers, tiles, manifest-allowlisted files with Range requests, time series, damage, trace, alerts, status, areas, values, people, services, validation, summaries, briefs, reviews, sources, admin audit, roles, job retry, and the U-06 routes (incidents, incident detail, area budget, buildings). |
| M3-04 worker | FIRMS every 30 minutes; night lights and clean-up daily; audit kept 30 days; expired briefs removed; local PostGIS port set with `CIVISAR_DB_PORT`. |

Work done while merging with `dev`: `v1.py` no longer imports the removed PR #21 JSON store (the API would not start); the C-01 handler registry answers only in synthetic mode, so its sample `/status` and `/sources` cannot hide the real routes; the registry test no longer deletes the real `/status` handler.

## 4. PR #21 overlap resolution

PostGIS is the single real-data store for `/areas`, `/areas/{id}/damage`, `/areas/{id}/values`, `/alerts`, `/status` and `/public/map`, consistent with [doc 21](../21_ML_BACKEND_FRONTEND_INTEGRATION.md). PR #21's JSON-backed API `Store`, `PUBLISHED_DIR` fallback, authenticated JSON route dispatch and `*` scope semantics were not kept. `PUBLISHED_DIR` is now only where `worker.main --publish/--agents` write files before `scripts.load_agent_outputs` loads them.

The behaviour kept from PR #21 is suppression of the public map. The team decided on 15 November 2026 to keep the public map off: `PUBLIC_RELEASE_APPROVED=true` cannot enable it, and a suppressed request never queries PostGIS. Any future publication needs artifact-bound approval and a humanitarian protection review under [doc 07](../07_SECURITY_PRIVACY_AND_RBAC.md) (licence/QA state, small and high-risk concentrations, spatial cohorts, snapshot differencing). H3 r8 aggregation or a three-cell threshold is not sufficient protection.

## 5. New plan (doc 25)

| Task | PR | Result (real data, 15 Nov 2026) |
|---|---|---|
| U-01 buildings | #37 | 268,536 OSM buildings; 97% untyped stays `unknown`; 421 ruin/destroyed/construction tags kept as information only |
| U-02 heights | #37 | OSM levels, then GHSL/GHS-OBAT, then type default: 241,770 GHSL, 26,343 default, 423 OSM; 3D-GloBFP not used |
| U-03 height check | #37 | 57% within one storey (70% target not met); 83% range coverage; towers about 18 m too low ([report](BUILDING_HEIGHT_CHECK.md)) |
| U-04 building table | #37 | Heights, floors, use, cell result and second-sensor flag; 12,414 buildings in candidate cells. Built with Kisara's population file (K-04): residents 1,305,218-1,863,142; with people not allocated and people in cells without buildings this adds up exactly to the population totals (1,635,592-2,298,561). High is never below low. |
| U-05 ranking | #41 | 131 incidents; seven named score parts; ordered by the low score, with a "could rank higher" flag where data is missing (missing data never pushes an incident up) |
| U-05 budget | #41 | US$0.4-4.3 billion and 0.5-14 years for the whole demo box; labelled a planning indication, with sourced assumptions |
| U-05 insights | #41 | 6 template statements; every number comes from computed values |
| U-05 assistant | #41 | Options, not orders; role limits; evacuation suggested only for a current fire |
| U-06 contract | #24 | `/incidents`, `/incidents/{id}`, `/areas/{id}/budget`, `/buildings`; existing endpoints unchanged |
| U-06 publish | #42 | Incidents, insights, recommendations per role, budgets and 2,201 building files (no residents per building) |
| U-06 endpoints | #43 | Migration 0006 and `scripts.load_agent_outputs`; hold, scope, role and bbox limits on every call; 503 until outputs are loaded |
| U-07 keys | #36 | Key names only in `.env.example`; owners and expiry in [KEYS.md](KEYS.md), no values |

## 6. Team pull requests fixed and merged on 15 November 2026

The team asked Udula to merge everything together. Fixes made so each PR was correct before merging:

| PR | Owner | Fix before merge |
|---|---|---|
| #25-#29 (boundaries, H3 grid, facilities, population, source register) | Kisara | Data files (`population.csv.gz`, `grid_r9.csv.gz`, `boundaries.geojson`, `facilities.csv`) removed from Git and the PRs squash-merged, so no data file is in `dev` history; boundaries crash on empty geometry fixed; test module renamed to avoid a name clash; dependency conflicts resolved |
| #22, #23, #31 (traceability, people/facilities, alerts read) | Chames | Reworked onto the PostGIS backend; registry handlers serve sample data only in synthetic mode; synthetic `/sources` serves the fixture only, never the real register stamped as synthetic |
| #35 | Udula | Leftover merge-conflict markers removed from `.gitignore` |
| #44 | Udula | `POST`/`GET /session` now return `expires_at`, as the contract requires |

Tests that need packages CI does not install (pandas, pyarrow) skip cleanly instead of failing.

## 7. End-to-end check of merged `dev` (15 November 2026)

| Check | Result |
|---|---|
| GitHub CI (python-and-contracts, frontend) | Passed on #43 and #44 |
| Tests, CI-like environment | 226 passed, 12 skipped |
| Tests, full environment | 273 passed, 1 skipped |
| Ruff, contract validator (45 operations), scaffold, secrets | Pass |
| Building table, worker publish (live FIRMS), agents on real data | Pass (numbers in section 5). One run crashed once while loading pandas; the rerun passed and it did not happen again. |
| Worker scheduler once against PostGIS | FIRMS ok (1 new fire alert); night lights unavailable (no history file on this machine); clean-up ok |
| PostGIS 16 in Docker: migration 0006 upgrade, downgrade, upgrade | Pass |
| Agent output load | 131 incidents, 393 recommendations, 6 insights, 131 budgets, 268,536 buildings; all geometries valid, EPSG:4326; a reload replaces the previous run |
| API smoke test, real-data mode, temporary local users | 47 of 47 calls pass and match the contract schemas (including Rashiru's `/map/context`): logged-out 401; officer 403 on admin audit; narrow-scope officer sees only their area (also in `/map/context`) and gets 403 elsewhere; oversized `/buildings` bbox refused; no resident fields; printed brief has the RESTRICTED banner. Test rows (brief, review, audit) deleted afterwards. |

## 8. Decisions and reviews still required

1. **Height target:** 57% within one storey rather than 70%; proposed wording is a satellite-estimated range with a warning that towers are underestimated.
2. **Fire delay:** `FIRE_RELEASE_DELAY_HOURS=0` shows fires to signed-in roles at once; decide whether a delay is needed.
3. **Rebuild scope:** `PROJECT_PLAN.md` says no rebuilding while doc 24 adopted a budget feature; reconcile scope.
4. **Full-AOI COG access:** decide whether broad `south-lebanon-demo` users keep downloads; cell-scoped users fail closed.
5. **Public map:** kept off (decision of 15 November). Only revisit with the review in section 4.

Points kept in the product: no residents per building are exposed; people stay at cell level; unknown cells are grey in the 3D view and never look undamaged; building damage is always the enclosing cell result; building heights describe the stock of about 2018, before the war.

## 9. Remaining and dependencies

| Needs | From | State | Unlocks |
|---|---|---|---|
| Facilities loaded into the backend (K-03 merged in #27) | Kisara / Udula | Not loaded; `/areas/{id}/facilities` returns 503 | Facilities route, alert rings, ranking facility part. Must respect doc 07 (no public inventory of critical facilities). |
| Source register passing the `SourceRecord` schema (K-05 merged in #29) | Kisara | Fails the schema (extra `update_frequency`, nulls, 17 "VERIFY" values); not served as real data | Real `/sources` from the register |
| Night-light history (`NIGHTLIGHT_HISTORY`) | Thanoban | Not on this machine | Possible power-loss alerts |
| Roads and shelters | M2-04, M2-05 | Not started | Routes, closures and shelters (503 until then) |
| Frontend real-data switch | Rashiru | Started in `bc5b122` (`/map/context`, map bundle, timeline); API checked, not checked in a browser here | Real data in the frontend |

Known limits: sessions, revocation and the sign-in limit are kept in process memory, so a multi-worker deployment needs shared storage first; a database outage during the final job-status write still needs stale-run recovery; there is no independent damage validation for Lebanon. This backend is a demo, not production-ready. The WorldPop source record is still missing from `sources.json`.
