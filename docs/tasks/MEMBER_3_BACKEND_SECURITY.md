# Member 3 work package

[Team allocation](../08_FOUR_MEMBER_TASK_ALLOCATION.md) · [Roadmap](../09_48_HOUR_DEVELOPMENT_ROADMAP.md) · [Contracts](../contracts/README.md)

Status: planned implementation, not completed work. File paths below are proposed outputs, not present application code. Effort means active work within the given window; allow breaks and integration buffer. All implementation details beyond cited source are ARCHITECT RECOMMENDATION.

## M3-01: Contract freeze, database and loaders

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md Agree at hour2/§3.1; UI_DESIGN.md §2.1 |
| Scope | Review OpenAPI, implement PostGIS migrations/schema and transactional manifest loaders; mock endpoints. |
| Priority / phase | MVP |
| Accountable owner | Member 3 |
| One reviewer | Member 4 |
| Dependency | M1/M2 identifiers and fixtures |
| Expected files / outputs | backend/app/schemas/; backend/migrations/; backend/app/loaders.py; backend/app/main.py |
| Required stub / mock | use docs/contracts JSON; M4 packages mock client fixtures |
| Effort and hackathon window | H0–H12; 7 active h |
| Input / output contract | manifest + canonical row → validated DB + versioned API |
| Local verification (planned) | `python -m pytest tests/api/test_contracts.py tests/geo/test_database.py` |
| Test cases | T-CONTRACT, T-SQL: FK/check/CRS/idempotency/atomic rollback |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 4 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H2 v0.1 freeze; H12 mock API to M4 |
| Blockers / fallback | Schema mismatch; contract PR first; do not silently coerce fields |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M3-02: Authentication, policy and protected storage

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md §3.3; PROJECT_PLAN.md §10; UI_DESIGN.md §6; PDF p2 §4 |
| Scope | Sessions/CSRF, RBAC+area/object tags, release gate, public sanitization, protected tiles/files/export, redacted audit. |
| Priority / phase | MVP invariant |
| Accountable owner | Member 3 |
| One reviewer | Member 4 |
| Dependency | M3-01; source safety rules |
| Expected files / outputs | backend/app/auth/; backend/app/policy/; backend/app/api/layers.py; tests/security/ |
| Required stub / mock | five demo roles and out-of-scope user, synthetic secrets only at runtime |
| Effort and hackathon window | H2–H16 plus H32–H38 audit; 8 active h |
| Input / output contract | session + resource + time → allow/filter/deny |
| Local verification (planned) | `python -m pytest tests/security` |
| Test cases | T-RBAC, T-LAYER, T-DELAY, T-CACHE, T-SAFETY: 401/403, Range, alternate path, logout and clock boundary |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 4 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H12 role API; H24 protected data; H38 release blocker review |
| Blockers / fallback | Auth/file bypass → no external demo link; localhost synthetic only |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M3-03: Domain API and evidence/brief integration

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md §§3.2/3.4; PROJECT_PLAN.md §8.1 |
| Scope | All area/alerts/routes/shelters/trace/brief endpoints with bounded queries, evidence, errors and same export filters. |
| Priority / phase | MVP |
| Accountable owner | Member 3 |
| One reviewer | Member 2 |
| Dependency | M3-01/02; M1-02; M2-02/03/04/05 |
| Expected files / outputs | backend/app/api/{areas,alerts,routes,shelters,sources,briefs}.py; backend/app/services/ |
| Required stub / mock | essential eight JSON contracts and collection wrappers |
| Effort and hackathon window | H8–H32; 8 active h |
| Input / output contract | domain callables → role-filtered HTTP response |
| Local verification (planned) | `python -m pytest tests/api` |
| Test cases | T-CONTRACT, T-TRACE, T-BRIEF: examples, lineage, role-filtered exports, unavailable sources |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 2 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H24 real-data API; H32 routes/shelters/sources UI handoff |
| Blockers / fallback | Late domain inputs; fixtures remain explicit synthetic; do not invent server measurements |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M3-04: Orchestration, Compose, CI and recovery

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md §§3.1/3.4; PROJECT_PLAN.md §8 Orchestrator/Safety |
| Scope | One worker scheduler, retry/cached state, job leases, Docker, env template, CI, metrics and rollback; free tunnel only after checks. |
| Priority / phase | MVP; sensitive offline/LLM later |
| Accountable owner | Member 3 |
| One reviewer | Member 1 |
| Dependency | M2-03 adapters; M3-01/02 |
| Expected files / outputs | worker/main.py; infra/compose.yaml; .env.example; .github/workflows/ci.yml; scripts/{preflight,load_demo,verify_demo}.py |
| Required stub / mock | no-network adapter fixture; failure injection; synthetic demo bundle |
| Effort and hackathon window | H0–H38; 6 active h plus H40 backup |
| Input / output contract | schedule + adapter results → atomic stored snapshot/status |
| Local verification (planned) | `docker compose -f infra/compose.yaml config; python -m pytest tests/unit/test_jobs.py` |
| Test cases | T-JOBS, T-DEVOPS: retry idempotence, cached failure, restore and no secret logs |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 1 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H2 environment skeleton; H16 scheduler; H32 verified link if available; H40 backup |
| Blockers / fallback | Docker/tunnel unavailable → localhost + recorded demo; no paid service; offline/LLM remain later |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.
