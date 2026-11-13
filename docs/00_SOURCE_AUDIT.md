# Source audit

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Scope and reading record

All six Markdown references were read in full, including tables, caveats and open items. Both PDF pages were text-extracted with pypdf and rendered with Poppler and visually inspected. Page 1 is the six-portal directory plus ASF links; page 2 continues access links, has a five-row priority table and five practical notes. No additional scientific chart or hidden map appeared. Poppler warned about Symbol/ArialUnicode fonts; visible text and the table remained readable. The original slide mentioned in the PDF was not supplied and was not claimed as reviewed.

| Reference | Audit | SHA-256 |
|---|---|---|
| ARCHITECTURE.md | READ completely | bbdf96f7ec949f9a689bf6cb14c9938eb23287eabddb6cfa1690c8087112c0b8 |
| DATASETS.md | READ completely | 0beee7862eead24c484cc70505279bc014d048b68b8eecafd7f3d06326f4176b |
| DATA_AND_API_PLAN.md | READ completely | 43e97ac8202c8c0934275997c0f41bfc528211737ea8b83ce63261e1e51b9a3c |
| NASA_DATASET_ANALYSIS.md | READ completely | 77775ac65a1ca0d765b7b75a96db70dc05361069965f0ef493c4f4f608fd813b |
| NASA_Open_Data_Links_Earth_Impact_Intelligence.pdf | READ; PDF both pages visually inspected | 1dc3fe32ce33771e7eb7c6ba63a6a0a9ba945ed6f53751a1c20b104976152ba9 |
| PROJECT_PLAN.md | READ completely | cc897d7cfe7d82c4d15495ee495bf783b41261b0bb18a7579430817a7e9d1c01 |
| UI_DESIGN.md | READ completely | 600754be1f2fc9e0662a0ad9379bd500a8f836b4ec80d47b46e640b5f8ab91db |


No mandatory reference is missing. Original documents remain unchanged. Conflicting scientific observations are source-reported, not independently validated. ARCHITECT RECOMMENDATION identifies additions; APPROVED below means explicit user requirement or recorded source decision, not fresh scientific certification.

## Repository and network reality

Repository: `dancing-with-the-sars`; original branch `docs/architecture-plan`, original HEAD `022599111ea437b62bf297851e0109f08cde94d8`; clean tracked and untracked state. Remote `https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars.git`. Detected default via `origin/HEAD`: `main`, fetched SHA `e99348c0aec238b4d4252f02001560f6f18d1fc7`. No AGENTS.md found in repository or accessible workspace ancestors. No application code, dependencies or tests existed: root README plus seven references only.

Git was absent from PATH but found at `C:/Program Files/Git/cmd/git.exe`. Initial fetch failed under sandbox; explicitly escalated retry succeeded. Planning branch created from origin/main, then fast-forwarded the two existing architecture commits from the original branch so ARCHITECTURE.md is retained with its history. No branch reset, deletion, reference edit, default-branch merge or bulk download occurred. Upstream to origin/main was removed from the new planning branch to avoid accidental push targeting.

External browse attempts: Claude UI mockup, Space Apps 2026 Resources tab, ASF NISAR documentation returned inaccessible via browser tool. Therefore exact token values in the remote mockup, current competition rules and new official product checks remain VERIFY. No CMR/ASF dataset query, FIRMS authenticated call, acquisition, deployment or scientific validation was executed. URLs in the source documents were read as references; reachability of all links was not tested. The 13 Nov snapshot is preserved, including unverified July/Aug outage and pre-21-Oct provisional claims. Recheck per-granule metadata instead of assuming date implies version.

## PDF practical rules

PDF p1 §1: Open Data is a metadata catalogue, API portal authentication varies, Earthdata filters by place/time, Worldview is context, Exoplanet Archive irrelevant, NASA Open is open-science information. PDF p1–2 §2: ASF Vertex/Search for SAR discovery, Earthdata Login for protected files, GIBS for web imagery, EONET natural-event context.

PDF p2 §3 priority order: ASF → Earthdata Search → Worldview/GIBS → Open Data catalogue → relevant general NASA APIs. PDF p2 §4: check service-specific auth/rate limits; GIBS is visualization, not analytical evidence; use NISAR product workflows instead of assuming api.nasa.gov; record dataset name/level/acquisition/version/coverage/terms/URL; never publish sensitive shelters or identifiable population concentrations. These rules are independently enumerated in [traceability](14_REQUIREMENTS_TRACEABILITY_MATRIX.md).

## Source discrepancies

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


## Reverification protocol

Member 1 saves metadata-only ASF/CMR query parameters, response time, collection IDs, counts, overlaps, track/frame and checksums at H0. Member 2 checks licences, dates, coverage, archives, GHSL units and humanitarian reports. Member 3 verifies credentials without recording secrets and local route isolation. Member 4 verifies challenge rules and mockup accessibility. Unavailable data remains Unknown or visibly synthetic; it cannot silently become a verified result.
