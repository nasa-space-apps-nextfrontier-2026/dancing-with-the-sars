# Udula: work log (M1 radar ML, M3 backend, U-01 to U-07)

Read this to see what Udula has finished, what is waiting, and what needs a team decision. Tasks: [Member 1](../tasks/MEMBER_1_UDULA_NISAR_ML.md) (M1-01 to M1-03); since 14 November 2026 the backend part of [Member 3](../tasks/MEMBER_3_RASHIRU_FRONTEND_BACKEND.md) (M3-01 to M3-04; Rashiru keeps the frontend); and the new-plan tasks U-01 to U-07 in [doc 25](../25_NEW_PLAN_TASKS.md). Last updated 14 November 2026 (evening).

## 1. Summary

| Area | State |
|---|---|
| Radar ML (M1-01 to M1-03) | **Merged** (#15, #16, #17) |
| Backend (M3-01 to M3-04) | Built and pushed; **no PR yet** (waits for the data-store decision, section 5) |
| U-01 to U-05 (buildings, heights, height check, building table, four agents) | Built, tested, pushed; PRs not opened yet |
| U-06 contract | **PR #24 open**, CI green, waiting for Rashiru's review |
| U-06 publish step | Built, tested, pushed |
| U-06 API endpoints | **Not started**: waits for PR #24 and the data-store decision |
| U-07 key names | Built and pushed |

All commits are under Udula's name with no AI co-author line.

## 2. Radar ML (M1-01 to M1-03): merged

| Item | PR |
|---|---|
| NISAR scene search, download and crop (track 151D, frame 72) | [#15](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/15) |
| Change features on H3 r9 cells, Isolation Forest anomaly model, candidate classes, tests (hold-out false alarms, eye check, strike context with UCDP, time slider) | [#15](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/15) |
| Sentinel-1 cross-check (13 cells where a second radar agrees: Corroborated) | [#16](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/16) |
| Contract export: 41,508 MetricValue, 38 Layer, 7 SourceRecord | [#17](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/17) |

Radar results are **candidates, not confirmed damage**. There is no independent damage assessment for Lebanon (no UNOSAT release), so validation is reported as unavailable. The radar could not assess 46% of cells: no result there does not mean no damage.

## 3. Backend (M3-01 to M3-04): branch `feature/m3-01-backend-foundation`

| Task | Done |
|---|---|
| M3-01 database and loaders | Migrations 0002-0005 (contract values, alerts, source status, briefs, audit log, alert reviews, role changes, job runs); transactional loader: 13,669 areas, 9 runs, 52,786 cell results, 41,508 values |
| M3-02 sign-in and safety | Area scope; 72-hour hold for every role (admin is not a bypass, doc 07); 5 failed sign-ins per 15 min; role changes end old sessions; sign-in fails closed without the database; audit log without coordinates or passwords |
| M3-03 API | Layers, tiles, time series, area damage, trace, alerts, status, areas, values, people, services, validation, area summary, briefs (create, read, print), alert reviews, sources, admin audit, role changes, job retry |
| M3-04 worker | Fires every 30 min, night lights and clean-up daily |

128 tests pass. Guide: `docs/31_BACKEND_REAL_DATA.md` on that branch.

## 4. New plan (doc 25)

| Task | Branch | Result |
|---|---|---|
| U-01 buildings | `feature/u-01-buildings-base` | 268,536 OSM buildings in the demo box; 97% untyped (use "unknown", not guessed); 421 OSM ruin/destroyed/construction tags kept as information only |
| U-02 heights | `feature/u-02-building-heights` | Order: OSM levels, then GHSL via GHS-OBAT (EU JRC, CC BY 4.0, 32 MB), then a type default. **3D-GloBFP not used**: all authors at Chinese institutions (and 40 GB). 90% GHSL, 9.8% default, 0.16% OSM |
| U-03 height check | `feature/u-03-height-check` | Held-out check on 414 OSM-tagged buildings: **57% within one storey (target 70% not met)**; the range holds the true height for **83%**; towers about 18 m too low. Note: `docs/progress/BUILDING_HEIGHT_CHECK.md` on that branch |
| U-04 building table | `feature/u-04-building-table` | One row per building: heights, floors, use, cell damage result, second-sensor flag; 12,414 buildings in candidate cells (about 7 million m2 of floor area). Residents stay empty until the population file is loaded |
| U-05 ranking | `feature/u-05-agent-ranking` | 131 incidents; score range from seven named parts; ordered by what is known, so missing data never pushes an incident up |
| U-05 budget | `feature/u-05-agent-budget` | Demo box: US$0.4-4.3 billion, 0.5-14 years, "Planning indication only". Cost per m2 anchored to the World Bank Syria assessment (Aug 2025), widened for Lebanon; crews, output and delays marked "assumption" |
| U-05 insights | `feature/u-05-agent-insights` | Template sentences; every number comes from computed values |
| U-05 assistant | `feature/u-05-agent-assistant` | "CIVISAR assistant": options, not orders; role limits; evacuation only for a current fire |
| U-06 contract | `feature/u-06-contract-incidents`, [PR #24](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/24) | `/incidents`, `/incidents/{id}`, `/areas/{id}/budget`, `/buildings`; existing endpoints unchanged; CI green |
| U-06 publish | `feature/u-06-publish-agents` | `python -m worker.main --agents` writes incidents, insights, recommendations per role, budgets and 2,201 building files; all validated against PR #24 |
| U-07 keys | `feature/u-07-keys` | Key names in `.env.example`; `docs/progress/KEYS.md` with names, owners, expiry (no values) |

## 5. Needs a team decision

1. **One data store.** Three versions of the same routes exist: Thanoban's #21 (JSON files, merged), Chames's #22 and #23, and the PostGIS backend. Reviews, briefs, the audit log and role changes must save data, so a database is needed anyway (doc 21 also says PostGIS). Proposal: PostGIS is the one store, the worker's publish output is loaded into it, and #21's public-map approval gate and night-light step are kept.
2. **Height target.** 57% within one storey instead of 70%. Proposal: accept the wider ranges and the label "Height estimated from satellite data (range); towers may be much taller."
3. **People unknown.** The contract needs whole-number people ranges, so "people unknown" cannot be expressed. Fix at H2 if population is late.
4. **Fire alert delay.** Fire alerts show to signed-in roles at once (`FIRE_RELEASE_DELAY_HOURS=0`). Should they wait?
5. **Rebuild scope.** `PROJECT_PLAN.md` still says "No rebuilding"; doc 24 adopted the budget feature.

## 6. Safety points for the new plan

- No residents per building in the API (doc 07): people stay at cell level; per-building numbers are used only inside the budget.
- The 3D view shows "unknown" cells in grey; damage on buildings is always the cell result.
- Building heights describe the stock around 2018, before the war.

## 7. Remaining

**Udula, after the decisions:** the four U-06 endpoints; the backend PR; PRs for the U branches; check the budget's cost per m2 against the World Bank Lebanon assessment (2025).

**Waiting on others:**

| Needs | From | State | Unlocks |
|---|---|---|---|
| Population per H3 r9 cell (K-04) | Kisara | PR #28 open | People ranges, area summary, briefs, residents in the building table, the people part of the ranking |
| Facilities (K-03) | Kisara | PR #27 open | Facilities route, alert rings, facility part of the ranking |
| Night-light history (`NIGHTLIGHT_HISTORY`) | Thanoban | Not sent | Possible power loss alerts |
| Review of contract PR #24 | Rashiru | Open, CI green | U-06 endpoints |
| Road and shelter data | M2-04, M2-05 | Not started | Routes, closures, shelters |
| Frontend switch to `DEMO_SYNTHETIC=false` | Rashiru | Not done | Real data on screen |

**Housekeeping:** the dev `.gitignore` still has leftover merge-conflict markers; the WorldPop source record is missing from `sources.json`; the repo's Contributors box still shows an old co-author from a removed commit (a repo admin can ask GitHub Support to refresh it).
