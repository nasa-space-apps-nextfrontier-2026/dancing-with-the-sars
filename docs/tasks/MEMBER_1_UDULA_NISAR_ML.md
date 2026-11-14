# Member 1 work package: Udula

Udula: NISAR damage model, end to end (all large radar downloads and training).

[Team assignment and branches](../17_TEAM_ASSIGNMENT_AND_BRANCHES.md) · [Team allocation](../08_FOUR_MEMBER_TASK_ALLOCATION.md) · [Roadmap](../09_48_HOUR_DEVELOPMENT_ROADMAP.md) · [Contracts](../contracts/README.md)

Status: planned implementation, not completed work. Task IDs (M1 to M4) are work-package IDs; the owner field names the person (Member 1 = Udula, 2 = Thanoban, 3 = Rashiru, 4 = Chames). File paths below are proposed outputs, not present application code. Effort means active work within the given window; allow breaks and integration buffer. All implementation details beyond cited source are ARCHITECT RECOMMENDATION.

## M1-01: Scene discovery, licence and tier preflight

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md §1.1; DATA_AND_API_PLAN.md §§1–2; NASA_DATASET_ANALYSIS.md §9 |
| Scope | Search BETA/provisional/V1, save actual overlap, track/frame, acquisition/version, download tiers only during development. Owner is Udula, who does all large downloads on the strong machine and shares only small crops (14 Nov 2026 team decision). |
| Priority / phase | MVP |
| Accountable owner | Member 1 |
| One reviewer | Member 2 |
| Dependency | none; H2 contract freeze |
| Expected files / outputs | worker/radar/discover.py; data/manifests/nisar.json; worker/radar/config/demo_aoi.json |
| Required stub / mock | metadata-only synthetic granules, missing-pass list |
| Effort and hackathon window | H0–H8; 5 active h plus download wait |
| Input / output contract | AOI + collection IDs → versioned granule manifest |
| Local verification (planned) | `python -m pytest tests/geo/test_manifest.py` |
| Test cases | T-DATA, T-LICENCE: duplicate versions, gap retained, wrong track, unavailable credentials |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 2 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H2 IDs and manifests to M3; H8 registered crop inputs to M1-02 |
| Blockers / fallback | Network, disk, Earthdata; bounded retries or explicitly synthetic data; never claim acquisition |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M1-02: Radar transformations, model and artifacts

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md §§1.3/1.5; DATA_AND_API_PLAN.md §1 |
| Scope | Registration, masking, version normalization, HH/HV features, quiet blocks, Isolation Forest/Mahalanobis, fallback, reason codes and COGs. Stretch only if core is green: GSLC coherence (Udula's machine). |
| Priority / phase | MVP |
| Accountable owner | Member 1 |
| One reviewer | Member 2 |
| Dependency | M1-01; M2-01 grid; M3-01 schema |
| Expected files / outputs | worker/radar/process.py; worker/radar/model.py; data/private/damage_cells.parquet; data/private/change/*.tif; data/manifests/radar_run.json |
| Required stub / mock | small synthetic arrays and H3 cells; no war-zone geometry |
| Effort and hackathon window | H2–H24; 14 active h |
| Input / output contract | granules + grid → damage_cells v0.1 + COG index |
| Local verification (planned) | `python -m pytest tests/geo/test_radar.py tests/unit/test_model.py` |
| Test cases | T-RADAR, T-GEO, T-ML: nodata, units, >3 dB share, quantiles, registration and drift |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 2 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H16 first cells M2/M3; H24 COG/time-series manifest M3 |
| Blockers / fallback | Cross-version bias; stop invalid comparisons, retain Unknown; z-score only if valid features |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M1-03: Scientific QA and validation availability

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md §§1.2/1.4; NASA_DATASET_ANALYSIS.md §9 |
| Scope | Spatial hold-out, enrichment with controls, 20 manual top cells, uncertainty report. These tests are the main proof. "No matching assessment available" is the normal case: no UNOSAT exists for Lebanon and no 2026 UNDP/CNRS-L was found; use one only if it appears at H0. Udula owns the hold-out areas and the 20-cell eye check for the NISAR model. The strike-enrichment and evidence tests are built and run by Thanoban inside M1-04 on small tables; the combined results go to the Sources page. |
| Priority / phase | MVP QA; overlay conditional |
| Accountable owner | Member 1 |
| One reviewer | Member 3 |
| Dependency | M1-02; permitted M2-03 context |
| Expected files / outputs | worker/radar/evaluate.py; data/manifests/model_tests.json; docs/model_validation.md (implementation output) |
| Required stub / mock | fixed synthetic score distribution and manual-review checklist |
| Effort and hackathon window | H24–H32; 6 active h |
| Input / output contract | cells + hold-out + reports → measured test results and limitations |
| Local verification (planned) | `python -m pytest tests/unit/test_evaluation.py` |
| Test cases | T-ML, T-VALIDATION: no leakage; duplicate reports; false-alarm numerator/denominator; no fake accuracy |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 3 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H32 QA results to M3 trace and M4 Sources |
| Blockers / fallback | No aligned labels; report independent QA, no precision/recall or confirmed collapse claims |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.
