# Team Lead full-stack execution backlog

Owner: **A, Rashiru** on `feature/lead-fullstack-app`. This is an executable backlog, not a claim that all tasks are done. Source authority: [product](PROJECT_PLAN.md), [UI](UI_DESIGN.md), [API](contracts/openapi.yaml), [security](07_SECURITY_PRIVACY_AND_RBAC.md), [frontend plan](06_FRONTEND_DESIGN_AND_SCREEN_PLAN.md), and [three-member allocation](18_THREE_MEMBER_EXECUTION_PLAN.md). The linked Claude design artifact remains inaccessible; exact visual tokens remain VERIFY. Preserve React/TypeScript/Vite/MapLibre and the FastAPI modular monolith.

## Scaffold assessment and order

The React shell, sign-in form, blank MapLibre canvas, static screen placeholders, typed fixture imports, FastAPI route registration, in-memory demo sessions, role checks, initial SQLAlchemy models and Alembic command setup exist. The API client currently implements session/status only. `GET /areas/{area_id}/summary` and `GET /sources/{source_id}` return 501; the UI reads local fixture JSON. No real NISAR layer, DB-backed domain data, reviewed migration, live source, operational route or validated model exists. PostGIS/Docker were unavailable in the last scaffold check. Fix the first vertical slice, then P0 NISAR controls and verified artifact ingestion; treat P1 screens as conditional. Never mark a draft route implemented merely because it is registered.

Each task row records priority, accountable owner, source, location, dependency, outcome, acceptance, verification and current status. `SCAFFOLDED` means a partial foundation exists; `PLANNED` means no task implementation yet. No row is complete solely because a fixture renders.

### Backend and security

| ID | Pri | Owner | Source | Exact location | Depends | Expected outcome | Acceptance criteria | Verification | Status |
|---|---|---|---|---|---|---|---|---|---|
| TL-B01 | P0 | A | 05; M3-01 | `backend/app/api/v1.py`, `docs/contracts/openapi.yaml` | H2 B/C schema | 40-operation inventory with explicit real/501 state | Paths/roles match draft; unknown operation stays 501; no fabricated success | `python -m scripts.validate_scaffold`; API tests | SCAFFOLDED |
| TL-B02 | P0 | A | 07; M3-02 | `backend/app/core/security.py`, `backend/app/core/permissions.py`, `backend/tests/` | TL-B01 | Server session, role, scope and object policy | Anonymous/analyst denial; no client role header; logout revokes; no private files or tiles bypass | `python -m pytest backend/tests` | SCAFFOLDED |
| TL-B03 | P0 | A | 05; M3-01 | `backend/app/db/models.py`, `backend/migrations/`, `scripts/initialize_database.py` | PostGIS availability | Reviewed first revision and persistence path | Migration runs on fresh PostGIS and rollback/backup plan reviewed; no SQLite substitute claimed | `python -m alembic -c backend/alembic.ini upgrade head`; DB test | PLANNED; CLI only |
| TL-B04 | P0 | A | 05/07; M3-03 | `backend/app/api/v1.py`, `backend/app/services/` | TL-B02; canonical fixtures | Role-scoped synthetic area summary and source record | Valid fixture schema; scoped area returns 200, wrong scope 403, invalid ID 404; no private public payload | `python -m pytest backend/tests` | PLANNED |
| TL-B05 | P0 | A | 04/05; M3-01/03 | `backend/app/services/`, `worker/interfaces.py` | B/C versioned manifest | Precomputed ML artifact ingestion boundary | Validate schema, checksum, CRS, dates/version, evidence and safety before atomic publish; HTTP never loads raw scenes | integration test with synthetic artifact | PLANNED |
| TL-B06 | P0 | A | 05/07; M3-03 | `backend/app/api/`, `backend/app/core/` | TL-B02/B05 | Layer, tile and source trace service | Policy before private file read, 72-hour gate and r8 suppression; no direct storage URL | RBAC/file/Range/delay tests | PLANNED |
| TL-B07 | P1 | A | 05; M3-03 | `backend/app/api/`, `backend/app/services/` | validated B/C outputs | Alerts, facilities, services and brief responses | Each number has source/date/evidence; missing value null/Unknown; role-filtered brief | API schema and safety tests | PLANNED |
| TL-B08 | P1 gated | A | 07; M2-04/05 | `backend/app/api/`, `backend/app/services/` | privacy approval, private graph/site review | Fictional route and shelter demonstration only | Officer/coordinator denial matrix; no real origin/site or external routing; field-check warning | security and negative egress tests | DEFERRED |

### Frontend and demo

| ID | Pri | Owner | Source | Exact location | Depends | Expected outcome | Acceptance criteria | Verification | Status |
|---|---|---|---|---|---|---|---|---|---|
| TL-F01 | P0 | A | UI §6; M4-01 | `frontend/src/app/App.tsx`, `frontend/src/services/api.ts` | TL-B02 | Restored session and logged-out view | No private fetch before auth; role downgrade/logout clears private state; keyboard sign-in and error state | `npm --prefix frontend run test` | SCAFFOLDED |
| TL-F02 | P0 | A | UI §§3-5; M4-02 | `frontend/src/components/MapPanel.tsx`, `frontend/src/app/App.tsx` | TL-B04 | Interactive map-to-area selection | Selectable synthetic area is explicitly non-geographic; loading/error/unknown states and equivalent keyboard control | component smoke and browser check | PLANNED |
| TL-F03 | P0 | A | UI §§2-4; M4-03 | `frontend/src/services/api.ts`, `frontend/src/types/contracts.ts`, `frontend/src/app/App.tsx` | TL-B04/F02 | Typed API-fed area and source panel | Real HTTP response, evidence label, range/source/date, synthetic badge, invalid-ID error | frontend/API contract tests | PLANNED |
| TL-F04 | P0 | A | UI §3.1; M4-02 | `frontend/src/components/`, `frontend/src/app/App.tsx` | B/C approved pass manifest and QA | NISAR before/after/change and HH/HV controls | Actual pass dates and version labels; missing gap explicit; unverified controls disabled; GIBS context separated | UI tests and manual map QA | PLANNED |
| TL-F05 | P0 | A | UI §3.1; M4-03 | `frontend/src/app/App.tsx`, `frontend/src/components/Evidence.tsx` | TL-B05/F04 | Sources, uncertainty and trace view | Source/date/licence/version and measured QA shown only when present; Unknown otherwise | component and contract tests | SCAFFOLDED |
| TL-F06 | P1 | A | UI §§3-5; M4-03/04 | `frontend/src/app/App.tsx`, `frontend/src/styles.css` | P0 green, TL-B07 | Alert/brief and responsive field views | Fire wording, printed citations, 360/390px access and 200% zoom | build, tests, manual accessibility/print review | PLANNED |

### Integration, DevOps and release

| ID | Pri | Owner | Source | Exact location | Depends | Expected outcome | Acceptance criteria | Verification | Status |
|---|---|---|---|---|---|---|---|---|---|
| TL-I01 | P0 | A | 21; M3-01 | `docs/contracts/`, `frontend/src/types/`, `backend/app/api/` | B/C acknowledgement | One versioned handoff schema | No competing field names; H3 strings, UTC/CRS, null/Unknown and fixture/real distinction | planning and contract validators | PLANNED |
| TL-I02 | P0 | A | 10; M3-04/M4-04 | `tests/`, `backend/tests/`, `frontend/src/**/*.test.tsx` | TL-B04/F03 | Map→API→summary/source test | Authenticated flow passes; wrong role/scope denied; no Docker required for synthetic path | pytest, Vitest, lint, build | PLANNED |
| TL-I03 | P0 | A | 11/13; M3-04/M4-04 | `.github/workflows/ci.yml`, `docker-compose.yml`, `README.md` | TL-I02 | Reproducible local/demo run | CI green; PostGIS test only when available; backup video and no secret/large data | CI plus local commands | SCAFFOLDED |
| TL-I04 | P0 | A | 07/10/13; M4-04 | `docs/22_DEMO_AND_ACCEPTANCE_CHECKLIST.md` | all P0 gates | Release decision and submission packet | No unverified science or sensitive locations; citations, recorded fallback and reviewer sign-off | checklist + rehearsal | PLANNED |

## API implementation order

The canonical [40-operation inventory](contracts/README.md) remains unchanged. First: `POST/GET/DELETE /session`, `/roles`, `/health`, `/status`, `/public/map` (foundation); then `GET /areas/{area_id}/summary`, `/sources`, `/sources/{source_id}`, `/areas/{area_id}/values` and `/values/{value_id}/trace` for the first slice. Next, once B/C artifacts pass QA: `/layers`, `/layers/{layer_id}`, `/layers/{layer_id}/timeseries`, guarded tiles/files, `/areas/{area_id}/damage` and `/areas/{area_id}/validation`. Remaining alert, people/service/facility, brief, route, shelter and admin operations remain explicit 501 until their domain code and policy tests pass. No new endpoint schema replaces `docs/contracts/openapi.yaml`.

## Definition of Done and blockers

A task is done only when its code runs, fixture or real lineage is explicit, response examples validate, authorization is enforced on the server, negative cases pass, UI handles loading/error/unknown, and a different member reviews the change. A's browser may format values but may not derive humanitarian estimates. The current local demo session store is in memory; production identity lifecycle, independent security review and private storage remain open. Docker/PostGIS, data licences, Earthdata access, BETA/PROVISIONAL calibration, matching validation data, external design access and challenge duration remain unresolved. A failed scientific gate disables the real analytical layer, not the synthetic fallback.
