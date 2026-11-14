# CIVISAR development scaffold

CIVISAR is a NASA Space Apps 2026 “Dancing with the SARs” humanitarian decision-support concept. This repository currently provides a **synthetic development scaffold**. It contains no processed radar, current civilian assessment, live routing or validated shelter result. Read the [source-grounded blueprint](docs/README.md) and [scope](docs/01_REQUIREMENTS_AND_SCOPE.md) before implementing domain features.

## Architecture and directories

`frontend/` is React/TypeScript/Vite/MapLibre and explicit synthetic screens. `backend/` is the FastAPI modular monolith with session/role policy, draft contract route registration and initial SQLAlchemy/PostGIS schema. `worker/` contains no-network typed radar/geodata/alert interfaces and deterministic Unknown outputs. `docs/contracts/` is the only canonical contract and fixture source; `shared/` explains its use. `infrastructure/docker/` holds local container builds. `scripts/` runs DB and scaffold checks; `tests/` checks integration contracts. `.github/` runs credential-free CI. No empty presentation-only package trees were created.

## Prerequisites and Windows PowerShell

Install Git, Python 3.12, Node 24 with npm and optionally Docker Desktop/Compose. Current scaffold Python commands run from the repository root. On this machine Git is at `C:\Program Files\Git\cmd\git.exe`; add it to PATH or invoke it explicitly. Create an ignored environment file with `Copy-Item .env.example .env` only for local use. No NASA account or key is required for synthetic mode.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
cd frontend
npm ci
npm run dev
```

Once frontend dependencies are installed, you can also start the frontend directly from the repository root with `npm.cmd run dev`. The root script forwards to the Vite application in `frontend/`.

In a second PowerShell at repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

The frontend serves `http://localhost:5173` and proxies `/api/v1` to `http://127.0.0.1:8000`. The authoritative **draft** of all 40 planned operations is [openapi.yaml](docs/contracts/openapi.yaml); runtime FastAPI `/docs` only shows implemented scaffold routes. Most domain operations return explicit HTTP 501 after server authorization. There are no default demo accounts. Run `.\.venv\Scripts\python.exe -m scripts.create_demo_user` from the repository root to create a local account in ignored `.env`, then restart the API. `CIVISAR_DEMO_USERS_JSON` holds password hashes and fixed roles. No role is taken from a client header. `/api/v1/health` is liveness; `/internal/ready` checks PostGIS connectivity and returns 503 until the database is available.

**Phase 4 synthetic full-stack slice:** create an analyst demo account with the command above and sign in. The app restores the server session after reload, keeps protected views hidden during session checks, and signs out with a CSRF-protected request. The main map has an explicitly non-georeferenced synthetic radar grid with before/after/change/swipe, HH/HV/HH-HV, opacity and endpoint controls. It does not contain NISAR imagery. Select **Select synthetic demo area** to request a role-scoped summary and source record showing Unknown evidence and provenance. The route works without PostGIS or NASA credentials; setting `DEMO_SYNTHETIC=false` disables the synthetic adapter. See the [Phase 4 report](docs/24_PHASE4_FULLSTACK_IMPLEMENTATION_REPORT.md) and [artifact handoff](docs/25_RADAR_ARTIFACT_HANDOFF.md).

## Docker and database

```powershell
docker compose up --build db api frontend
docker compose --profile worker-once run --rm worker
docker compose exec api python -m scripts.initialize_database
```

The API image includes `scripts/initialize_database.py`. `docker compose up -d db` starts only the development database on loopback. A `.env` with local-only credentials is separate from Compose's illustrative defaults. Production deployment and backups are not part of this scaffold.

For a new empty local PostGIS database, run `.\.venv\Scripts\python.exe -m scripts.initialize_database` from the repository root after reviewing the target and [migration notes](backend/migrations/README.md). This applies the initial Alembic revision. Do not use it against an older database created by `Base.metadata.create_all` without a separate baseline review. This revision has only been checked offline until a live PostGIS service is available.

## Worker and tests

```powershell
.\.venv\Scripts\python.exe -m worker.main --once
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe docs/contracts/validate_planning.py
.\.venv\Scripts\python.exe -m scripts.validate_scaffold
.\.venv\Scripts\python.exe -m ruff check backend worker tests scripts
cd frontend
npm run lint
npm run test
npm run build
```

The worker returns Unknown with null numbers; it does not contact ASF, CMR or humanitarian APIs. API 501 responses mark unimplemented operations. Public empty preview, status, health, session foundation, synthetic source records, the scoped synthetic area summary and empty layer list have scaffold behavior. Database initialization requires PostGIS and has not been substituted with SQLite.

## Environment and safety

`.env.example` lists server-only optional credentials, database URL, allowed frontend origin, synthetic switch and demo users. `COOKIE_SECURE=false` is for loopback HTTP only. Do not expose this configuration to the internet. Routes, shelters, tiles, files and exports require server policy; no real operational records or raw datasets are served. The frontend is labelled illustrative, including its blank map. Printing is a synthetic placeholder and no real report is generated. The [security plan](docs/07_SECURITY_PRIVACY_AND_RBAC.md) defines further release blockers.

## Branches, ownership and next work

The active three-member model is [documented here](docs/18_THREE_MEMBER_EXECUTION_PLAN.md): A (Rashiru) owns the combined `feature/lead-fullstack-app` frontend/backend branch and integration; B (Udula) owns `feature/m1-radar-damage`; C (Thanoban) owns `feature/m2-geodata-alerts`. `dev` remains the integration branch and `main` is protected. The older four-member [allocation](docs/08_FOUR_MEMBER_TASK_ALLOCATION.md) and [scaffold report](docs/17_DEVELOPMENT_SCAFFOLD_REPORT.md) are historical planning evidence. The [Team Lead backlog](docs/19_TEAM_LEAD_FULLSTACK_PLAN.md), [24h/48h scenarios](docs/20_24H_AND_48H_HACKATHON_ROADMAP.md), and [integration rules](docs/21_ML_BACKEND_FRONTEND_INTEGRATION.md) govern new work. No feature branch is merged or pushed by this local milestone.
