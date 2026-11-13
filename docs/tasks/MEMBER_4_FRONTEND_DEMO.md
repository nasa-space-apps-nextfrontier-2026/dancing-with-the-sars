# Member 4 work package

[Team allocation](../08_FOUR_MEMBER_TASK_ALLOCATION.md) · [Roadmap](../09_48_HOUR_DEVELOPMENT_ROADMAP.md) · [Contracts](../contracts/README.md)

Status: planned implementation, not completed work. File paths below are proposed outputs, not present application code. Effort means active work within the given window; allow breaks and integration buffer. All implementation details beyond cited source are ARCHITECT RECOMMENDATION.

## M4-01: App foundation, design system and mock client

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md Part4; UI_DESIGN.md §§1/4/5/6 |
| Scope | Vite React MapLibre, token variables/themes, shared evidence/range/date controls, sign-in/public view, typed fixtures. |
| Priority / phase | MVP |
| Accountable owner | Member 4 |
| One reviewer | Member 3 |
| Dependency | M3-01 H2 freeze; UI source |
| Expected files / outputs | apps/web/src/{api,mocks,components,theme}; apps/web/src/screens/SignIn.tsx; PublicPreview.tsx |
| Required stub / mock | copy reviewed contracts, synthetic badges and all error states |
| Effort and hackathon window | H0–H12; 7 active h |
| Input / output contract | OpenAPI/fixtures → accessible client shell |
| Local verification (planned) | `npm --prefix apps/web run test; npm --prefix apps/web run build` |
| Test cases | T-UI, T-CONTRACT: no secret in bundle, mock badge, accessible components |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 3 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H2 client shapes; H12 sign-in and public preview |
| Blockers / fallback | External design inaccessible → use written design, mark exact tokens VERIFY |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M4-02: Main map, timeline, feed and inspector

| Field | Commitment |
|---|---|
| Source trace | UI_DESIGN.md §§3.1/4; ARCHITECTURE.md §4.2 |
| Scope | Main map, missing passes, HH/HV, swipe/swap, folding rails, alert feed, per-agent inspector/time series/validation states. |
| Priority / phase | MVP |
| Accountable owner | Member 4 |
| One reviewer | Member 1 |
| Dependency | M4-01; M3-03; M1-02 layers |
| Expected files / outputs | apps/web/src/screens/{ScreenMainMap,ScreenInspector}.tsx; components/{TimeSlider,LayerToggle,MapLegend,AlertCard}.tsx |
| Required stub / mock | Layer/AlertDetail fixtures with missing interval and denied tile |
| Effort and hackathon window | H8–H24; 7 active h |
| Input / output contract | layer metadata + series → MapLibre presentation only |
| Local verification (planned) | `npm --prefix apps/web run test -- map timeline` |
| Test cases | T-UI, T-DISPLAY: no fabricated pass, denied source not loaded, only active legend |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 1 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H16 map on fixtures; H24 real-data layers |
| Blockers / fallback | COGs late → clearly synthetic layer; metadata never claimed as analysis |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M4-03: Decision screens, sources and print

| Field | Commitment |
|---|---|
| Source trace | UI_DESIGN.md §§2/3.1; ARCHITECTURE.md §§4.2/4.3 |
| Scope | Alert, summary, routes, shelters, Sources and A4 brief; source trace; review/field-check affordances; deny demo. |
| Priority / phase | MVP |
| Accountable owner | Member 4 |
| One reviewer | Member 3 |
| Dependency | M3-03; M2-02/04/05; M1-03 |
| Expected files / outputs | apps/web/src/screens/{ScreenAlertDetail,ScreenAreaSummary,ScreenAreaBrief,ScreenRoutes,ScreenShelters,ScreenSources}.tsx; print.css |
| Required stub / mock | all essential contract examples; role variants; no live sensitive coordinates |
| Effort and hackathon window | H16–H32; 9 active h |
| Input / output contract | authorized APIs → people-first screens + role-filtered A4 |
| Local verification (planned) | `npm --prefix apps/web run test -- screens print` |
| Test cases | T-BRIEF, T-TRACE, T-UI: seven route facts, warnings, footer sources, analyst shelter denial |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 3 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H24 summary/alert; H32 route/shelter/source; H38 print |
| Blockers / fallback | M2 workload → implement against fixtures early; never fake actual provenance |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M4-04: Responsive QA, demo and submission

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md §4.3/Timeline; UI_DESIGN.md §§1/5 |
| Scope | Phone layouts, keyboard/contrast, mock-real audit, end-to-end story, video, citations, final release checklist. |
| Priority / phase | MVP; PWA shell stretch |
| Accountable owner | Member 4 |
| One reviewer | Member 3 |
| Dependency | all MVP tasks; M1-03 science report; M3-02 security |
| Expected files / outputs | apps/web/src/screens/ScreenMobile.tsx; tests/e2e/; docs/demo_runbook.md; submission text; video outside Git |
| Required stub / mock | offline/failure scenarios; local recorded backup |
| Effort and hackathon window | H32–H48; 7 active h plus coordinated rehearsal |
| Input / output contract | approved build + evidence → reproducible judge walkthrough |
| Local verification (planned) | `npm --prefix apps/web run test:e2e; npm --prefix apps/web run build` |
| Test cases | T-A11Y, T-E2E, T-SUBMIT: role denial, failure fallback, full trace, citations |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 3 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H38 freeze; H40–44 video; H44–48 submission |
| Blockers / fallback | No verified hosting → recorded/local demo; protected offline deferred |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.
