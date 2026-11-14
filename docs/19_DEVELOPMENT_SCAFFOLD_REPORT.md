# Development scaffold verification and handoff

14 November 2026. This report describes the local scaffold on `dev`; it does not certify any operational or scientific result. The 40 planning artifacts, 957 trace rows, eight synthetic examples, seven original references, 18 task assignments, and the canonical draft contract remain authoritative. The planning commit was already present as `39dbba3`; `dev` was created from the fast-forwarded planning branch. Temporary render assets and installed validation packages accidentally included in that earlier commit are removed by the scaffold commit, without rewriting history.

## Actual project structure

```text
docs/                  existing blueprint, ADRs, contracts, tasks, this report
frontend/              React, TypeScript, Vite, MapLibre shell and tests
backend/               FastAPI, role/session policy, PostGIS models and tests
worker/                deterministic radar, geodata and alert boundaries
shared/                pointers to canonical contracts and fixtures
infrastructure/docker/ local images; database runs through Compose
scripts/               setup, validation and development commands
tests/                 cross-package contract and safety checks
.github/workflows/      credential-free pull-request checks
```

Only approved local development boundaries are present. No NASA download, model training, live monitoring, real routing, shelter publication, deployment, or remote push occurred. The linked Claude visual mockup was unavailable in the planning phase; the UI follows `UI_DESIGN.md`, with an illustrative blank map.

## Component traceability

Statuses describe the scaffold itself. `TESTED` means a narrow local test passed, not that the full requirement is complete. All real-data and operational acceptance criteria remain open.

| Source requirement | Component and owner | Location | Status | Test reference | Dependency and remaining work |
|---|---|---|---|---|---|
| 06, 07; M4-01 | Public-safe shell, Rashiru | `frontend/src/app`, `frontend/src/components` | TESTED | `frontend/src/app/App.test.tsx` | Complete accessible screen states, session restoration and visual QA |
| 05; M4-01 | Typed API client, Rashiru | `frontend/src/services`, `frontend/src/types` | TESTED | `frontend/src/services/api.test.ts` | Connect approved server response schema and pagination |
| 06; M4-02/03 | Map and domain views, Rashiru | `frontend/src/app`, `frontend/src/components/MapPanel.tsx` | SCAFFOLDED | App smoke test | Approved layers, accessible detail flows and responsive verification |
| 05, 07; M3-01/02 | API, errors, roles and sessions, Rashiru | `backend/app/api`, `backend/app/core` | TESTED | `backend/tests/test_api.py` | Persistence, scope policy, audit review, endpoint implementation |
| 05; M3-01 | Initial PostGIS models and DB setup, Rashiru | `backend/app/db`, `backend/migrations`, `scripts/initialize_database.py` | SCAFFOLDED | import, readiness and Alembic `heads` checks | Local PostGIS; reviewed first Alembic revision; DB initialization not run here |
| 05; M3-03 | 40 draft route inventory, Rashiru | `backend/app/api/v1.py` | TESTED | `scripts/validate_scaffold.py` | Most protected operations deliberately return 501; add validated responses |
| 04; M1-01/02/03 | Radar interfaces, Udula | `worker/radar`, `worker/pipelines` | SCAFFOLDED | `worker/tests` | Source/version manifest, licensed scenes, scientific QA and processing |
| 03, 04; M2-01/02/03 | Geodata and alerts, Rashiru | `worker/geodata`, `worker/alerts` | SCAFFOLDED | `worker/tests` | Source terms, H3 grid, joins, thresholds and provenance |
| 07; M2-04/05 | Route and shelter safety boundary, Rashiru | `backend/app/core/permissions.py`, `worker/geodata` | TESTED | API denial tests | Private graph, evidence and coordinator review; real routes disabled |
| 02; M3-04 | Twelve deterministic logical-agent interfaces, Rashiru | `backend/app/agents` | TESTED | `scripts/validate_scaffold.py` | Wire approved computed values and trace records |
| 11; M3-04 | Local containers and CI, Rashiru | `docker-compose.yml`, `infrastructure/docker`, `.github/workflows` | SCAFFOLDED | YAML parse, local checks | Docker unavailable on this machine; CI awaits first PR run |
| 10, 11; all owners | Contract and obvious-secret guards | `docs/contracts`, `scripts/validate_scaffold.py`, `scripts/check_secrets.py` | TESTED | validators, pytest, scanner | Add DB-backed integration and dedicated secret scanner before deployment |

## All 18 member tasks

Updated 14 Nov 2026 to the team's decision (see [17](17_TEAM_ASSIGNMENT_AND_BRANCHES.md) and [08](08_FOUR_MEMBER_TASK_ALLOCATION.md)). The team works on `dev` through short-lived `feature/<task-id>-<short-name>` branches. Statuses mean a team member can start the task; they do not mark it complete.

| Person | Tasks enabled by scaffold | First work and handoff |
|---|---|---|
| Udula (Member 1) | M1-01, M1-02, M1-03: SCAFFOLDED | Start M1-01 scene/version manifest and downloads; model code goes in `worker/radar/`. Hand the damage table to Thanoban and Rashiru. |
| Thanoban (Member 2) | M1-04, M2-06: SCAFFOLDED / DEFERRED | Night-light and fire models in `worker/services/`, strike tests in `worker/evaluation/`; trained on free Google Colab ([18](18_THANOBAN_ML_PLAN_AND_COLAB.md)). Hand callable functions to Rashiru. |
| Rashiru (Member 3) | M2-01 to M2-05, M3-01 to M3-04, M4-01 to M4-04: SCAFFOLDED | All frontend, backend, data, alerts, routes, shelters, hosting and PR merges. Start with M3-01 Alembic revision and M4-01 typed responses. |
| Chames (Member 4) | none | Not working on the project. |

## Validation and limitations

| Check | Result |
|---|---|
| Planning validator | PASS: 40 planning files, 957 trace rows, 40 operations, synthetic examples |
| Scaffold inventory and obvious-secret scan | PASS: 40 registered operations, 12 interfaces, synthetic fixtures; no obvious credential pattern |
| Python lint and tests | PASS: Ruff; 7 tests. One Starlette/httpx deprecation warning |
| Alembic command setup | PASS: `alembic heads` and offline `upgrade --sql head` load the configuration/environment; no revision exists or was applied yet |
| Backend process smoke check | PASS: Uvicorn started and `/api/v1/health` returned 200 |
| Frontend lint, tests, TypeScript and build | PASS: 2 tests and production build. Vite warns that the initial MapLibre bundle exceeds 500 kB |
| npm production dependency audit | PASS: zero reported vulnerabilities with `--omit=dev` |
| npm full development dependency audit | PARTIAL: 7 moderate advisories remain in tooling; the 2 critical Vitest/tinypool advisories were removed by upgrading Vitest |
| Database, Docker images and Compose runtime | BLOCKED locally: Docker CLI/daemon unavailable. Readiness returns 503 without PostGIS; initialization was not falsely reported as run |
| Scientific QA and real-data integration | DEFERRED by scope: no licensed scenes, live sources, field verification or model outputs |

The initial schema is bootstrapped with `create_all`, while Alembic configuration is ready for reviewed revisions; Member 3 must author and test the first revision. Sessions are in memory and local demo users come from ignored `.env`; this is a local foundation only. The runtime FastAPI OpenAPI page excludes the 501 draft handlers; `docs/contracts/openapi.yaml` remains the canonical draft and route coverage is checked separately. CI has not run on GitHub yet. The obvious-secret guard catches common key patterns and secret files but is not comprehensive.

Security defaults deny unauthenticated restricted routes, guard tiles/files/exports via the same server policy, avoid client-supplied roles, and return unknown/unavailable rather than fabricated data. Private location release, audited data access, operational routing and deployment require the approvals and tests in [07](07_SECURITY_PRIVACY_AND_RBAC.md) and [10](10_TESTING_AND_ACCEPTANCE_PLAN.md). The proposed dataset catalogue and unresolved integration choices remain unresolved; this scaffold does not activate them.
