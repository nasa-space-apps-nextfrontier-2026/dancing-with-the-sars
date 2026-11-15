# Team update, 15 November 2026: everything is merged into `dev`

From Udula. Everything is now merged into `dev` and the whole system was checked end to end. **Please pull `dev`.** The team asked me to finish the open items too, so sections 4 and 5 are now done (updated later on 15 November, PRs #47 to #50); only the night-light history is still being built.

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
| Progress log, team update | #45, #46 |
| Finalisation: facilities, source register, landing page with sign-in for real data, decisions, demo setup | #48, #49, #47, #50 |

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

**Thanoban (#47, landing page and open dashboard)**
- Kept the landing page and the open dashboard with the labelled sample data. Put sign-in back for **real data** (project rule: login required): `/signin` and "Sign in for real data" in the menu.
- Removed the calls to the public OSRM routing server (doc 03: no external routing).
- The sample data named a real school and mosque in Khiam (and 5 other real buildings) as shelter options on a public page; they are now "Sample shelter N (building type)".

**Everyone**
- Sign-in (`POST` and `GET /session`) was missing `expires_at`, which the contract requires. Fixed in #44.
- Demo mode read real files from `data/local` (population, facilities, grid) and labelled them synthetic; it now serves sample records only (#48).
- The dashboard showed a made-up "residents" estimate per building, also on real data; removed (doc 07) (#50).
- Missing inputs (facilities on the map, roads, night lights) showed as 0; they now read Unknown with the reason (#47).

## 3. End-to-end check of `dev`

| Check | Result |
|---|---|
| Tests, CI-like setup | 238 passed, 12 skipped |
| Tests, all packages installed | 285 passed, 1 skipped; frontend 30 tests, lint, type check and build pass |
| Ruff, contract check (45 operations), scaffold, secrets | Pass |
| GitHub CI | Passed on every PR |
| Building table (real data) | 268,536 buildings, built with Kisara's population file. Residents plus unallocated people add up exactly to the population totals (1.64M to 2.30M). |
| Agents (real data) | 131 incidents, 6 insights, budgets per area and for the whole demo box |
| Live fire feed | Works (1 new fire alert) |
| Database (PostGIS 16 in Docker) | All migrations up to 0006 install, roll back and reinstall cleanly. All agent outputs loaded; every building shape is valid. |
| API in real-data mode | 50 of 50 calls pass and match the contract, including Rashiru's `/map/context` and the facilities route |

What the API check confirmed:
- Logged-out users get 401.
- Users see only their own area.
- Data in the 72-hour hold stays hidden for every role, admin included.
- No resident counts per building are exposed.
- Printed briefs carry the RESTRICTED banner.

## 4. Open items: done

| Item | Result | PR |
|---|---|---|
| Facilities in the backend | 383 facilities inside Lebanon loaded (160 of Kisara's 543 were in northern Israel and are dropped). `/areas/{id}/facilities`: analysts get type and status without the location, officer and above get the point. | #48 |
| Source register | Rewritten to the 6 non-radar sources we really use (Black Marble, FIRMS, WorldPop, GHS-OBAT, OSM facilities, HDX boundaries); every record matches `SourceRecord`. `/sources` serves 13 records. | #49 |
| Frontend with real data | Checked in the browser: signed in, 100 real ranked incidents and the real NISAR timeline; signed out, the labelled sample. | #47 |
| Roads and shelters | Demo-only (doc 07: no real routes or shelter sites in the hackathon). Real mode says "unavailable". | #50 (decision D21) |
| One-command demo setup | `python -m scripts.demo_setup` runs the whole real-data setup; checked end to end. | #50 |
| Night-light history | Script ready to run locally; waiting for the Earthdata token, then power-loss alerts turn on. | next PR |

## 5. Decisions: taken

All recorded in `docs/12_RISK_REGISTER_AND_DECISION_LOG.md` (D19 to D29), each with where it is enforced: public map off; public demo with sign-in for real data; routes and shelters demo-only; heights as a range with the tower warning; no fire alert delay (FIRMS is already public); budget-only rebuild scope; radar downloads for whole-box users only; facilities rules; no people per building; Unknown instead of zero; source list.

To run it yourself: `python -m scripts.demo_setup` (see `docs/31_BACKEND_REAL_DATA.md` section 0).
