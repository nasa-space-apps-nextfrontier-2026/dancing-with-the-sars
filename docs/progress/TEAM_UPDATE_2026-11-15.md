# Team update, 15 November 2026: everything is merged into `dev`

From Udula. Everything is now merged into `dev` and the whole system was checked end to end. There are no open pull requests. **Please pull `dev`**, read section 4 for what is still open for you, and answer the decisions in section 5.

Details: [Udula's progress log](UDULA_PROGRESS.md) and the [backend guide](../31_BACKEND_REAL_DATA.md).

## 1. What got merged

| Area | PRs |
|---|---|
| Radar ML | #15, #16, #17 |
| Backend on PostGIS | #38 |
| U-01 to U-04 (buildings, heights, height check, building table) | #37 |
| U-05 (ranking, budget, insights, assistant) | #41 |
| U-06 (contract, publish step, API endpoints) | #24, #42, #43 |
| U-07 (key names) | #36 |
| Kisara (boundaries, H3 grid, facilities, population, source register) | #25, #26, #27, #28, #29 |
| Chames (traceability, people/facilities, alerts read) | #22, #23, #31 |
| Fixes | #35 (`.gitignore`), #44 (session) |
| Progress log | #45 |

## 2. What was fixed before merging

**Kisara**
- Data files (population, grid, boundaries, facilities) were removed from Git. The repository is public, so data stays in `data/` on your own machine only. The PRs were squash-merged, so none of those files are in the `dev` history.
- Fixed a crash in the boundaries step on empty shapes.
- Renamed one test file that had the same name as one of Chames's.
- Resolved the requirements conflicts.

**Chames**
- The PRs were moved onto the PostGIS backend.
- Registry handlers now answer only in demo (synthetic) mode. Before, they hid the real `/status` and `/sources` in real-data mode.
- The registry test no longer deletes the real `/status` handler.
- Synthetic `/sources` serves only the sample record, never the real list marked as synthetic.

**Everyone**
- Sign-in (`POST` and `GET /session`) was missing `expires_at`, which the contract requires. Fixed in #44.

## 3. End-to-end check of `dev`

| Check | Result |
|---|---|
| Tests, CI-like setup | 226 passed, 12 skipped |
| Tests, all packages installed | 273 passed, 1 skipped |
| Ruff, contract check (45 operations), scaffold, secrets | Pass |
| GitHub CI | Passed on every PR |
| Building table (real data) | 268,536 buildings, built with Kisara's population file. Residents plus unallocated people add up exactly to the population totals (1.64M to 2.30M). |
| Agents (real data) | 131 incidents, 6 insights, budgets per area and for the whole demo box |
| Live fire feed | Works (1 new fire alert) |
| Database (PostGIS 16 in Docker) | All migrations up to 0006 install, roll back and reinstall cleanly. All agent outputs loaded; every building shape is valid. |
| API in real-data mode | 47 of 47 calls pass and match the contract, including Rashiru's `/map/context` |

What the API check confirmed:
- Logged-out users get 401.
- Users see only their own area.
- Data in the 72-hour hold stays hidden for every role, admin included.
- No resident counts per building are exposed.
- Printed briefs carry the RESTRICTED banner.

## 4. What is still open, and who

| Who | What | Why it matters |
|---|---|---|
| Kisara | Facilities are merged (#27) but not loaded into the backend yet. We should load them together. Doc 07 says there must be no public list of critical facilities. | The facilities route shows "unavailable"; alert rings and the facility part of the ranking stay empty |
| Kisara | `data/manifests/sources.json` fails the `SourceRecord` schema: extra `update_frequency` field, some empty values, 17 entries still say "VERIFY". The WorldPop record is missing. | Until it passes, `/sources` cannot serve it as real data |
| Thanoban | Send the night-light history file (`NIGHTLIGHT_HISTORY`) | Possible power-loss alerts stay off without it |
| Rashiru | Check the map screens with real data in the browser (the API side of `/map/context` is checked). Please use PRs instead of pushing straight to `dev`. | Real data shown in the frontend |
| M2 | Roads and shelters are not started | Routes, closures and shelters endpoints return "unavailable" until then |

## 5. Decisions we still need

1. **Height accuracy:** heights are within one storey for 57% of buildings, not the 70% target. Proposal: show a range and warn that towers are underestimated.
2. **Fire alert delay:** fire alerts go out with no delay (`FIRE_RELEASE_DELAY_HOURS=0`). Do we want a delay?
3. **Rebuild scope:** `PROJECT_PLAN.md` says no rebuilding, but doc 24 added a budget feature. We need to agree on one.
4. **Radar image downloads:** should users with access to the whole demo box be allowed to download the radar image files (COG files)? Users limited to smaller areas cannot.
5. **Public map:** stays off, as agreed today.

Reply in the team chat or edit this file through a PR.
