# Testing and acceptance plan

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Two distinct verification levels

This planning deliverable is verified for file integrity, links, tables, source mapping, JSON/schema structure, ownership and Git diff. Application tests below are **planned, not executed**: the repository initially has no app or test harness. No claim of scientific accuracy, API access, deployment or field readiness follows from documentation validation.

All routine automated tests run on synthetic arrays, tiny synthetic graphs and scrubbed adapter responses without production credentials or war-zone coordinates. Source: ARCHITECTURE.md §1.4/3.5/4.4, PROJECT_PLAN.md §10, UI_DESIGN.md §§4–6. Extra engineering thresholds are ARCHITECT RECOMMENDATION.

| Test ID | Owner | Planned location | Cases | Pass criterion |
|---|---|---|---|---|
| T-AGENTS | Member 3 | tests/unit/test_domain_contracts.py | Twelve named deterministic interfaces, including disabled Movement fixture and Report/Safety | Each uses versioned trusted inputs and evidence-bearing outputs; no LLM-generated measurements |
| T-DATA | Member 1 | tests/geo/test_manifest.py | Metadata-only fixtures: same granule/version repeated, missing passes, footprint touch vs overlap, auth failure | Deterministic dedup; exact gaps; manifest/version/checksum required; no claim acquisition |
| T-LICENCE | Member 2 | tests/unit/test_source_policy.py + human source review | Unapproved ACLED/assessment terms, missing attribution/URL, Chinese-owned fixture | Block ingestion/publication; seven source references and source mark conflicts disclosed |
| T-RADAR | Member 1 | tests/geo/test_radar.py | Synthetic linear power, invalid nodata/zero, HH/HV mismatch, translated raster/version offset | Units correct; invalid Unknown; registration/drift gates fail; no silent interpolation |
| T-GEO | Member 1 | tests/geo/test_grid.py + raster QA | Wrong EPSG, invalid polygon, H3 r9→r8 parent, nodata, overlap/dimensions, GHSL coarse pixels | Correct joins/units; rejected invalid CRS; mask respected; sums conserved; area_id stable |
| T-ML | Member 1 | tests/unit/test_model.py + scientific report | Spatial train/hold-out blocks, 95/99/99.9 thresholds, Mahalanobis comparison, z fallback, top20 manual review | No train/hold-out leakage; measured false-alarm interval/enrichment; reasons; no assumed calibrated confidence |
| T-COHERENCE | Member 1 | tests/geo/test_crosscheck.py + expert review | Short versus cross-gap pair, phase alignment failure, seasonal decorrelation | Invalid feature excluded; no GUNW cross-gap fiction; report high technical risk |
| T-VALIDATION | Member 1 | tests/unit/test_assessment.py + licence/time/space review | Missing UNOSAT, mismatched report dates and polygons | No promised LB overlay or accuracy; UNDP/CNRS-L requires actual aligned authorized assessment |
| T-PEOPLE | Member 2 | tests/unit/test_people.py | Population conservation, overlap classes, null vulnerability, scenario weights and low/high | No double count; low≤high; pre-displacement label; missing not zero; date/source retained |
| T-FACILITY | Member 2 | tests/unit/test_facilities.py | OSM hospital with no radar change but no report; stale operating report | No inferred operating status; explicit Unknown or dated Reported |
| T-SERVICES | Member 2 | tests/unit/test_services.py | Night-light drop without report, unverified dependency edge | Possible power loss only; dependency uncertainty preserved; no logistics quantities |
| T-ALERT | Member 2 | tests/unit/test_alerts.py | 1km/12h clustering boundaries; low-confidence/permanent fires; two clear nights <50% baseline; timeout/429 | Dedup stable; baseline QA; cause Unknown; cached last-success displayed; failed poll not all clear |
| T-INDEPENDENCE | Member 2 | tests/unit/test_corroboration.py | Same report from two portals, GIBS and underlying product, independent reports with incompatible claim | No false upgrade; record source-family independence and scope of corroborated claim |
| T-ROUTE | Member 2 | tests/unit/test_routes.py | Tiny synthetic graph with three alternatives, closed bridge, unknown segment, disconnected nodes, new closure | Confirmed closures avoided; seven facts; fewer options explained; invalidation; external network forbidden |
| T-SHELTER | Member 2 | tests/unit/test_shelter.py | All space modes, OSM/GHSL/default precedence, missing geometry/levels, hazardous candidate | Building-first; correct capacity range; uncertainty shown; field-check caveat; no certification |
| T-CONTRACT | Member 3 | tests/api/test_contracts.py | Essential fixtures/schema and all endpoint status codes; client/server shared version | No shape drift; valid JSON; evidence required; generated client compiles |
| T-SQL | Member 3 | tests/geo/test_database.py | PostGIS transaction failure, duplicate run, invalid FK/low>high, region queries | Atomic rollback; idempotent load; GiST index used on bounded fixture query |
| T-RBAC | Member 3 | tests/security/test_roles.py | Anonymous/analyst/officer/coordinator/admin × route/shelter/brief; out-of-area objects | 401 absent session; 403 forbidden role/area/object; analyst cannot extract shelter fields anywhere |
| T-LAYER | Member 3 | tests/security/test_private_layers.py | GET/HEAD/Range on COG/PMTiles/GeoJSON, guessed path, encoded traversal, alternate download | Same 401/403; no public static bypass, public artifact contains no r9/private metadata |
| T-DELAY | Member 3 | tests/security/test_publication.py | UTC clock 71h59m versus 72h; missing acquisition time; derivative and cached tiles | No early release; r8 plus suppression; other roles cannot bypass withheld strike-derived files |
| T-CACHE | Member 3 | tests/security/test_cache.py + browser storage inspection | Role downgrade/logout, PWA offline, shared proxy, stale route/revoked brief | Private no-store; caches cleared; no restricted SW/localStorage/source-map copy |
| T-SAFETY | Member 3 | tests/security/test_safety.py + protection review | Military/frontline tags, live tracking fields, public concentrations, logs and upstream URLs | Excluded/rejected; no coordinates/tokens in logs; no external routing/LLM leak; field-use warnings |
| T-TRACE | Member 3 | tests/api/test_trace.py | Value→run→granules/source, unknown licence, cyclic lineage, inaccessible parent | Full permitted trace or redaction; no fabricated source/date/version; model QA shown |
| T-BRIEF | Member 4 | tests/e2e/brief.spec.ts + A4 inspection | Analyst/coordinator exports; QR/path; null inputs; long sources | One usable black-white A4 page, footnotes, role filtering, no token/coordinates in QR |
| T-UI | Member 4 | apps/web/src/**/*.test.tsx | All screens/components, source wording, side rails, focus, mock badge, route attributes | Source design behavior; no fake passes or values; candidate/unknown language everywhere |
| T-DISPLAY | Member 4 | tests/e2e/layers.spec.ts | GIBS unavailable/BETA blank; polarization/date swap; >8 layers | Neutral fallback; no GIBS analytical substitution; missing passes dotted; active legend only |
| T-A11Y | Member 4 | tests/e2e/accessibility.spec.ts + manual keyboard | 360/390/1280 px, 200% zoom, light/dark, keyboard/screen-reader paths | Focus and labels usable, contrast/shape cues, responsive field views, no map-only task |
| T-JOBS | Member 3 | tests/unit/test_jobs.py | Duplicate job, expired lease, interrupted fetch, closure revision | Idempotent retry; last-good retained; cached/error metadata; route/report invalidation |
| T-DEVOPS | Member 3 | scripts/verify_demo.py + restore rehearsal | Fresh clone, no-network fixtures, Compose health, backup laptop | Documented startup/test; no paid requirement; restore approved artifact/DB version |
| T-MOVEMENT | Member 2 | tests/unit/test_movement.py (future) | Coarse synthetic DTM/Meta, lag and restricted camps | Delayed aggregates only, unknown sample bias, no individual tracking |
| T-BACKLOG | Member 4 | Scope review at H38 | Every F01–F28 and deferred dataset/agent | Each assigned phase/task; deferred items not falsely counted as MVP done |
| T-LLM | Member 3 | tests/security/test_llm_boundary.py (future) | Sensitive question, numeric invention, unsupported answer | No external restricted input; trusted numbers only; non-authoritative fixed questions |
| T-E2E | Member 4 | tests/e2e/demo.spec.ts | Fire→detail→summary→routes→coordinator shelters→analyst denied→Sources; offline variant | Full deterministic journey and server denials; science failures visible |
| T-SUBMIT | Member 4 | Human submission checklist | Video, citations, challenge tie, clean repo, actual test report | All claims match executed work; release/tag only after review; no operational locations |


## Security fixture matrix and commands

M3 creates runtime-only sessions for each role and two area scopes. Test authenticated policy decisions at HTTP and object levels, plus actual byte/file serving. `GET /api/v1/shelters` anonymous → 401; analyst → 403; officer → 403; coordinator in wrong area → 403; coordinator in scope → authorized synthetic result. `POST /api/v1/routes` analyst → 403. Analyst `/briefs/{id}/print` must not reveal a coordinator's shelter section. Protected tiles/files receive 401/403 as appropriate including alternate download/Range/HEAD. Public response inspections scan entire body, not only visible UI.

Planned commands after implementation: `python -m pytest tests/unit tests/geo tests/api tests/security`; `npm --prefix apps/web run test`; `npm --prefix apps/web run test:e2e`; `npm --prefix apps/web run build`; `docker compose -f infra/compose.yaml config`. Member 3 supplies dependency locks and exact scripts. Never report these commands passed before they exist.

## Scientific gate interpretation

Quiet hold-out target “about 1%” at 99% threshold is a source expectation, not an achieved rate. Record sample size, numerator/denominator and uncertainty, spatial block split, residual calibration/season bias and 20 manual checks. Near-strike enrichment does not prove collapse or provide ground-truth accuracy. If verification fails, label outputs candidates with failed QA or withhold them; do not adjust thresholds on the hold-out set to manufacture success.

## Release blockers

Any secret/coordinate leak, public private-file bypass, missing 72 h gate, unauthorized role/object access, fabricated measurements or unsupported validation claim blocks external demonstration. Broken core NISAR processing blocks full real-data MVP acceptance. Honest synthetic backup is permitted with its limitations clearly stated. Cosmetic issues may be deferred only if access, source inspection, basic phone views and A4 remain usable. Record gate owner, actual command/result, artifact revision and unresolved risks.
