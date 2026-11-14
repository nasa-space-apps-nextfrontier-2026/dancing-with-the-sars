# Member 2 work package: Thanoban

Thanoban: small-data ML (night lights, fires, evidence tests); no backend, no radar downloads; demo and submission from H38.

[Team assignment and branches](../17_TEAM_ASSIGNMENT_AND_BRANCHES.md) · [Team allocation](../08_FOUR_MEMBER_TASK_ALLOCATION.md) · [Roadmap](../09_48_HOUR_DEVELOPMENT_ROADMAP.md) · [Contracts](../contracts/README.md)

Status: planned implementation, not completed work. Task IDs (M1 to M4) are work-package IDs; the owner field names the person (Member 1 = Udula, 2 = Thanoban, 3 = Rashiru, 4 = Chames (not on the project)). File paths below are proposed outputs, not present application code. Effort means active work within the given window; allow breaks and integration buffer. All implementation details beyond cited source are ARCHITECT RECOMMENDATION.

## M1-04: Services-loss models (night lights, fires)

| Field | Commitment |
|---|---|
| Source trace | ARCHITECTURE.md Part 2.2 (night lights, fires); PROJECT_PLAN.md §5a, §6.4; DATASETS.md §2 |
| Scope | Small-data ML, no radar downloads. (a) Night-light power-loss model: Black Marble VJ146A2/VJ246A2 archive plus NRT, 60-clear-night baseline per cell, anomaly score gives "Possible power loss" with confidence. (b) Fire event model: FIRMS points, remove permanent hot spots and low confidence, cluster within 1 km and 12 h, give "Fire detected" events (never a cause). The strike-enrichment tests moved to Udula (M1-03) on 14 Nov 2026; Thanoban hands over the harness he already built (PRs #6 and #12). Owner is Thanoban. |
| Priority / phase | MVP |
| Accountable owner | Member 2 |
| One reviewer | Member 1 |
| Dependency | M2-01 H3 grid is not needed (uses `h3` directly) |
| Expected files / outputs | worker/services/nightlights.py; power_loss.py; fires.py; firms_feed.py; blackmarble_history.py |
| Required stub / mock | synthetic clear-night series with a known drop; fake FIRMS points with a permanent hot spot |
| Effort and hackathon window | H2–H30; about 16 active h; all laptop-light (under about 1 GB of data) |
| Input / output contract | Black Marble cells / FIRMS points → alert events (area, time, source, label, confidence) |
| Local verification (planned) | `python -m pytest worker/tests` |
| Test cases | T-ALERT, T-SERVICES: insufficient clear nights → Unknown; permanent hot spot removed; two sources agree → Corroborated; no cause claimed |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 1 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H12 callable functions to Rashiru (M2-03) |
| Blockers / fallback | Too few clear nights → Unknown; missing NRT history → archive join |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.

## M2-06: Movement and global backlog specification

| Field | Commitment |
|---|---|
| Source trace | PROJECT_PLAN.md §§5/6.8; ARCHITECTURE.md stretch |
| Scope | DTM/Meta coarse delayed trends; future watch list and selective processing; no individual/camp coordinates. |
| Priority / phase | Stretch movement; global after hackathon |
| Accountable owner | Member 2 |
| One reviewer | Member 1 |
| Dependency | M2-02; licences; M3-02 privacy |
| Expected files / outputs | docs/backlog/movement_global.md; future worker/geodata/movement.py |
| Required stub / mock | unavailable/disabled trend fixture |
| Effort and hackathon window | No core allocation; max 1 h design; implementation after core |
| Input / output contract | permitted coarse reports → delayed trend, not live people |
| Local verification (planned) | `python -m pytest tests/unit/test_movement.py (after implementation)` |
| Test cases | T-MOVEMENT, T-BACKLOG: aggregation/delay, no individual payloads |
| Definition of Done | Expected artifacts committed in a small PR to dev; Member 1 reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims. |
| Integration checkpoint | H38 record deferred scope; later approved iteration |
| Blockers / fallback | Licences, cadence, sample bias; stay disabled |

Handoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.
