# Team onboarding

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Read first

Start with [scope](01_REQUIREMENTS_AND_SCOPE.md), [architecture](02_FULL_SYSTEM_ARCHITECTURE.md), your [task package](08_FOUR_MEMBER_TASK_ALLOCATION.md), [contracts](contracts/README.md) and [security](07_SECURITY_PRIVACY_AND_RBAC.md). Sources remain original and may conflict; decision status is in [source audit](00_SOURCE_AUDIT.md). Exactly four accountable members; names/contact handles pending assignment.

## Current repository versus target development setup

Current repository contains documentation and draft fixtures only. No package.json, Python project, Compose stack, API server or runnable app tests exist yet. The commands below are **target implementation instructions** for M3/M4 to make real, not completed setup or guaranteed executable commands today. Planning validation can run independently using the committed documentation validator.

Prerequisites to verify at H0: Git, Python compatible with pinned GIS wheels, Node compatible with chosen Vite version, Docker with Compose/PostGIS, adequate disk/network, GDAL and tippecanoe in reproducible containers. Pin actual versions after checking official compatibility and the team's machines; no unverified “latest” version promise. Windows: install Git on PATH or use `C:/Program Files/Git/cmd/git.exe`; use WSL2/Linux containers for GIS tools if native binaries differ. macOS/Linux: same Compose interfaces, shell path syntax adjusted. No paid infrastructure.

```text
git clone https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars.git
cd dancing-with-the-sars
git fetch origin
git switch dev
git switch -c feature/m3-backend-security
```

Remote branches must have been pushed before a fresh clone can switch to them. Until then use the local branches or an approved repository handoff; do not claim remote availability. Each member uses their feature branch from [allocation](08_FOUR_MEMBER_TASK_ALLOCATION.md). Preserve dirty work and inspect existing branch before creating.

## Planned startup after M3/M4 scaffold

1. Copy `.env.example` to ignored `.env` locally (`Copy-Item` PowerShell or `cp` POSIX); generate local credentials without committing them. Set DEMO_SYNTHETIC=true initially, server-only keys empty for no-network mode.
2. `docker compose -f infra/compose.yaml config` validates environment and ports. `docker compose -f infra/compose.yaml up --build` starts db/api/worker/web. Bind only loopback during development; confirm health before tunnel exposure.
3. `python scripts/load_demo.py --synthetic` loads small safe fixtures transactionally; `python scripts/verify_demo.py` checks contracts and role/file denial. M3 implements these entry points.
4. `python -m pytest tests/unit tests/geo tests/api tests/security`; `npm --prefix apps/web ci`; `npm --prefix apps/web run test`; `npm --prefix apps/web run build`; `npm --prefix apps/web run test:e2e`. M4 must provide package-lock and matching scripts; M3 provides Python lock/environment instructions.
5. Confirm login/role downgrade, missing passes, cached state, source trace and A4. Only then replace permitted fixtures with validated real artifacts. Do not hide a synthetic fallback behind a real-data label.

## Accounts and preflight checklist

Each member: individual Earthdata Login. M2: FIRMS MAP_KEY, ACLED permitted access, DTM key if stretch needed; inspect source licences. M3: optional Cloudflare account only if free tunnel is confirmed and security tests pass. M4: challenge Resources/rules and submission requirements. M1 checks bandwidth, disk, actual product specs/CMR and radiometric comparability. Challenge prep rules must be checked before development downloads begin. No credentials entered into PRs, chat fixtures or screenshots.

## Common integration issues

H3 numeric precision loss → strings. Metres computed in degrees → project before analysis. Different nodata conventions → manifest and validation. BETA/provisional version drift → scientific QA gate. Cadaster overlaps → fractional crosswalk not duplicate totals. Missing NRT history → archive join. Blank GIBS BETA → context fallback, not fabricated analytical pass. Browser PMTiles Range unauthorized → implement guarded range endpoint rather than public bucket. Host/container paths → DATA_ROOT mount and manifest-relative paths. Windows GIS build failure → verified container, not silent algorithm replacement.

## Handoff and support

Every handoff includes artifact/schema version, checksum, date/CRS/unit, licence/tag, tests and known gaps. Member 1 contact [pending]; Member 2 [pending]; Member 3 [pending]; Member 4 [pending]. Raise scientific uncertainty to M1, GIS/source semantics to M2, permissions/deployment to M3, UI/demo truthfulness to M4. A blocked source does not permit fake evidence. Recovery uses [DevOps rollback](11_DEVOPS_DEPLOYMENT_AND_GIT_WORKFLOW.md); no destructive Git recovery.
