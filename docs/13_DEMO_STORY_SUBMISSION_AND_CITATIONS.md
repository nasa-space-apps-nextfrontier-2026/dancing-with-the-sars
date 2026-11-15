# Demo story, submission and citations

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Judge-facing story

Source: ARCHITECTURE.md §4.3 and PROJECT_PLAN.md §§2/5/6. Show humanitarian decisions grounded in NISAR surface change, with evidence and limits. Do not frame the product as validated navigation, military intelligence or current live satellite tracking. All sensitive route/shelter examples are synthetic/redacted. Every synthetic panel has a badge; actual science results are shown only after measured QA.

| Step / target time | Operator / owner | Show | Evidence of success |
|---|---|---|---|
| 0:00–0:30 | M4 narrator, logged out | Public-safe delayed r8 preview, challenge tie and sign-in | No exact shelter/critical-site/route data |
| 0:30–1:10 | Analyst, M1 science support | Jan BETA→Jun NISAR HH/HV change, missing acquisition interval, later pass strip | Actual dates/version/QA and candidate wording; synthetic fallback disclosed if needed |
| 1:10–1:50 | Officer | Fire alert→detail with 1/3 km synthetic rings | Fire detected, no cause, source/local+UTC time, cached/fresh state |
| 1:50–2:30 | Officer | Area summary people first, vulnerability/what-to-bring | Source-linked ranges, Unknown service limits, no invented quantities |
| 2:30–3:10 | Officer | Compare inbound/outbound A/B/C; inject synthetic confirmed closure | Seven facts, revision warning, recompute locally; no safe label |
| 3:10–3:40 | Coordinator | Ranked building shelter, space mode and capacity uncertainty | For checking, protection/ordnance banner, no public locations |
| 3:40–4:10 | Analyst, M3 security support | Direct shelter API attempt and protected file attempt | Actual 403; show scrubbed response, not only missing button |
| 4:10–4:50 | Analyst | Sources→trace value→model QA; print brief | Dataset/version/date/licence, measured tests/limits; A4 source footnotes |
| 4:50–5:00 | M4 | Honest limits and next steps | Not field validated; explicit availability and validation blockers |

Times are ARCHITECT RECOMMENDATION, not a known competition video limit. M4 verifies submission requirements and adjusts. Rehearse H32–H38; record H40–H44. No live deployment or submission is performed by this planning task.

## Backup and failure narrative

M3 prepares local sanitized demo bundle and second laptop; M4 records the approved journey. Simulate one API outage to demonstrate Cached + last-success instead of pretending live updates. If radar processing fails, show synthetic UI journey plus NISAR metadata and clearly state uncompleted scientific work. Do not imply browse imagery is computed damage. Security failure removes external link until fixed.

## Citation package

NISAR challenge citation: [Dancing with the SARs Resources tab](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=resources), verification pending. Link official product/DAAC guidance and exact collection/granule record for real acquisitions. NISAR is direct Tab per source; OPERA/Black Marble/FIRMS/NASADEM Tab tool; GIBS Other via PDF. Do not repeat the inconsistent six-source provenance count without its caveat.

For every used dataset provide provider, product/level, acquisition range, processing version, spatial coverage/resolution, terms/attribution, source URL, accessed date, API and known limits. NASA and ESA/Copernicus attributions are separate where required. UNDP/CNRS-L availability and rights remain VERIFY. OSM attribution/ODbL, WorldPop/JRC product terms, ACLED/DTM/Meta/Insecurity Insight restrictions need resource-specific review. Never cite a source as acquired merely because it appears in the catalogue.

The [source audit](00_SOURCE_AUDIT.md) links the untouched references. The PDF directory is a provenance/access aid, not a scientific validation source. The [source link register](14B_SOURCE_LINK_REGISTER.md) inventories supplied URLs and check status.

## Submission checklist and release record

M4 owns text/video/repository links/citations and actual Space Apps form requirements; M1 signs science caveats, M2 confirms source rights and quantities, M3 signs security and hosting scope. Include exact reviewed commit, synthetic-versus-real declaration, measured model QA, source snapshot date, unavailable datasets and operational limitations. Tag reviewed dev only after final checks; do not imply branch protection, deployment, field validation or submission occurred during planning.
