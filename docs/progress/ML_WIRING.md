# ML wiring: how the ML outputs reach the API

14 November 2026. Connects Udula's NISAR damage table and Thanoban's night-light and fire models to the backend. Follows [21](../21_ML_BACKEND_FRONTEND_INTEGRATION.md): the API never computes anything per request, it only reads small published files.

## Flow

```text
damage_cells.parquet (Udula, restricted)  ─┐
bm_history.csv.gz (Black Marble, Colab)   ─┼─> python -m worker.main --publish  ->  data/published/*.json  ->  API
FIRMS 7-day public files (--fires)        ─┘     (worker/publish.py)               (backend/app/services/published.py)
```

```text
python -m worker.main --publish --damage <damage_cells.parquet> --history <bm_history.csv.gz> [--fires] [--out data/published]
```

Outputs (outside Git, `data/` is ignored): `damage.json` (per H3 r9 cell, contract `DamageList` fields plus label), `values.json` (`MetricValue` anomaly scores), `alerts.json` (`AlertDetail`: possible power loss, fire detected), `manifest.json` (source freshness and failures). A missing input is recorded as unavailable; nothing is invented.

## API endpoints now backed by real data

| Endpoint | Roles | Returns |
|---|---|---|
| `GET /areas`, `/areas/{id}/damage`, `/areas/{id}/values` | analyst+ | damage candidate class, reason codes, run id; anomaly score as a `MetricValue` with evidence label |
| `GET /alerts`, `/alerts/{id}` | analyst+ | possible power loss (both satellites = 2 independent sources, one = low confidence) and fire detected; `cause` is always "not determined" |
| `GET /status` | public | source freshness and failure text from the manifest |
| `GET /public/map` | public | suppressed unless a person sets `PUBLIC_RELEASE_APPROVED=true`; then only delayed H3 r8 cells with at least 3 candidate cells, with bucketed counts (3-5, 6-10, 11+), never r9 ids or scores |

## Safety gates (all tested in `backend/tests/test_ml_wiring.py`)

- Radar results are withheld until 72 hours after the last pass (`release_at`), for every role.
- Area scopes are enforced per cell (r9 id or its r8 parent); alerts outside the caller's scope return 404.
- No public output without human approval; no exact counts or cell ids in public output.
- Responses are checked against the OpenAPI schemas (`DamageList`, `MetricList`, `AlertList`, `AreaList`, `PublicMap`, `Status`).

## Findings and open items for Rashiru

1. **Permission change to review:** `permissions.allowed` now treats the scope `*` as "all areas" (needed because the damage areas are thousands of H3 cells). Assign it only to named analysts in `.env`.
2. `MetricValue.confidence` must be a number in the contract, but the model's confidence is a text class (low, medium, high). It is sent as null and written in `limitations`. Decide at H2.
3. The `/areas/{id}/damage` item has no evidence label (the contract forbids extra fields); the label is on the matching `/values` item. Extend the contract if the frontend wants it in one call.
4. Fire alerts need the `h3` package in the worker environment (`worker.Dockerfile` installs backend requirements only); damage tables need `pandas` and `pyarrow` for `.parquet`.
5. Alert `rings`, `facilities`, `services` and `route_options_url` are empty until the people, facility and route functions exist.
6. The frontend has not been wired; the typed client in `frontend/src/services` still needs these endpoints.
