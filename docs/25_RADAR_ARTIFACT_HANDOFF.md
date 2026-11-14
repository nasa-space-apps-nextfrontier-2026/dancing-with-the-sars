# Radar artifact handoff v1

Status: synthetic-only validation implemented. Real scientific artifacts require B/C review and a contract change before ingestion. This page describes the offline transfer envelope. `docs/contracts/openapi.yaml` remains the authority for `SourceRecord`, `Layer`, and `MetricValue`; the envelope embeds those objects without redefining their fields. No HTTP route ingests an artifact.

## Exact envelope

JSON object with exactly these top-level keys; unknown keys fail v1 validation:

| Field | Required type and meaning |
|---|---|
| `schema_version` | Literal `1.0.0` |
| `artifact_version` | Nonempty string; sample `synthetic-1` |
| `synthetic` | Literal `true` for the current gate |
| `area_id` | Literal `demo-area-01` for the synthetic, non-H3 fixture |
| `geometry` | `null` for this synthetic fixture; no claimed coverage geometry |
| `track`, `frame`, `orbit` | `151`, `72`, `descending` |
| `acquisitions` | Exactly two ordered objects, before and after, with exactly `source_id`, `acquired_at` (UTC Z), `processing_version`, `polarizations` (`["HH","HV"]`), `raster_crs` (`EPSG:4326`), `valid_pixel_count` (`0`); sample endpoints 2026-01-19 and 2026-06-24 |
| `asset` | Exactly `path` (sibling CSV file, no traversal), `format` (`CSV`), `sha256` (digest of file bytes) |
| `classification` | Exactly `{ "class": "Unknown", "score": null, "reason_codes": ["NO_VALID_PIXELS"], "qa_status": "synthetic_test_only" }` |
| `source_records` | Two canonical `SourceRecord` objects, same IDs, dates, version, track/frame as acquisitions; `live_tested: false` |
| `layer` | One canonical `Layer` object, source IDs match; analyst-only, `restricted_until_review`, `Unknown` |
| `metric_value` | One canonical `MetricValue` object, area/source IDs match; `radar_candidate_change`, low/high/confidence `null`, `Unknown` |

Sample payload: [synthetic_radar_manifest.json](../shared/fixtures/synthetic_radar_manifest.json) and its SHA-256 checked [CSV](../shared/fixtures/synthetic_radar_features.csv). The CSV contains no valid pixels. The source names, endpoints, CRS, and version labels are synthetic contract material, not proof of downloaded or paired NISAR scenes. The source-reported 20 Jan–17 Jun 2026 gap is not filled.

## Acceptance and transfer

Run `.venv/Scripts/python.exe -m scripts.ingest_radar_artifact shared/fixtures/synthetic_radar_manifest.json` from repo root. `backend/tests/test_radar_artifact.py` checks acceptance and refusal of real marker, version mismatch, checksum mismatch, public role, invented numeric value, candidate class, and gap date. The validator reads only the manifest and sibling asset, validates embedded objects against canonical OpenAPI schemas, and returns a small summary. It does not insert database rows, publish tiles, serve files, process rasters, or change the active run.

For a real B/C handoff, open a contract review before changing this validator. The review must establish a stable H3 r9 area ID and valid WGS84 geometry, raster source CRS and valid-pixel footprint, actual granule IDs and UTC acquisition times, collection/product version and CRID, calibration/unit meaning, nodata mask, checksum per file, source rights, run and parameter IDs, QA status, score/threshold provenance, and reason codes. A model anomaly score is not a calibrated probability of damage. Unknown remains null. B reviews polarization and version interpretation; C reviews feature/classification semantics. A accepts only reviewed, licensed, authorized area-level derivatives through an offline transactional ingestion path. Public release requires the separate suppression and review policy in `docs/07_SECURITY_PRIVACY_AND_RBAC.md`.
