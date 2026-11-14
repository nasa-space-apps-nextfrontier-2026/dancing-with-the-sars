# Member 4 work package: Chames

Chames: backend only: data, alerts, routes, shelters, worker and hosting.

[Team assignment and branches](../17_TEAM_ASSIGNMENT_AND_BRANCHES.md) · [Team allocation](../08_FOUR_MEMBER_TASK_ALLOCATION.md) · [Roadmap](../09_48_HOUR_DEVELOPMENT_ROADMAP.md) · [Contracts](../contracts/README.md)

Status: planned implementation, not completed work. Task IDs (M1 to M4) are work-package IDs; the owner field names the person (Member 1 = Udula, 2 = Thanoban, 3 = Rashiru, 4 = Chames). File paths below are proposed outputs, not present application code. Effort means active work within the given window; allow breaks and integration buffer. All implementation details beyond cited source are ARCHITECT RECOMMENDATION.

## M2-01: Source register, grids and base geometry

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md §2.1; DATA_AND_API_PLAN.md §3; DATASETS.md §7 |
| Scope | HOTOSM/admin/WorldPop/GHSL/NASADEM preflight; stable H3/cadaster joins; licence register. |
| Priority / phase | MVP |
| Accountable owner | Member 4 |
| One reviewer | Member 3 |
| Dependency | M3-01 shared schema; source terms |
| Expected files / outputs | pipelines/geodata/ingest.py; pipelines/geodata/grid.py; data/manifests/sources.json; data/private/base_layers.gpkg |
| Required stub / mock | synthetic tiny buildings/roads/grid; licence-unverified fixture |
| Effort and hackathon window | H0–H12; 6 active h |
| Input / output contract | licensed extracts → grid/crosswalk/source records/base layers |
| Local verification (planned) | `python -m pytest tests/geo/test_grid.py tests/geo/test_ingest.py` |
| Test cases | T-GEO, T-LICENCE: CRS/invalid geometry/admin boundaries/levels precedence |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 3 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H2 IDs to all; H12 base grid/residents/facilities inputs M3 |
| Blockers / fallback | Unavailable licence/download; tiny synthetic bounded fixture, no raw redistribution |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M2-02: People, facilities, services and report model

| Field | Commitment |
|---|---|
| Source trace | PROJECT_PLAN.md §§6.2–6.6/8; ARCHITECTURE.md §2.2 |
| Scope | Mass-conserving baseline, scenario ranges, vulnerable groups, five severity parts, reported operating state, source-linked what-to-bring. |
| Priority / phase | MVP |
| Accountable owner | Member 4 |
| One reviewer | Member 3 |
| Dependency | M2-01; M1-02 H16 cells; M2-03 services |
| Expected files / outputs | pipelines/geodata/people.py; facilities.py; services.py; report.py; data/private/area_values.parquet |
| Required stub / mock | AreaSummary and MetricValue fixtures owned for UI packaging by M4 |
| Effort and hackathon window | H8–H24; 7 active h |
| Input / output contract | cells + baseline + reports → MetricValue[] and AreaSummary |
| Local verification (planned) | `python -m pytest tests/unit/test_people.py tests/unit/test_services.py` |
| Test cases | T-PEOPLE, T-FACILITY, T-SERVICES: uncertainty, no overlap double count, unknown ≠ zero, hospital not inferred open |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 3 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H12 baseline to M3; H24 joined real-data summary to M3/M4 |
| Blockers / fallback | Missing demographics/operating report → Unknown; no invented current displaced count |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M2-03: Hazard adapters, dedup and corroboration

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md §2.2; PROJECT_PLAN.md §§5a/6.8b |
| Scope | FIRMS, Black Marble archive/NRT, IODA adapters; licensed ACLED/Insecurity context; source independence and alert review domain. Chames owns scheduler calls, IODA, ACLED context, corroboration and the Cached fallback. The night-light power-loss model and the fire event model are written by Thanoban in M1-04; Chames calls them. |
| Priority / phase | MVP bounded sources |
| Accountable owner | Member 4 |
| One reviewer | Member 3 |
| Dependency | M2-01 source terms; M3-04 scheduler |
| Expected files / outputs | pipelines/alerts/{firms,lights,ioda,corroboration}.py; data/private/alerts.geojson |
| Required stub / mock | sanitized HTTP fixtures for success/timeout/rate limit; no keys |
| Effort and hackathon window | H8–H24; 6 active h |
| Input / output contract | bounded observations → AlertDetail + freshness; callable adapters |
| Local verification (planned) | `python -m pytest tests/unit/test_alerts.py` |
| Test cases | T-ALERT, T-INDEPENDENCE: 1km/12h cluster, two clear nights, duplicate rehosts, cached timestamp |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 3 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H16 callable jobs to M3; H24 alerts to M4 |
| Blockers / fallback | FIRMS key/ToS blocked; visibly synthetic or Cached with last-good date; no claim live tested |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M2-04: Private graph, alternatives and closures

| Field | Commitment |
|---|---|
| Source trace | PROJECT_PLAN.md §6.5; ARCHITECTURE.md §2.2; DATA_AND_API_PLAN.md §4 |
| Scope | 2–3 distinct in/out routes; seven facts; unknown road status; confirmed closure invalidation; no external routing. |
| Priority / phase | MVP |
| Accountable owner | Member 4 |
| One reviewer | Member 3 |
| Dependency | M2-01 roads only to build and test. M3-02 policy and M3-03 endpoint only for the hand-off. |
| Expected files / outputs | pipelines/routing/graph.py; routes.py; closures.py; data/private/demo_graph.graphml |
| Required stub / mock | tiny synthetic graph with three options, bridge, unknown edge and disconnected case |
| Effort and hackathon window | H12–H32 (start on the synthetic graph at H12, real roads when M2-01 is ready); 5 active h |
| Input / output contract | authorized route intent + graph revision → RouteOption[] |
| Local verification (planned) | `python -m pytest tests/unit/test_routes.py` |
| Test cases | T-ROUTE: avoid confirmed closures, fewer paths explain, unknown heavy suitability, no network call |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 3 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H32 callable and revision tests to M3; seven facts to M4 |
| Blockers / fallback | Disconnected/incomplete graph → fewer/no route with warning, never fabricated third option |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M2-05: Shelter scoring and capacity ranges

| Field | Commitment |
|---|---|
| Source trace | PROJECT_PLAN.md §6.7; DATA_AND_API_PLAN.md §3 |
| Scope | Moved from Member 2 to Member 1 on 14 Nov 2026 to balance load; starts after H24 when radar work eases. Buildings first, configurable modes, uncertain floor-area estimate, access/hazard caveats, field-check requests; scoped open-land screen. |
| Priority / phase | MVP buildings; open land lower priority |
| Accountable owner | Member 4 |
| One reviewer | Member 3 |
| Dependency | M2-01; M1-02; M2-02; M3-02 |
| Expected files / outputs | pipelines/shelter/candidates.py; capacity.py; data/private/shelter_candidates.parquet |
| Required stub / mock | redacted ShelterCandidate example and synthetic candidate geometries |
| Effort and hackathon window | H24–H32; 4 active h |
| Input / output contract | authorized area + assumptions → ranked candidates + capacity range |
| Local verification (planned) | `python -m pytest tests/unit/test_shelter.py` |
| Test cases | T-SHELTER: modes, bounds, missing levels/GHSL, known hazard exclusion; never certify safety |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 3 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H24 first list; H32 final callable M3/M4 |
| Blockers / fallback | Height and structural uncertainty; type default explicitly labelled or no capacity; cut open land before buildings |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M3-04: Orchestration, Compose, CI and recovery

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md §§3.1/3.4; PROJECT_PLAN.md §8 Orchestrator/Safety |
| Scope | MVP: one worker scheduler, retry with cached last-good state, Docker Compose, env template, free tunnel only after checks. Stretch (after H38): job leases, CI, metrics, rollback. |
| Priority / phase | MVP; sensitive offline/LLM later |
| Accountable owner | Member 4 |
| One reviewer | Member 3 |
| Dependency | M2-03 adapters; M3-01/02 |
| Expected files / outputs | worker/main.py; infra/compose.yaml; .env.example; .github/workflows/ci.yml; scripts/{preflight,load_demo,verify_demo}.py |
| Required stub / mock | no-network adapter fixture; failure injection; synthetic demo bundle |
| Effort and hackathon window | H0–H38; 6 active h plus H40 backup |
| Input / output contract | schedule + adapter results → atomic stored snapshot/status |
| Local verification (planned) | `docker compose -f infra/compose.yaml config; python -m pytest tests/unit/test_jobs.py` |
| Test cases | T-JOBS, T-DEVOPS: retry idempotence, cached failure, restore and no secret logs |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 3 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H2 environment skeleton; H16 scheduler; H32 verified link if available; H40 backup |
| Blockers / fallback | Docker/tunnel unavailable → localhost + recorded demo; no paid service; offline/LLM remain later |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.
