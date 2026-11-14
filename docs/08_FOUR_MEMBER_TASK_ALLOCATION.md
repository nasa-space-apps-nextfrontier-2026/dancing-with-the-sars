# Four-member ownership and handoffs

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Accountable roles

Source: ARCHITECTURE.md Parts 1–4; user requires exactly four members. No names invented. Exactly one member is accountable per task; reviewer is a different member. Domain ownership does not transfer when M3 exposes an API or M4 builds its presentation.

| Member | Primary responsibility | Task package | Feature branch from dev |
|---|---|---|---|
| Member 1 | Radar / remote sensing / ML | [M1 tasks](tasks/MEMBER_1_RADAR_ML.md) | feature/m1-radar-damage |
| Member 2 | Geodata / humanitarian analytics / alerts / local routes / shelters | [M2 tasks](tasks/MEMBER_2_GEODATA_ALERTS.md) | feature/m2-geodata-alerts |
| Member 3 | Backend / DB / safety / orchestration / DevOps | [M3 tasks](tasks/MEMBER_3_BACKEND_SECURITY.md) | feature/m3-backend-security |
| Member 4 | Frontend / UI fixtures / QA-demo / submission | [M4 tasks](tasks/MEMBER_4_FRONTEND_DEMO.md) | feature/m4-frontend-demo |

## Shared dependency matrix

| Task | Owner | Reviewer | Dependency | Checkpoint |
|---|---|---|---|---|
| M1-01 | Member 1 | Member 2 | none; H2 contract freeze | H2 IDs and manifests to M3; H8 registered crop inputs to M1-02 |
| M1-02 | Member 1 | Member 2 | M1-01; M2-01 grid; M3-01 schema | H16 first cells M2/M3; H24 COG/time-series manifest M3 |
| M1-03 | Member 1 | Member 4 | M1-02; permitted M2-03 context | H32 QA results to M3 trace and M4 Sources |
| M1-04 | Member 1 | Member 2 | M1-02 and M1-03 gates | H36 go/no-go with M4; nothing new after H38 |
| M2-01 | Member 2 | Member 1 | M3-01 shared schema; source terms | H2 IDs to all; H12 base grid/residents/facilities inputs M3 |
| M2-02 | Member 2 | Member 1 | M2-01; M1-02 H16 cells; M2-03 services | H12 baseline to M3; H24 joined real-data summary to M3/M4 |
| M2-03 | Member 2 | Member 1 | M2-01 source terms; M3-04 scheduler | H16 callable jobs to M3; H24 alerts to M4 |
| M2-04 | Member 2 | Member 1 | M2-01 roads (M3-02/M3-03 for hand-off only) | H32 callable and revision tests to M3; seven facts to M4 |
| M2-05 | Member 1 | Member 2 | M2-01; M1-02; M2-02; M3-02 | H24 first list; H32 final callable M3/M4 |
| M2-06 | Member 2 | Member 3 | M2-02; licences; M3-02 privacy | H38 record deferred scope; later approved iteration |
| M3-01 | Member 3 | Member 4 | M1/M2 identifiers and fixtures | H2 v0.1 freeze; H12 mock API to M4 |
| M3-02 | Member 3 | Member 4 | M3-01; source safety rules | H12 role API; H24 protected data; H38 release blocker review |
| M3-03 | Member 3 | Member 2 | M3-01/02; M1-02; M2-02/03/04/05 | H24 real-data API; H32 routes/shelters/sources UI handoff |
| M3-04 | Member 3 | Member 1 | M2-03 adapters; M3-01/02 | H2 environment skeleton; H16 scheduler; H32 verified link if available; H40 backup |
| M4-01 | Member 4 | Member 3 | M3-01 H2 freeze; UI source | H2 client shapes; H12 sign-in and public preview |
| M4-02 | Member 4 | Member 1 | M4-01; M3-03; M1-02 layers | H16 map on fixtures; H24 real-data layers |
| M4-03 | Member 4 | Member 3 | M3-03; M2-02/04/05; M1-03 | H24 summary/alert; H32 route/shelter/source; H38 print |
| M4-04 | Member 4 | Member 3 | all MVP tasks; M1-03 science report; M3-02 security | H38 freeze; H40–44 video; H44–48 submission |


## RACI

R/A = one accountable implementer; C = named cross-review or domain consultation; I = notified. Team-wide gates have one accountable gate owner, with each member responsible for their own input.

| Deliverable | Member 1 | Member 2 | Member 3 | Member 4 |
|---|---|---|---|---|
| Radar cells and scientific QA | R/A | C | I | C |
| Geodata, population, alerts, route/shelter algorithms | C | R/A | C | I |
| API/schema/auth/policy/protected storage | I | C | R/A | C |
| Job scheduling, retries, CI and deployment | C | C | R/A | I |
| UI/components/typed mock fixtures | C | I | C | R/A |
| H2 contract freeze | C | C | R/A | C |
| H24 real-data integration gate | C | C | R/A | C |
| H38 full rehearsal and feature freeze | C | C | C | R/A |
| Video/submission/citation assembly | C | C | C | R/A |

## Workload balance

14 Nov 2026 change: shelters (M2-05) moved to Member 1 after H24, routes (M2-04) start early on a synthetic graph, and Member 3 extras (CSRF, audit log, job leases, CI, metrics, rollback) moved to stretch. Before that change: M2 core tasks total about 28 active hours plus at most one hour backlog design. This is still the bottleneck. Start tiny bounded data and route/shelter fixtures early; no global watch list, movement pipeline or broad environmental datasets in core. M3 owns scheduler/leases/retries/loaders; M4 owns UI contract fixtures and screen state handling. M1 reviews M2 CRS, capacity and population joins. Support is explicit review/integration work; M2 retains algorithm accountability. M1 ~25 core active hours plus ≤4 optional; M3 ~29; M4 ~30. Remaining elapsed time is downloads, review, breaks, integration and contingency, not an assumption of 48 uninterrupted working hours.

## Team conventions

Freeze H3 IDs, row fields, units/CRS, dataset manifests, evidence enums, file naming and eight essential JSON contracts at H2. A later change starts with an API/schema PR and receiving-member acknowledgement. Use source/run IDs in filenames; UTC internal time; source precision retained; snake_case JSON fields; no bare scalar estimates; no secret fixtures. Small PRs at H2/H8/H16/H24/H32 rather than one giant member branch at H48. Every PR has one reviewer, source trace, tests, known limits and whether data is synthetic.

Contacts remain placeholders: Member 1 [name/contact pending], Member 2 [pending], Member 3 [pending], Member 4 [pending]. Handoffs fail if the receiver cannot reproduce the artifact or the manifest omits evidence, dates, units, sensitivity or schema version.
