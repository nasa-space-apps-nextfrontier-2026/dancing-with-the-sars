# Risk register and decision log

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Decision authority

Source disagreements are retained in [source audit](00_SOURCE_AUDIT.md); proposals do not replace original files. APPROVED = explicit user constraint or recorded source decision; PROPOSED = recommended pending owner/leader review; VERIFY = fact/access needs evidence; BLOCKED = unavailable evidence prevents that feature, not the entire documentation task. Review decisions at H2 and H24; record approver/date and test evidence in later PRs.

| ID | Topic | Source A + section | Source B + section | Impact | Recommended decision | Status | Owner | Validation |
|---|---|---|---|---|---|---|---|---|
| D01 | Catalogue count | DATASETS.md §1–3: 14 | DATA_AND_API_PLAN.md §2–3: 15 (7 NASA, 8 other) | Add GUNW and GHSL; remove unavailable UNOSAT. OCHA is a supporting join asset, not a hidden sixteenth headline source. Keep both inventories. GIBS is NASA-operated but Other provenance. | Recommend 15, pending leader approval | PROPOSED | Member 2 | Compare numbered families and terms at H2 |
| D02 | Before/after coverage | PROJECT_PLAN.md §5: public data starts June | DATA_AND_API_PLAN.md §1; NASA_DATASET_ANALYSIS.md §2 | Without BETA there is no pre-escalation baseline. | 151D frame 72; six BETA dates through 19 Jan, first later 24 Jun, eleven later through 3 Nov; no invented 20 Jan–17 Jun passes | VERIFY | Member 1 | Re-query ASF by collection, track, frame and actual overlap; save manifest |
| D03 | GUNW availability | DATASETS.md §6: none over Lebanon | DATA_AND_API_PLAN.md §2: 22 BETA + 37 PROVISIONAL; V1 none | Short-baseline products do not span Jan–Jun. | Conditional stretch; verify footprint and paired dates; GSLC cross-gap coherence high risk | VERIFY | Member 1 | Inspect pair baselines, phase alignment, noise and decorrelation on quiet controls |
| D04 | Version and season correction | ARCHITECTURE.md §1.3: corrected automatically | DATA_AND_API_PLAN.md §1; NASA_DATASET_ANALYSIS.md §9: consistency test needed | Anomaly training cannot guarantee removal of version or seasonal effects. | Stable-area normalization, registration and incidence/seasonality tests; fail closed to Unknown | PROPOSED | Member 1 | Version-stratified quiet hold-out, residual bias and spatial artifact report |
| D05 | Historical lights and fires | DATASETS.md §2: NRT | DATA_AND_API_PLAN.md §2: archive + NRT | NRT rolling retention cannot supply January baseline. | Join archives and NRT with product-quality/version precedence and timestamps | PROPOSED | Member 2 | 60 clear-night baseline completeness; duplicate archive/NRT test |
| D06 | Height and roads | PROJECT_PLAN.md §6.7: OSM levels | DATA_AND_API_PLAN.md §3: only 0.28% levels, GHSL fallback | Capacity uncertain; public Overpass unreliable. | HDX primary; OSM levels then GHSL 100 m / 3 m then type default; propagate range | PROPOSED | Member 2 | AOI coverage audit; no per-building precision claim from 100 m grid |
| D07 | Damage validation | PROJECT_PLAN.md §4–6; DATASETS.md §3: UNOSAT and UNDP | ARCHITECTURE.md §1.2: no usable Lebanon UNOSAT; 2026 UNDP not found | No supervised ground truth or accuracy percentage is established. | No promised UNOSAT overlay. UNDP/CNRS-L exact time/space and permission VERIFY; independent QA if unavailable | BLOCKED | Member 1 | Obtain licensed, aligned assessment before validation overlay or precision/recall |
| D08 | Display versus science | NASA_DATASET_ANALYSIS.md §5 expands core datasets | DATA_AND_API_PLAN.md §2–3 narrows them; PDF p2 §4 | Extra imagery must not inflate analytical evidence or scope. | GIBS NISAR and DIST-HLS context only; BETA may be blank; document exclusions | PROPOSED | Member 1 | Trace numeric inputs to scientific products, never rendered tiles |
| D09 | Web/PWA/offline | UI_DESIGN.md §1, §3.1: installable and saved routes | ARCHITECTURE.md Part 4 and stretch: responsive + print first | Sensitive offline data survives logout. | Web responsive MVP and A4 print; installable public shell stretch; restricted offline briefs/routes post-hackathon pending encryption/revocation design | PROPOSED | Member 4 | No service-worker cache of protected responses; logout purge test |
| D10 | Login and public preview | PROJECT_PLAN.md §1: not public app | UI_DESIGN.md §6: login decided, public-safe view | Public preview must not expose sensitive buildings or population concentrations. | Protected roles plus strictly filtered public H3 r8 preview; briefs require sign-in | APPROVED | Member 3 | 401/403 and object/file/download/print tests |
| D11 | Navigation | PROJECT_PLAN.md §6.5: in-app or phone handoff | UI_DESIGN.md §7: in-app only; DATA_AND_API_PLAN.md §4 local routing | External URLs can leak destinations. | Local graph and in-app static turn list; no external handoff, no GPS tracking | PROPOSED | Member 2 | Network egress test; closure revision invalidates selected route |
| D12 | Delay | PROJECT_PLAN.md §10: days | UI_DESIGN.md §5/7 and ARCHITECTURE.md §3.3: 72 h after pass | Delayed publication must cover derivatives and alternate files. | At least acquisition-end +72 h for all newly published strike-related changes; public also r8 and suppression; correction never resets old evidence to evade policy | APPROVED | Member 3 | Boundary at 71:59/72:00; cache, tiles, trace and report export tests |
| D13 | Fire satellite label | UI_DESIGN.md §7 mockup S-NPP | DATASETS.md §2; DATA_AND_API_PLAN.md §2 NOAA-20/21 | Mock label could misidentify data. | NOAA-20/21 product-specific labels; S-NPP archive only if actually used | PROPOSED | Member 4 | SourceRecord satellite equals UI and export |
| D14 | Global and movement | PROJECT_PLAN.md §5/6.8 global watch list | ARCHITECTURE.md Ground rules: one area | Four-person capacity. | South Lebanon MVP; aggregated movement stretch; automatic global watch list and selective processing post-hackathon | PROPOSED | Member 2 | No global scanning jobs in MVP; retained backlog |
| D15 | Challenge rules and provenance counts | DATASETS.md intro says 6 tab/tool; §2 marks GIBS Other | PROJECT_PLAN.md §3 says four additional then six; rules claim | The six-source total and official rules are not independently verified. | Count explicit marks: one Tab + four Tab tool = five in current rows; retain claimed six as conflict. Verify current rules; retain exclusion of Chinese-owned data as project constraint | VERIFY | Member 4 | Capture Resources-tab/rule evidence and licences at H0; inaccessible here |
| D16 | Stretch after freeze | ARCHITECTURE.md stretch only after H38 | ARCHITECTURE.md Timeline: freeze H38 | Starting optional features after freeze threatens demo. | Only validated optional work completed before H38 can ship; post-H38 fixes only | PROPOSED | Member 4 | Feature inventory frozen at H38 |
| D17 | Counts are minimums | PROJECT_PLAN.md §11; ARCHITECTURE.md §1.4 | ARCHITECTURE.md §1.3 allows false alarms | Misses do not make an uncertain estimate a rigorous lower bound. | Report candidate ranges and false positives/negatives; no guaranteed lower-bound claim | PROPOSED | Member 1 | Sources page uncertainty review |
| D18 | Coherence and source breadth | NASA_DATASET_ANALYSIS.md §5 calls GSLC/GUNW, DSWx, POWER core | ARCHITECTURE.md tiers and DATA_AND_API_PLAN.md §3 drop/defer | Earlier investigation is broader than final weekend budget. | GCOV core; GSLC/GUNW conditional; broad environmental science backlog excluded from demo | PROPOSED | Member 1 | Tier budget and exclusion ledger review at H2 |


## Risk register

| ID | Risk | Impact | Owner | Trigger | Mitigation / contingency |
|---|---|---|---|---|---|
| R01 | Radar download/disk exceeds weekend | High | Member 1 | H0 throughput and actual manifests | A/B first, crop, no C until core green; synthetic fallback disclosed |
| R02 | Jan–Jun version/season confounding | High | Member 1 | Stable controls and registration fail | Withhold claim, report Unknown/QA failure; not solved automatically by anomaly model |
| R03 | No aligned damage labels | High | Member 1 | UNDP/CNRS-L unavailable or mismatched | Quiet hold-out/manual checks; no false accuracy/UNOSAT overlay |
| R04 | Cross-gap coherence invalid | High | Member 1 | Pair phase/baseline/decorrelation checks fail | Exclude coherence; retain valid GCOV |
| R05 | M2 overloaded | High | Member 2 | Miss H12/H16 handoff | M3 scheduling/loaders, M4 fixtures, M1 GIS review; postpone global/movement/open land |
| R06 | Sensitive file/brief/cache bypass | Critical | Member 3 | Any RBAC/area/Range/export test fails | Block link/release; sanitize fixtures and fix policy before demo |
| R07 | Licences/API accounts unavailable | High | Member 2 | Missing written permitted use or key | Disable source, Unknown or synthetic; never assume unrestricted HDX reuse |
| R08 | Population/height/road incompleteness | High | Member 2 | Coverage/levels audit low; no operating reports | Ranges/default flags, no capacity/passability certainty |
| R09 | Source outages/rolling retention | Medium | Member 3 | Timeout, stale API, NRT date missing | Archive joins, last-good Cached, timestamps; no fabricated current data |
| R10 | Public aggregation still reveals civilians | Critical | Member 3 | Unique/high-risk cells or temporal differencing | Suppress/manual review; use synthetic public layer |
| R11 | Mock data mistaken for measured facts | High | Member 4 | Fixture audit detects unlabeled values | Visible synthetic flags on maps/exports; per-value trace |
| R12 | Challenge rules/provenance miscount | High | Member 4 | Official page inaccessible; six vs five marks | Keep VERIFY; capture actual rules before development/submission |
| R13 | Hosting/Windows GIS tooling fails | Medium | Member 3 | Compose/GDAL/tippecanoe or tunnel preflight fails | Containerize verified tools, laptop/recording backup; no paid switch |
| R14 | Feature freeze violated | Medium | Member 4 | Optional work proposed after H38 | Fixes only, move enhancement to after hackathon |


## Proposed ADRs

[ADR 001](adr/001_MODULAR_MONOLITH_AND_CONTRACTS.md) fixes implementation boundaries; [ADR 002](adr/002_PUBLICATION_AND_LOCAL_ROUTING.md) covers privacy; [ADR 003](adr/003_RADAR_VALIDITY_AND_DATA_BASELINE.md) resolves scientific/data proposal boundaries. All retain PROPOSED status unless an explicit existing requirement is stated separately. No undocumented alternative stack or paid service is chosen.
