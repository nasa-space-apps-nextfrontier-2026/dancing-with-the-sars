# ML → backend → frontend integration agreement

Status: Phase 3 working handoff, pending three-member H2 acknowledgement. [Draft OpenAPI](contracts/openapi.yaml), [eight canonical JSON examples](contracts/README.md), [geospatial rules](04_GEOSPATIAL_AND_ML_PIPELINES.md) and [security policy](07_SECURITY_PRIVACY_AND_RBAC.md) remain the schema authority. This page specifies transfer and gates; it does not create competing JSON types or approve unresolved ADRs.

## Shared identifiers and value semantics

| Field/rule | Agreement | Failure action |
|---|---|---|
| `area_id` | Stable lowercase H3 string with explicit resolution; r9 for computation, parent r8 only for reviewed aggregated display. `demo-area-01` is fixture-only and not H3. | Reject mismatched resolution or unknown IDs; never coerce strings into JS numbers. |
| Geometry/CRS | GeoJSON WGS84/EPSG:4326; record raster source CRS and transform; use checked local metric CRS for distances. | Reject missing/invalid CRS or geometry; no degree-as-metre calculation. |
| Time | UTC acquisition start/end, processing time, `release_at` and exact actual pass ID. Local time is a display conversion. | Missing acquisition timestamp holds release; no interpolated passes. |
| Value row | Preserve `area_id, metric, low, high, unit, label, source, date, safety_tag` and canonical `MetricValue` extensions. Null means Unknown, never zero. | Reject missing provenance or low > high. |
| Evidence | Observed, Reported, Corroborated, Unknown are distinct from synthetic/real and Cached/Stale. Candidate damage remains a hypothesis. | Do not promote evidence beyond its weakest independent input. |
| Dataset | `SourceRecord` carries provider, product level, version, acquisition, licence, URL, limits and `live_tested`. | Unverified rights or version stays blocked. |

No real NISAR pixel, model score or population count is generated in the application scaffold. If scientific QA has not passed, return explicit unavailable/Unknown. The 72-hour minimum hold, public r8 suppression and separate review apply to real strike-related change and all derivatives; a valid H3 index alone does not make release safe.

## B ↔ C model handoff

B owns ASF scene discovery, Earthdata access, GCOV alignment and HH/HV feature extraction for **track 151 descending/frame 72**. Each input artifact needs source collection/granule IDs, actual coverage and valid-pixel footprint, polarization/band, processing version/CRID, acquisition UTC, raster CRS, calibration/unit interpretation, nodata mask, file checksum, software/parameter run ID, licence and QA status. B sends a small synthetic feature table first; raw granules remain private and out of Git.

C owns the agreed feature/output schema, H3 join and ancillary features, Isolation Forest or documented z-score fallback, candidate classification, confidence wording, independent validation and model report. Required output concepts are H3 r9 cell ID, paired acquisition IDs/dates and versions, HH/HV feature values with units and valid counts, candidate/other-change/Unknown class, score and threshold provenance, reason codes, QA state, source/run IDs and checksum. Scores are anomaly scores, **not calibrated damage probabilities**. Unknown/no-data and BETA–PROVISIONAL bias failures remain explicit. The output table/GeoJSON/COG manifest uses the existing `MetricValue`, `Layer`, `SourceRecord` and area contracts where applicable; any extra field goes through a contract PR before ingestion.

Filename convention: `<product>_<track>_<frame>_<acquisition-or-pair>_<processing-version>_<run-id>.<ext>` with a manifest mapping exact filenames to SHA-256. This is an implementation convention to review at H2, not a claim that source products already exist. Large COG/GeoTIFF and private GeoJSON stay outside Git; only synthetic small fixtures and non-sensitive manifests may be committed. B reviews C's interpretation of polarization/version; C reviews B's feature semantics.

## A's ingestion and API boundary

A validates artifact schema, checksum, run ID, source/rights, coverage, CRS, dates, version, evidence, no-data and safety tags before transactional PostGIS insertion or pointer promotion. The API never computes large radar scenes during HTTP requests. Reject an artifact with missing metadata or failed QA; retain last reviewed run. Synthetic input is stored/served separately and every response has `synthetic: true` plus per-value labels. Real and synthetic rows may not be silently merged.

The first no-database slice uses the canonical synthetic `AreaSummary.json` and `SourceRecord.json`: an authenticated analyst scoped to `demo-area-01` may retrieve `/api/v1/areas/demo-area-01/summary`; `/api/v1/sources/demo-source-01` gives the synthetic source record; wrong scope is denied and unknown IDs fail explicitly. This is a deterministic **development adapter**, not live evidence. The frontend selects a clearly non-geographic synthetic area, fetches both typed responses, displays range/Unknown/age/source and handles loading/error/denied. An anonymous map never fetches or exposes the restricted summary.

Later real integration uses `GET /layers`, `/layers/{layer_id}/timeseries`, guarded tiles/files, `/areas/{area_id}/damage`, `/areas/{area_id}/summary`, `/areas/{area_id}/values`, `/sources` and `/values/{value_id}/trace` as specified in the draft contract. A server policy checks role, area, object, licence, release time and field filtering before returning a file or JSON. Public GIBS imagery, if technically available, is labelled context and never passed off as B/C analytical output.

## Checkpoints and acceptance

| Gate | Handoff evidence | Receiver check |
|---|---|---|
| 1: contract freeze | B/C/A sign off on canonical IDs, field names, CRS, UTC, null/Unknown, version and safety policy | A validates fixture against JSON Schema/OpenAPI; all three record unresolved points |
| 2: synthetic full stack | Small synthetic B→C artifact plus A's API→frontend area/source flow | pytest and Vitest verify role denial, typed response, provenance and labels without Docker |
| 3: real candidate | B's version/registration/coverage QA; C's spatial hold-out, top-cell review, controls and limitations | A ingests only reviewed artifacts; otherwise keeps real map unavailable and demo synthetic |

Every PR includes schema version, exact artifact path, checksum, test command/result, date/CRS/unit, source/licence, sensitivity, missing passes and receiving-member acknowledgement. A schema change lands before dependent code. No fabricated precision/recall, confirmed destruction, safe route, working facility or certified shelter claim is permitted.
