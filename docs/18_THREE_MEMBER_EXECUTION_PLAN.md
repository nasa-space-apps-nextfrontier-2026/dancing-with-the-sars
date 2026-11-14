# Three-member execution plan

Status: active Phase 3 ownership plan, 14 November 2026. Challenge duration is **unconfirmed**. The [four-member allocation](08_FOUR_MEMBER_TASK_ALLOCATION.md) and [former assignment](17_TEAM_ASSIGNMENT_AND_BRANCHES.md) remain historical records; this page governs new work. It does not approve the proposed ADRs, a 15-source rollout, operational routing, or any scientific result.

## People, branches and boundaries

| Active member | Accountable work | Branch | First handoff |
|---|---|---|---|
| A: Rashiru, Team Lead | React/MapLibre, FastAPI/PostGIS, policy, ingestion, CI, integration, PRs, demo and submission | `feature/lead-fullstack-app` | Typed synthetic area and source API, then map-to-summary slice |
| B: Udula, ML engineer 1 | ASF/Earthdata discovery; NISAR 151D/72 scene/version manifest, GCOV crop/registration, HH/HV features, change imagery and radar QA | `feature/m1-radar-damage` | Metadata-only manifest with acquisition/version/CRS/coverage and missing-pass list |
| C: Thanoban, ML engineer 2 | Shared feature/output schema, H3 and ancillary features, Isolation Forest/fallback, candidate classes, independent evaluation, evidence and damage export | `feature/m2-geodata-alerts` | Synthetic contract-compatible scored cells, test and QA specification |

A owns HTTP responses and display, never radar science. B owns radar acquisition and preprocessing, not the scoring model. C owns scoring and science evaluation, not raw radar downloads or application auth. B and C jointly review the handoff schema but edit separate files. A is accountable for a single full-stack branch while retaining separate `frontend/` and `backend/` modules. Reviewers are C for B, B for C, and one of B/C for A's contract and integration PR; security review requires a competent independent reviewer before external exposure.

## Disposition of every inherited task

Task IDs identify the original work package, not a still-active four-person assignment. P0 means the core demonstration, P1 means only after the P0 gate, and deferred means outside the short sprint. Source details and acceptance criteria remain in `docs/tasks/` and [the trace matrix](14_REQUIREMENTS_TRACEABILITY_MATRIX.md).

| Original task | Current accountable owner | Priority and disposition | Handoff or remaining scope |
|---|---|---|---|
| M1-01 scene/version preflight | B | P0 active | Manifest to C/A; metadata and licence check before download |
| M1-02 radar transforms and model | B | P0 active for radar features; model subwork delegated to C | B sends aligned HH/HV features and change-artifact manifest; C scores |
| M1-03 scientific QA | C | P0 active | C owns spatial hold-out/model report; B supplies registration/version QA and image review |
| M1-04 night-light/fire models and evidence tests | C | P1 conditional | Small ancillary signals and strike enrichment only after core candidate model works |
| M2-01 grid/source baseline | C | P0 active for H3/ancillary feature preparation | C sends stable IDs, CRS and source manifest; A owns DB ingestion |
| M2-02 people/facilities/services | A | P1 conditional | No population or operating-status claims without permitted, dated inputs |
| M2-03 alerts | A | P1 conditional | A owns API/worker integration; C owns any model-produced signal |
| M2-04 private routing | Deferred | Excluded from 24h; 48h P1 only after safety gate | A would own a fictional private demonstration; no operational navigation |
| M2-05 shelter candidates | Deferred | Excluded from 24h; 48h P1 only after safety gate | A would own restricted fictional candidates; no real site release |
| M2-06 movement/global watch list | Deferred | Post-hackathon | No individual movement or automatic global scanning |
| M3-01 schema, DB, loaders | A | P0 active | Contract v0.1 and validated synthetic ingestion; first reviewed migration remains open |
| M3-02 auth, policy, private storage | A | P0 active | Server role/scope/object checks; demo sessions are local only |
| M3-03 domain API/evidence | A | P0 area/source/layer subset; P1 other operations | Maintain all 40 draft paths; return explicit 501 for unfinished work |
| M3-04 worker/DevOps | A | P0 local reproducibility; external hosting deferred | CI and offline/synthetic fallback before demo |
| M4-01 app, auth, typed client | A | P0 active | Session restoration, synthetic labels, request states |
| M4-02 map and NISAR controls | A | P0 active | Real imagery only after B/C QA; honest empty acquisition controls meanwhile |
| M4-03 decision screens | A | P0 area summary/Sources; P1 alerts/brief/routes/shelters | Do not let a rendered placeholder count as implemented |
| M4-04 responsive QA and submission | A | P0 demo/release coordination; P1 polish | Record fallback and cite actual source/QA state |

## Critical path and gates

1. **Contract gate:** A/B/C agree on H3 r9 computation, r8 publication, UTC dates, CRS, provenance, null/Unknown, versioned artifact names, and canonical JSON before real integration. The existing `docs/contracts/` files are the authority; a contract change gets its own reviewed PR.
2. **Synthetic vertical slice:** A serves a role-scoped synthetic area and source from FastAPI; frontend selects it from an interactive map and renders evidence-aware data. This must pass without Docker or Earthdata credentials.
3. **Real NISAR gate:** B supplies actual 151D/72 acquisition/version and calibration QA; C supplies model tests and limitations. Failed or absent QA keeps the real layer disabled and the synthetic label visible. GIBS is context, not analytical proof.
4. **Release gate:** A verifies role denial, source dates, scientific wording, privacy filtering and reproducible fallback. No direct `main` change, deployment or public sensitive link follows from this plan.

Three-person load makes A the bottleneck. Scope is reduced at the gate, not by weakening auth or scientific QA. A prioritizes P0 map/area/source integration; P1 alerts and printable view follow only if tests remain green. Routes, shelters, global monitoring, movement and extra radar tracks cannot block the core story. Both [24h and 48h schedules](20_24H_AND_48H_HACKATHON_ROADMAP.md) reserve time for breaks, review, video and submission; neither duration is asserted as official.
