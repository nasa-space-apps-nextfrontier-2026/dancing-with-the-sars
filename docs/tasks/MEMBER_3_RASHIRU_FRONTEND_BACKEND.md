# Member 3 work package: Rashiru

Rashiru: frontend (with Claude Design), most of the backend, and manager of all PRs.

[Team assignment and branches](../17_TEAM_ASSIGNMENT_AND_BRANCHES.md) · [Team allocation](../08_FOUR_MEMBER_TASK_ALLOCATION.md) · [Roadmap](../09_48_HOUR_DEVELOPMENT_ROADMAP.md) · [Contracts](../contracts/README.md)

Status: planned implementation, not completed work. Task IDs (M1 to M4) are work-package IDs; the owner field names the person (Member 1 = Udula, 2 = Thanoban, 3 = Rashiru, 4 = Chames). File paths below are proposed outputs, not present application code. Effort means active work within the given window; allow breaks and integration buffer. All implementation details beyond cited source are ARCHITECT RECOMMENDATION.

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
| Scope | MVP: sign-in sessions, roles (RBAC) with area/object tags, access checks on every endpoint and layer file, 72-hour release hold, public filtering. Stretch (after H38): CSRF hardening, redacted audit log. |
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
| Scope | All area/alerts/routes/shelters/trace/brief endpoints with bounded queries, evidence, errors and same export filters. Rashiru implements the protected endpoints (routes, shelters, closure reports, brief, trace-a-value). Chames implements the plain endpoints (layers, areas, alerts, facilities, status, sources) in a separate PR. |
| Priority / phase | MVP |
| Accountable owner | Member 3 |
| One reviewer | Member 4 |
| Dependency | M3-01/02; M1-02; M2-02/03/04/05 |
| Expected files / outputs | backend/app/api/{areas,alerts,routes,shelters,sources,briefs}.py; backend/app/services/ |
| Required stub / mock | essential eight JSON contracts and collection wrappers |
| Effort and hackathon window | H8–H32; 8 active h |
| Input / output contract | domain callables → role-filtered HTTP response |
| Local verification (planned) | `python -m pytest tests/api` |
| Test cases | T-CONTRACT, T-TRACE, T-BRIEF: examples, lineage, role-filtered exports, unavailable sources |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 4 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H24 real-data API; H32 routes/shelters/sources UI handoff |
| Blockers / fallback | Late domain inputs; fixtures remain explicit synthetic; do not invent server measurements |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M4-01: App foundation, design system and mock client

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md Part4; UI_DESIGN.md §§1/4/5/6 |
| Scope | Vite React MapLibre, token variables/themes, shared evidence/range/date controls, sign-in/public view, typed fixtures. |
| Priority / phase | MVP |
| Accountable owner | Member 3 |
| One reviewer | Member 4 |
| Dependency | M3-01 H2 freeze; UI source |
| Expected files / outputs | apps/web/src/{api,mocks,components,theme}; apps/web/src/screens/SignIn.tsx; PublicPreview.tsx |
| Required stub / mock | copy reviewed contracts, synthetic badges and all error states |
| Effort and hackathon window | H0–H12; 7 active h |
| Input / output contract | OpenAPI/fixtures → accessible client shell |
| Local verification (planned) | `npm --prefix apps/web run test; npm --prefix apps/web run build` |
| Test cases | T-UI, T-CONTRACT: no secret in bundle, mock badge, accessible components |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 4 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H2 client shapes; H12 sign-in and public preview |
| Blockers / fallback | External design inaccessible → use written design, mark exact tokens VERIFY |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M4-02: Main map, timeline, feed and inspector

| Field | Commitment |
|---|---|
| Source trace | UI_DESIGN.md §§3.1/4; ARCHITECTURE.md §4.2 |
| Scope | Main map, missing passes, HH/HV, swipe/swap, folding rails, alert feed, per-agent inspector/time series; Validation tab shows "No matching assessment available" as the normal state plus the model test results. |
| Priority / phase | MVP |
| Accountable owner | Member 3 |
| One reviewer | Member 4 |
| Dependency | M4-01; M3-03; M1-02 layers |
| Expected files / outputs | apps/web/src/screens/{ScreenMainMap,ScreenInspector}.tsx; components/{TimeSlider,LayerToggle,MapLegend,AlertCard}.tsx |
| Required stub / mock | Layer/AlertDetail fixtures with missing interval and denied tile |
| Effort and hackathon window | H8–H24; 7 active h |
| Input / output contract | layer metadata + series → MapLibre presentation only |
| Local verification (planned) | `npm --prefix apps/web run test -- map timeline` |
| Test cases | T-UI, T-DISPLAY: no fabricated pass, denied source not loaded, only active legend |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 4 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H16 map on fixtures; H24 real-data layers |
| Blockers / fallback | COGs late → clearly synthetic layer; metadata never claimed as analysis |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M4-03: Decision screens, sources and print

| Field | Commitment |
|---|---|
| Source trace | UI_DESIGN.md §§2/3.1; ARCHITECTURE.md §§4.2/4.3 |
| Scope | Alert, summary, routes, shelters, Sources and A4 brief; source trace; review/field-check affordances; deny demo. |
| Priority / phase | MVP |
| Accountable owner | Member 3 |
| One reviewer | Member 4 |
| Dependency | M3-03; M2-02/04/05; M1-03 |
| Expected files / outputs | apps/web/src/screens/{ScreenAlertDetail,ScreenAreaSummary,ScreenAreaBrief,ScreenRoutes,ScreenShelters,ScreenSources}.tsx; print.css |
| Required stub / mock | all essential contract examples; role variants; no live sensitive coordinates |
| Effort and hackathon window | H16–H32; 9 active h |
| Input / output contract | authorized APIs → people-first screens + role-filtered A4 |
| Local verification (planned) | `npm --prefix apps/web run test -- screens print` |
| Test cases | T-BRIEF, T-TRACE, T-UI: seven route facts, warnings, footer sources, analyst shelter denial |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 4 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H24 summary/alert; H32 route/shelter/source; H38 print |
| Blockers / fallback | M2 workload → implement against fixtures early; never fake actual provenance |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M4-04: Responsive QA, demo and submission

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md §4.3/Timeline; UI_DESIGN.md §§1/5 |
| Scope | Phone layouts, keyboard/contrast, mock-real audit, end-to-end story, video, citations, final release checklist. The demo story, video and submission page (H38–H48) are done by Thanoban; Rashiru keeps phone layout, accessibility, QA and the release checklist. |
| Priority / phase | MVP; PWA shell stretch |
| Accountable owner | Member 3 |
| One reviewer | Member 4 |
| Dependency | all MVP tasks; M1-03 science report; M3-02 security |
| Expected files / outputs | apps/web/src/screens/ScreenMobile.tsx; tests/e2e/; docs/demo_runbook.md; submission text; video outside Git |
| Required stub / mock | offline/failure scenarios; local recorded backup |
| Effort and hackathon window | H32–H48; 7 active h plus coordinated rehearsal |
| Input / output contract | approved build + evidence → reproducible judge walkthrough |
| Local verification (planned) | `npm --prefix apps/web run test:e2e; npm --prefix apps/web run build` |
| Test cases | T-A11Y, T-E2E, T-SUBMIT: role denial, failure fallback, full trace, citations |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 4 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H38 freeze; H40–44 video; H44–48 submission |
| Blockers / fallback | No verified hosting → recorded/local demo; protected offline deferred |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.
