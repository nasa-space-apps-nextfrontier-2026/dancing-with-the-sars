# 32 · Frontend-aligned backend integration

Status: 15 November 2026. Integration branch: `feature/m4-frontend-backend-integration`.

## Source-of-truth audit

The current UI source is the Cesium implementation merged to `dev` by PR #33 (`0edc0dd`), primarily under `frontend/src/features/map/`. The older light prototype is archived and was not used to infer backend requirements.

The application has one authenticated React screen rather than ten routed pages. `App.tsx` restores the cookie session and renders either the sign-in view or `MapScreen`. Map, Alerts, Areas and Sources are in-screen panels. The latter three were placeholders in PR #33 and now render released data or explicit empty states.

| UI surface | Required data | Backend source | Empty/unavailable behaviour |
|---|---|---|---|
| Sign-in and account menu | Session, role, scopes, CSRF token | `/session`, `/roles` | Sign-in error; labelled local demo option only when the server is unreachable |
| Incident ranking | Ranked incidents, named factors, ranges, unknowns | `/incidents`, `/map/context` | Empty scoped list; no fabricated ranking |
| Incident detail | Insights, recommendations, damage candidates, population context | `/incidents/{id}`, `/areas/{id}/damage`, `/areas/{id}/people` via `/map/context` | Unknown evidence and per-domain unavailability |
| Satellite timeline | Released acquisitions, product name, missing intervals | `/layers`, `/layers/{id}/timeseries` metadata via `/map/context` | Whole-screen “No released observations”; missing is not rendered as no change |
| Map overlays | Scoped H3 centroids, damage candidates, alerts, population | `/map/context`; raster tiles remain `/layers/{id}/tiles/...` | Absent layers stay empty and are listed in `unavailable` |
| Alerts | Released fire and possible-power-loss alerts | `/alerts` via `/map/context` | Empty scoped alert list |
| Areas | Incident AOIs allowed by `area_scopes` | `/incidents` via `/map/context` | Empty scoped area list |
| Sources | Provenance attached to released insights and alerts | Incident details and alerts | Empty provenance state |
| Facilities, routes, shelters | Reviewed operational datasets | Existing contracted endpoints | Explicitly unavailable; never substituted with sample operational claims |
| Budget | Low/high planning range, assumptions and limitations | `/areas/{id}/budget` via `/map/context` | Omitted when no reviewed output exists |
| 3D buildings | Scoped GeoJSON, height ranges and cell-derived candidate class | `/buildings` | Not loaded until an authorized bounding-box request succeeds |

## API composition

`GET /api/v1/map/context` is an authenticated `analyst+` composition endpoint for the current map load. Optional `area_id` uses the existing area-scope authorization and `limit` is restricted to 1–100. Its `FrontendMapBundle` contract contains existing contract objects rather than a second scientific model:

- `IncidentList` and per-incident `IncidentDetail`.
- `LayerList` and per-area `DamageList`.
- `AlertList`, population `MetricList` objects and `Budget` objects.
- authenticated generalized H3 cell centres for display.
- a keyed `unavailable` object for inputs that are not loaded.

The service reads only the existing PostGIS-backed services. `data/published`, the PR #21 JSON Store and `PUBLISHED_DIR` are not API fallbacks. Public map publication remains hard-suppressed.

## Frontend integration policy

- A session with `synthetic: false` calls `/map/context` and never falls back silently to the fixture.
- A session with `synthetic: true` may load `frontend/public/sample/civisar-3d-sample.json`; the UI shows the **Sample data** badge.
- Missing evidence stays absent or Unknown. A failed real request becomes an error state.
- Candidate surface change is not relabelled as confirmed damage.
- Fire and possible-power-loss markers use only released, scoped alert records.
- Routes, shelters and facilities stay empty until their validated sources exist.

## Database relationships used

The integration reuses migrations 0001–0006: `areas` provides H3 hierarchy and geometry; `radar_artifacts` owns acquisition and processing metadata; `radar_area_results` belongs to one artifact and one area; `metric_values` carries ranged, sourced evidence; `alerts` carries generalized released events; and `agent_runs`, `agent_incidents`, `agent_recommendations`, `agent_insights`, `agent_budgets` and `agent_buildings` store reviewed derived outputs. Session, access, reviews, audit and job tables retain their existing security roles.

No live database operation, ingestion, migration execution or empirical validation was performed while implementing this integration.

## Remaining limitations

- Real NISAR artifacts and agent outputs must be loaded and validated before the real map can display them.
- Facilities, roads, closures, shelters, population and night-light inputs remain independently availability-gated.
- Live PostGIS integration requires a disposable database through `CIVISAR_TEST_DATABASE_URL`; unit/security stand-ins are not equivalent.
- Public release requires artifact-bound approval and the outstanding humanitarian protection review.
- Shared multi-worker session, revocation and login-rate-limit state is still required for production deployment.
