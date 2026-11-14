# ML wiring: how the ML outputs reach the API

14 November 2026. This document originally recorded the JSON publication design introduced by commit `e821448` and merged through PR #21. That design connected Udula's NISAR damage table and Thanoban's night-light and fire models to the backend through generated `data/published/*.json` files.

## Current M3 status (15 November 2026)

- PostGIS is the sole authoritative real-data API store. PR #21's JSON-backed API store, `PUBLISHED_DIR` fallback and wildcard `*` area scope were not retained.
- The current `GET /public/map` endpoint is permanently suppressed. `PUBLIC_RELEASE_APPROVED=true` cannot enable publication, and suppressed requests return without constructing a database engine or querying PostGIS.
- Before any future public release system can be enabled, it needs immutable artifact-bound approval, licence and QA checks, high-risk-cell review, spatial-cohort controls and snapshot-differencing analysis.
- H3 r8 aggregation and a three-candidate minimum are not sufficient humanitarian protection.

The remaining flow, endpoint table and findings below preserve the original PR #21 design for historical traceability. They are **superseded and not descriptions of current M3 runtime behavior**.

## Historical PR #21 JSON publication flow (superseded)

```text
damage_cells.parquet (Udula, restricted)  ─┐
bm_history.csv.gz (Black Marble, Colab)   ─┼─> python -m worker.main --publish  ->  data/published/*.json  ->  API
FIRMS 7-day public files (--fires)        ─┘     (worker/publish.py)               (backend/app/services/published.py)
```

```text
python -m worker.main --publish --damage <damage_cells.parquet> --history <bm_history.csv.gz> [--fires] [--out data/published]
```

Outputs (outside Git, `data/` is ignored): `damage.json` (per H3 r9 cell, contract `DamageList` fields plus label), `values.json` (`MetricValue` anomaly scores), `alerts.json` (`AlertDetail`: possible power loss, fire detected), `manifest.json` (source freshness and failures). A missing input is recorded as unavailable; nothing is invented.

## Historical PR #21 endpoint design (superseded)

| Endpoint | Roles | Returns |
|---|---|---|
| `GET /areas`, `/areas/{id}/damage`, `/areas/{id}/values` | analyst+ | damage candidate class, reason codes, run id; anomaly score as a `MetricValue` with evidence label |
| `GET /alerts`, `/alerts/{id}` | analyst+ | possible power loss (both satellites = 2 independent sources, one = low confidence) and fire detected; `cause` is always "not determined" |
| `GET /status` | public | source freshness and failure text from the manifest |
| `GET /public/map` | public | **Superseded behavior:** PR #21 proposed suppression unless a person set `PUBLIC_RELEASE_APPROVED=true`, followed by delayed, bucketed H3 r8 output. Current M3 is always suppressed and cannot be enabled by that setting. |

## Historical PR #21 safety gates (superseded)

- Radar results are withheld until 72 hours after the last pass (`release_at`), for every role.
- Area scopes are enforced per cell (r9 id or its r8 parent); alerts outside the caller's scope return 404.
- The original design required human approval and removed exact counts and r9 identifiers. Current M3 publishes no public radar cells at all; future approval must be artifact-bound and complete the additional humanitarian review listed above.
- Responses are checked against the OpenAPI schemas (`DamageList`, `MetricList`, `AlertList`, `AreaList`, `PublicMap`, `Status`).

## Historical findings and open items for Rashiru

1. **Superseded permission change:** PR #21 treated `*` as "all areas" for thousands of H3 cells. Current M3 did not retain this behavior; wildcard scope grants no access.
2. `MetricValue.confidence` must be a number in the contract, but the model's confidence is a text class (low, medium, high). It is sent as null and written in `limitations`. Decide at H2.
3. The `/areas/{id}/damage` item has no evidence label (the contract forbids extra fields); the label is on the matching `/values` item. Extend the contract if the frontend wants it in one call.
4. Fire alerts need the `h3` package in the worker environment (`worker.Dockerfile` installs backend requirements only); damage tables need `pandas` and `pyarrow` for `.parquet`.
5. Alert `rings`, `facilities`, `services` and `route_options_url` are empty until the people, facility and route functions exist.
6. The frontend has not been wired; the typed client in `frontend/src/services` still needs these endpoints.
