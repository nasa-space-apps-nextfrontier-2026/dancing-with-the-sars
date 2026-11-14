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

In a second PowerShell at repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

The frontend serves `http://localhost:5173` and proxies `/api/v1` to `http://127.0.0.1:8000`. The authoritative **draft** of all 40 planned operations is [openapi.yaml](docs/contracts/openapi.yaml); runtime FastAPI `/docs` only shows implemented scaffold routes. Most domain operations return explicit HTTP 501 after server authorization. There are no default demo accounts. Run `.\.venv\Scripts\python.exe -m scripts.create_demo_user` from the repository root to create a local account in ignored `.env`, then restart the API. `CIVISAR_DEMO_USERS_JSON` holds password hashes and fixed roles. No role is taken from a client header. `/api/v1/health` is liveness; `/internal/ready` checks PostGIS connectivity and returns 503 until the database is available.

## Docker and database

```powershell
docker compose up --build db api frontend
docker compose --profile worker-once run --rm worker
docker compose exec api python -m scripts.initialize_database
```

The API image includes `scripts/initialize_database.py`. `docker compose up -d db` starts only the development database on loopback. A `.env` with local-only credentials is separate from Compose's illustrative defaults. Production deployment, migration history and backups are not part of this scaffold.

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

The worker returns Unknown with null numbers; it does not contact ASF, CMR or humanitarian APIs. API 501 responses mark unimplemented operations. Only the public empty preview, status, health, session foundation, source list and empty layer list currently have scaffold behavior. Database initialization requires PostGIS and has not been substituted with SQLite.

## Environment and safety

`.env.example` lists server-only optional credentials, database URL, allowed frontend origin, synthetic switch and demo users. `COOKIE_SECURE=false` is for loopback HTTP only. Do not expose this configuration to the internet. Routes, shelters, tiles, files and exports require server policy; no real operational records or raw datasets are served. The frontend is labelled illustrative, including its blank map. Printing is a synthetic placeholder and no real report is generated. The [security plan](docs/07_SECURITY_PRIVACY_AND_RBAC.md) defines further release blockers.

## Branches, ownership and next work

`main → planning/civisar-full-architecture → dev → feature/m{1,2,3,4}-...` describes local branch ancestry. The four exact names and reviewer rules are in [team allocation](docs/08_FOUR_MEMBER_TASK_ALLOCATION.md) and [CONTRIBUTING](CONTRIBUTING.md). Member 1 starts M1-01 metadata/version manifest; Member 2 M2-01 source terms/grid; Member 3 M3-01 migration and contract refinement; Member 4 M4-01 typed client and UI foundations. The scaffold report records actual validation and unresolved work: [17](docs/17_DEVELOPMENT_SCAFFOLD_REPORT.md).
