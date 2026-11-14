# Four-member ownership and handoffs

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Accountable roles

Source: ARCHITECTURE.md Parts 1–4; user requires exactly four members. No names invented. Exactly one member is accountable per task; reviewer is a different member. Domain ownership does not transfer when M3 exposes an API or M4 builds its presentation.

Updated 14 Nov 2026: the task IDs M1 to M4 are work-package IDs; the owner is the person above. ML is split by dataset (Udula: NISAR; Thanoban: night lights and fires) and all large downloads are Udula's.

| Member | Person | Primary responsibility | Task package | Branch prefix |
|---|---|---|---|---|
| Member 1 | Udula | NISAR damage model end to end; all large radar downloads and training (strong machine) | [Udula tasks](tasks/MEMBER_1_UDULA_NISAR_ML.md) | `feature/m1-*` |
| Member 2 | Thanoban | Small-data ML (night-light power loss, fire events), demo and submission. Trains on free Google Colab, not locally ([plan](18_THANOBAN_ML_PLAN_AND_COLAB.md)). No backend | [Thanoban tasks](tasks/MEMBER_2_THANOBAN_SMALL_DATA_ML.md) | `feature/m1-04-*` |
| Member 3 | Rashiru | **All frontend and all backend** (database, sign-in, safety, API, data, alerts, routes, shelters, worker, hosting) and **manager of all PRs** | [Rashiru tasks](tasks/MEMBER_3_RASHIRU_FRONTEND_BACKEND.md) | `feature/m2-*`, `feature/m3-*`, `feature/m4-*` |
| Member 4 | Chames | Not working on the project (14 Nov 2026 decision). No tasks, no reviews | [Chames note](tasks/MEMBER_4_CHAMES_BACKEND_DATA.md) | none |

Branches, PR rules and code ownership are in [17_TEAM_ASSIGNMENT_AND_BRANCHES.md](17_TEAM_ASSIGNMENT_AND_BRANCHES.md).

## Shared dependency matrix

| Task | Owner | Reviewer | Dependency | Checkpoint |
|---|---|---|---|---|
| M1-01 | Member 1 | Member 2 | none; H2 contract freeze | H2 IDs and manifests to M3; H8 registered crop inputs to M1-02 |
| M1-02 | Member 1 | Member 2 | M1-01; M2-01 grid; M3-01 schema | H16 first cells M2/M3; H24 COG/time-series manifest M3 |
| M1-03 | Member 1 | Member 3 | M1-02; permitted M2-03 context | H32 QA results to M3 trace and M4 Sources |
| M1-04 | Member 2 | Member 1 | none (uses `h3` directly); Udula's damage table for the final test run | H12 callable night-light and fire functions to M2-03; H24 real run; H32 test numbers to M4 Sources |
| M2-01 | Member 3 | Member 2 | M3-01 shared schema; source terms | H2 IDs to all; H12 base grid/residents/facilities inputs M3 |
| M2-02 | Member 3 | Member 2 | M2-01; M1-02 H16 cells; M2-03 services | H12 baseline to M3; H24 joined real-data summary to M3/M4 |
| M2-03 | Member 3 | Member 2 | M2-01 source terms; M3-04 scheduler | H16 callable jobs to M3; H24 alerts to M4 |
| M2-04 | Member 3 | Member 2 | M2-01 roads (M3-02/M3-03 for hand-off only) | H32 callable and revision tests to M3; seven facts to M4 |
| M2-05 | Member 3 | Member 2 | M2-01; M1-02; M2-02; M3-02 | H24 first list; H32 final callable M3/M4 |
| M2-06 | Member 2 | Member 1 | M2-02; licences; M3-02 privacy | H38 record deferred scope; later approved iteration |
| M3-01 | Member 3 | Member 1 | M1/M2 identifiers and fixtures | H2 v0.1 freeze; H12 mock API to M4 |
| M3-02 | Member 3 | Member 1 | M3-01; source safety rules | H12 role API; H24 protected data; H38 release blocker review |
| M3-03 | Member 3 | Member 1 | M3-01/02; M1-02; M2-02/03/04/05 | H24 real-data API; H32 routes/shelters/sources UI handoff |
| M3-04 | Member 3 | Member 1 | M2-03 adapters; M3-01/02 | H2 environment skeleton; H16 scheduler; H32 verified link if available; H40 backup |
| M4-01 | Member 3 | Member 2 | M3-01 H2 freeze; UI source | H2 client shapes; H12 sign-in and public preview |
| M4-02 | Member 3 | Member 2 | M4-01; M3-03; M1-02 layers | H16 map on fixtures; H24 real-data layers |
| M4-03 | Member 3 | Member 1 | M3-03; M2-02/04/05; M1-03 | H24 summary/alert; H32 route/shelter/source; H38 print |
| M4-04 | Member 3 | Member 1 | all MVP tasks; M1-03 science report; M3-02 security | H38 freeze; H40–44 video; H44–48 submission |


## RACI

R/A = one accountable implementer; C = named cross-review or domain consultation; I = notified. Team-wide gates have one accountable gate owner, with each member responsible for their own input.

| Deliverable | Udula (1) | Thanoban (2) | Rashiru (3) |
|---|---|---|---|
| NISAR radar cells, damage model and hold-out tests | R/A | C | C |
| Night-light and fire models | C | R/A | C |
| Strike-enrichment tests on the damage table (with the harness Thanoban wrote) | R/A | C | I |
| Base data, people, facilities, alert plumbing, routes, shelters | I | C | R/A |
| Database, sign-in, roles, API, storage, worker, hosting | C | I | R/A |
| UI, components, mock fixtures, QA | C | C | R/A |
| H2 contract freeze | C | C | R/A |
| H24 real-data integration gate | C | C | R/A |
| H38 full rehearsal and feature freeze | C | C | R/A |
| Video, submission and citation assembly | C | R/A | C |
| All PR merges, `dev` to `main` promotions | I | I | R/A |

## Workload balance

Approximate active hours after the 14 Nov 2026 decision: Udula about 31 (including the strike-enrichment tests), Thanoban about 16 plus the demo, **Rashiru about 85** (all frontend, all backend, all data work and PR management). That is more than one person can do in 48 hours, even with Claude Code and Claude Design, so the cut order in ARCHITECTURE.md is mandatory, not optional: after the NISAR map, sign-in with roles and the safety rules, cut Gemini box, coherence, phone layout and print, open-land shelters, late slider passes. Start every screen on mock data at H2. Once the ML tasks are done (about H30), Udula and Thanoban can take over named tasks from Rashiru by agreement, through a PR that changes the owner field.

## Team conventions

Freeze H3 IDs, row fields, units/CRS, dataset manifests, evidence enums, file naming and eight essential JSON contracts at H2. A later change starts with an API/schema PR and receiving-member acknowledgement. Use source/run IDs in filenames; UTC internal time; source precision retained; snake_case JSON fields; no bare scalar estimates; no secret fixtures. Small PRs at H2/H8/H16/H24/H32 rather than one giant member branch at H48. Every PR has one reviewer, source trace, tests, known limits and whether data is synthetic.

Contacts remain placeholders: Member 1 [name/contact pending], Member 2 [pending], Member 3 [pending], Member 4 [pending]. Handoffs fail if the receiver cannot reproduce the artifact or the manifest omits evidence, dates, units, sensitivity or schema version.
