# DevOps, deployment and Git workflow

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Actual planning Git setup

Original branch `docs/architecture-plan` at `022599111ea437b62bf297851e0109f08cde94d8`. Detected remote default `origin/main` at `e99348c0aec238b4d4252f02001560f6f18d1fc7`. Working tree initially clean. Fetch succeeded after sandbox network retry. Created `planning/civisar-full-architecture` from origin/main and fast-forwarded existing architecture commits to preserve the seventh source; default/original branches were not changed. Planning upstream to origin/main was removed. Final commit/branch/status verification is reported in the completion response and git log; this document does not invent a future commit hash.

After validating and committing docs, create `dev` at the plan commit only if still absent locally/remotely. Existing dev would require a reviewed ordinary PR/merge, never reset or overwrite. No feature branches are created until implementation starts. Remote push is left pending because no prior explicit push authorization is established; local commit/branches fulfill the safe fallback in the request. Exact optional push commands are below.

Branches are planned in [17_TEAM_ASSIGNMENT_AND_BRANCHES.md](17_TEAM_ASSIGNMENT_AND_BRANCHES.md) (updated 14 Nov 2026): `main` (demo-ready, tagged) and `dev` (protected integration branch), with short-lived `feature/<task-id>-<short-name>` branches per task, `docs/<name>` for documentation and `fix/<short-name>` after the H38 freeze. Rashiru manages and merges all PRs; his own PRs are approved by Udula or Thanoban. No `dev` exists yet: create it from `main` first. Feature branches originate from `dev`; reviewed `dev` is promoted to `main` at H24, H38 and H48. Do not merge into `main` during planning.

## Commands (Windows Git is installed outside PATH)

```powershell
& 'C:\Program Files\Git\cmd\git.exe' status -sb
& 'C:\Program Files\Git\cmd\git.exe' branch -a
& 'C:\Program Files\Git\cmd\git.exe' log -5 --oneline
# Only after explicit remote-push authorization:
& 'C:\Program Files\Git\cmd\git.exe' push -u origin planning/civisar-full-architecture
& 'C:\Program Files\Git\cmd\git.exe' push -u origin dev
# At implementation start, with clean working tree:
& 'C:\Program Files\Git\cmd\git.exe' switch dev
& 'C:\Program Files\Git\cmd\git.exe' switch -c feature/m1-01-nisar-download
```

Everyone uses `feature/<task-id>-<short-name>` branches. macOS/Linux use `git` with the same arguments. If branch already exists, inspect/check it out without recreating. Dirty tree: preserve work; use a scoped commit by owner or isolated worktree after inspection, never destructive cleaning. On conflicts, review both sides with owners, resolve intentionally and rerun contracts/tests; use merge abort if resolution is uncertain, never force-push shared branches. No reset --hard, clean -fd, force push or branch deletion.

## PR/protection/release recommendations

ARCHITECT RECOMMENDATION: protect main/dev against direct pushes and force pushes; require one non-author review, successful CI, resolved comments and up-to-date merge checks. No protection was configured remotely here. Rashiru merges all PRs; Udula and Thanoban review each other's ML and approve Rashiru's PRs; any auth/layer/retention change is also reviewed by Rashiru. Small PRs include source/task IDs, input/output contract, actual validation, data sensitivity and rollback. Avoid mixing code/large binaries with documentation PRs.

CI proposed gates: source/reference integrity; Markdown/JSON/OpenAPI; Python formatting and meaningful tests; PostGIS integration; frontend typecheck/build/components; role/file/privacy tests; E2E and secret/dependency checks. Fork CI has no production credentials. Pin dependencies/containers with a documented update process after verification. Release candidate `v0.1.0-demo-rc1`, final `v0.1.0-demo` only after H48 review; tags not created in planning. Record full commit and approved dataset/run manifest in release notes.

## Local runtime and hosting

Planned Compose services: db (PostGIS), api, worker, web/proxy. Worker imports shared Python pipeline modules; no queue broker needed for single-host demo. Ignore `.env`, raw/cropped sensitive data, local DB volumes, recordings and private reports in future `.gitignore`; planning does not edit the existing root README or source references.

Environment template keys (blank values, no secrets): DATABASE_URL, SESSION_SECRET, EARTHDATA_TOKEN, FIRMS_MAP_KEY, ACLED_TOKEN, IOM_DTM_KEY, ALLOWED_ORIGIN, DATA_ROOT, DEMO_SYNTHETIC, COOKIE_SECURE. API keys never use VITE_ prefix. M3 creates `.env.example` and `.gitignore` in implementation, with local least-privilege passwords generated outside Git.

Free-only: laptop Compose first, optional Cloudflare Tunnel after free-tier/account/HTTPS and exposure checks. Tunnel is not a substitute for session authorization. No tunnel/deployment tested or created here. If verification fails, use localhost demonstration and recorded video. Cross-platform onboarding is in [15](15_TEAM_ONBOARDING.md); Windows WSL2/Linux containers and macOS/Linux Docker differences must be tested by team.

## Operations, observability and rollback

Health: API responds sanitized status, DB check private, source freshness/last-success surfaced without credentials. Metrics: job duration/failures, queue age, data age, invalidated routes, denied requests, disk/RAM. Logs use request/run IDs, never precise route endpoints, shelter coordinates, user secrets or raw source responses.

Back up a sanitized demo DB dump plus checksummed approved artifacts/config version to second laptop; exclude real secrets. Restore rehearsal at H40 loads previous schema-compatible snapshot and changes approved run pointers atomically. Application rollback uses reviewed previous image/commit; DB migration rollback must be tested or restore snapshot rather than destructive ad hoc SQL. Keep a recorded demo if network/source APIs fail. Sensitive real-data retention requires approved policy before any production use.
