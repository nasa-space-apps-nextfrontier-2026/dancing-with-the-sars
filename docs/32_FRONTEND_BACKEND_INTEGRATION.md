# 32 · Frontend/backend integration

Status: 15 November 2026. Integration branch: `feature/m4-frontend-backend-dev-sync`. Dev base: `0e3bf34b2c14a54a20ed97f542655e1ed775b8ef` (PR #43, U-06 PostGIS endpoints).

This document describes the current Cesium application under `frontend/src/features/map/`. The archived HTML prototype and its former ten-view route inventory are not the current frontend.

## Verification vocabulary

- **IMPLEMENTED** — code and a contract exist, but this label alone does not establish runtime behaviour.
- **AUTOMATED TEST PASSED** — exercised with isolated frontend or backend tests.
- **LIVE HTTP VERIFIED** — checked against the local running HTTP services.
- **MANUAL TEST PENDING** — requires a developer to inspect the real browser UI; no visual claim is made.
- **BLOCKED BY DATA** — the UI or API preserves an unavailable state because reviewed source data is absent.

Code implementation, integration testing, scientific validation, and production readiness are separate acceptance gates.

## Local development modes

### Login-free synthetic preview

From `frontend/` run:

```powershell
npm run dev
```

The script starts Vite in `preview` mode at `http://localhost:5173`. `runtime.ts` enables preview only when Vite reports a development build. `App.tsx` then creates an explicitly synthetic demo session and opens the current Cesium dashboard without calling the session endpoint or rendering the sign-in screen. `api.mapData` loads `/sample/civisar-3d-sample.json`, and the header displays **Sample data**.

Preview mode does not authenticate with FastAPI and cannot turn protected endpoints into public endpoints. The local backend continues to return `401` for an unauthenticated `/api/v1/map/context` request. FastAPI session validation, CSRF, RBAC, area scope and release policy are unchanged.

The optional `VITE_CIVISAR_DEV_PREVIEW=true` setting has the same local-development effect. It is not a security control: `import.meta.env.DEV` must also be true, so a production build cannot enable the preview bypass with this variable.

### Normal authenticated mode

Start the backend from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Then start the frontend:

```powershell
cd frontend
npm run dev:auth
```

Ensure `VITE_CIVISAR_DEV_PREVIEW` is unset or false. Vite proxies `/api` to `VITE_API_PROXY_TARGET`, defaulting to `http://127.0.0.1:8000`. `VITE_API_BASE_URL` may select a different non-secret API base. The normal UI restores the HttpOnly cookie session through `GET /session`; sign-in and sign-out continue to use the custom cookie and CSRF implementation.

Do not place passwords, session tokens, database credentials or other secrets in `VITE_*` variables. Any Cesium token used in the browser must be an appropriately restricted public client token, not a privileged credential.

## Current frontend surfaces

The application has one session-gated React shell and one Cesium dashboard rather than separate routed pages. Map, Alerts, Areas and Sources are in-screen panels.

| Frontend feature | React/API consumer | Backend contract or source | Status | Verification and gap |
|---|---|---|---|---|
| Session restore, sign-in and sign-out | `App.tsx`, `SignIn.tsx`, `api.ts` | `GET/POST/DELETE /session`; `GET /roles` | IMPLEMENTED; AUTOMATED TEST PASSED | Cookie, CSRF, rate-limit and RBAC tests pass. Browser sign-in remains MANUAL TEST PENDING. |
| Login-free preview | `runtime.ts`, `App.tsx`, `api.mapData` | Labelled bundled fixture only | IMPLEMENTED; AUTOMATED TEST PASSED | Test proves no session fetch and no sign-in view. Browser appearance is MANUAL TEST PENDING. |
| Cesium 2D, 3D and split map | `MapScreen.tsx`, `engine.ts` | Bundle centroids, raster `tile_url`, external basemaps | IMPLEMENTED | Browser/WebGL behaviour is MANUAL TEST PENDING. A Cesium token affects terrain/buildings, not auth. |
| Incident ranking and selection | `panels.tsx`, `analysis.ts` | `/incidents` and `/incidents/{id}` composed by `/map/context` | IMPLEMENTED; AUTOMATED TEST PASSED | Scoped/released service behaviour is tested with isolated database stand-ins. No live PostGIS verification. |
| Radar acquisition timeline | `mapData.ts`, `MapScreen.tsx`, `timeline.ts` | `/layers` metadata and `/layers/{id}/timeseries`, composed by `/map/context` | IMPLEMENTED; AUTOMATED TEST PASSED | Selection and playback use released acquisition timestamps only; missed intervals remain visible but playback skips them. Playback stops at the end, on manual selection, when data changes and on unmount. Browser synchronization remains MANUAL TEST PENDING. |
| Raster layers and visibility | `engine.ts`, Layers panel | `/layers/{id}/tiles/{z}/{x}/{y}` | IMPLEMENTED; AUTOMATED BACKEND TEST PASSED | Authorized tile access is covered in backend tests; rendered tiles are MANUAL TEST PENDING and BLOCKED BY DATA when no reviewed raster exists. |
| Candidate surface change | `mapData.ts`, map engine and incident panel | `/areas/{id}/damage`, composed by `/map/context` | IMPLEMENTED; AUTOMATED TEST PASSED | Results remain candidates with Unknown evidence; no confirmed-damage claim. Real artifacts are BLOCKED BY DATA. |
| Secondary-sensor corroboration | `mapData.ts`, incident panel | Released damage reason codes | PARTIALLY INTEGRATED | The UI maps supported reason codes; empirical corroboration is BLOCKED BY DATA and not scientifically verified. |
| Alerts | Alerts panel | `/alerts` composed by `/map/context`; `/alerts/{id}` remains available | IMPLEMENTED; AUTOMATED TEST PASSED | Only released, scoped fire or possible-power-loss alerts are included. Browser panel is MANUAL TEST PENDING. |
| Areas | Areas panel | Scoped incident AOIs in `/map/context`; `/areas` remains available | IMPLEMENTED; AUTOMATED TEST PASSED | The current panel derives its list from map incidents, not a second frontend request. Browser panel is MANUAL TEST PENDING. |
| Sources | `SourcesPanel.tsx`, typed `api.sourceCatalogue` | Cursor-paginated `GET /sources` | IMPLEMENTED; AUTOMATED TEST PASSED; LIVE HTTP VERIFIED | Shows provider, dataset, acquisition dates, maturity, processing, provenance, coverage, licence, access method and limitations. Loading, empty and typed error states are tested. Browser rendering remains MANUAL TEST PENDING. |
| Population context | `mapData.ts`, incident/power panels | `/areas/{id}/people`, composed by `/map/context` | IMPLEMENTED; AUTOMATED TEST PASSED; BLOCKED BY DATA | Missing population remains Unknown; reviewed population data is not loaded. |
| Service status | Existing backend area services | `/areas/{id}/services` | BACKEND IMPLEMENTED; FRONTEND NOT INTEGRATED; BLOCKED BY DATA | The map bundle does not currently include water, electricity, health or communications service records. |
| Facilities | Existing backend area facilities | `/areas/{id}/facilities` | BACKEND EMPTY-STATE IMPLEMENTED; BLOCKED BY DATA | No facility is presented as operational without a validated dataset. |
| Shelters and routes | Existing contracts and empty map arrays | `/shelters`, `/routes` | BLOCKED BY DATA | No availability, capacity or safety claim is fabricated. Current synthetic fixture is illustrative and labelled. |
| Insights and decision assistance | Incident detail panels | Reviewed incident insights and recommendation composed by `/map/context` | IMPLEMENTED; AUTOMATED TEST PASSED; BLOCKED BY DATA | Missing agent outputs produce explicit unavailability. No AI narrative substitutes for linked evidence. |
| Budget assistance | Budget panels | `/areas/{id}/budget`, composed by `/map/context` | IMPLEMENTED; AUTOMATED TEST PASSED; BLOCKED BY DATA | Ranges, assumptions and limitations are preserved; no value is presented as a quote. |
| 3D buildings | `engine.ts` | `/buildings?bbox=...` | PARTIALLY INTEGRATED; BLOCKED BY DATA | Backend scope and release rules are tested. Browser load and validated building inputs remain pending. |
| Public map | No current dashboard dependency | `/public/map` | LIVE HTTP VERIFIED as suppressed | Publication is hard-suppressed; it is not enabled by preview mode. |

## API integration contract

The frontend's direct API calls are deliberately small:

| Request | Authentication | Frontend handling | Verified result |
|---|---|---|---|
| `GET /api/v1/session` | Cookie session | Restores normal authenticated UI; failure shows sign-in | AUTOMATED TEST PASSED |
| `POST /api/v1/session` | Credentials in JSON request body | Establishes HttpOnly cookie session | AUTOMATED BACKEND TEST PASSED |
| `DELETE /api/v1/session` | Cookie plus `X-CSRF-Token` | Revokes session and returns to sign-in | AUTOMATED BACKEND TEST PASSED |
| `GET /api/v1/sources[?cursor=…]` | Public or cookie session | Loads every approved catalogue page; renders metadata and limitations without inventing records | AUTOMATED TEST PASSED; LIVE HTTP VERIFIED as `200` synthetic catalogue in local demo mode |
| `GET /api/v1/map/context?limit=100` | Analyst-or-higher scoped session | Converts the bundle into the unchanged Cesium view model; never falls back to a fixture | AUTOMATED FRONTEND/BACKEND TEST PASSED; unauthenticated LIVE HTTP VERIFIED as `401` |
| `GET /api/v1/health` | Public | Health status | LIVE HTTP VERIFIED as `200` with `synthetic: true` in the running local backend |
| `GET /api/v1/public/map` | Public, hard suppressed | Not used by the dashboard | LIVE HTTP VERIFIED as `200`, `suppressed: true` |

`GET /map/context` accepts optional `area_id` and `limit` from 1 through 100. It composes the existing PostGIS-backed incident, incident detail, layer, damage, alert, population and budget services. Its `unavailable` map records absent domains; it never replaces failed real-data calls with illustrative values. Database failure is a typed `503`. Frontend request tests preserve typed `401`, `403`, `422` and `503` errors.

The OpenAPI contract contains 45 operations, including independent area, source, service, facility, route and shelter routes. Contract existence does not mean the current dashboard directly calls each route or that its external data is loaded.

## Automated and live verification

Results from this integration pass:

- Backend full suite on the dev-synchronized branch: `273 passed, 1 skipped, 4 warnings`.
- Focused newly integrated agent/map-context suite: `9 passed, 1 warning`.
- Frontend suite: `24 passed` across 9 files.
- Frontend ESLint: passed with zero warnings.
- TypeScript project check: passed.
- Frontend production build: passed; Vite reports the existing large-chunk advisory for the Cesium bundle.
- Local frontend `/`: HTTP `200`.
- Local backend `/api/v1/health`: HTTP `200`, synthetic mode explicitly true.
- Local backend `/api/v1/sources`: HTTP `200`, with every returned record explicitly synthetic in demo mode.
- Unauthenticated `/api/v1/map/context`: HTTP `401` with `UNAUTHENTICATED`.
- `/api/v1/public/map`: HTTP `200` with no layers and `suppressed: true`.

The skipped test requires a disposable PostGIS instance through `CIVISAR_TEST_DATABASE_URL`. These results do not establish live Supabase/PostGIS integration or empirical NISAR correctness. One warning is the existing Starlette TestClient/httpx deprecation warning; three warnings come from the existing `worker.main` run-module tests importing that module before executing it through `runpy`.

## Manual browser verification checklist

Windows browser automation was stopped because the automation safety system could not establish the current Chrome URL confidently. It was not retried or circumvented. Every item below is therefore **MANUAL TEST PENDING**.

1. **Default load:** run `npm run dev` and open `http://localhost:5173`; expect the Cesium dashboard, not sign-in or a redirect loop.
2. **Synthetic disclosure:** expect the **Sample data** badge and a demo account label; no fixture value should appear as real NISAR or humanitarian evidence.
3. **Cesium initialization:** choose a restricted public Cesium token or “Continue without 3D buildings”; expect a map canvas or an honest 2D fallback banner, never a blank screen.
4. **2D mode:** press 2D; expect the 2D map container and existing overlays without a crash.
5. **3D mode:** press 3D; expect the globe/map. Without a token, expect flat ground and the explanatory banner.
6. **Split mode:** press Split; expect synchronized 2D and 3D containers without clipping.
7. **Area selection:** open Areas and select an available area; expect selection/focus only for visible scoped data.
8. **Incident selection:** choose an incident or “Fly to top incident”; expect the detail panel and camera focus to update together.
9. **Radar timeline:** move the satellite-pass slider, then use Play and Pause; expect date, candidate layers and selected acquisition to synchronize. Playback must visit released acquisitions only, leave missing intervals visible, and stop safely at the end.
10. **Layer visibility:** toggle damage, corroboration, fire, night, population and other available layers; expect only supported layers to appear and missing layers to remain unavailable.
11. **Panels:** open and close Alerts, Areas and Sources; expect released fixture content or explicit empty states, with no inert controls.
12. **Loading/unavailable states:** in authenticated mode, exercise an unavailable backend or empty scoped result; expect loading to resolve to typed error, Unknown, or unavailable—not synthetic fallback or false zero.
13. **Console:** inspect DevTools Console; expect no uncaught React, Cesium or network exceptions. Record token/basemap warnings separately.
14. **Network:** inspect DevTools Network; preview should load the labelled sample and must not successfully read protected `/api/v1/map/context`. Authenticated mode should send cookies and receive the contract bundle or a typed `401/403/422/503`.
15. **Responsive layout:** check desktop, tablet and mobile widths; expect accessible navigation and no controls hidden by overlap or horizontal clipping.
16. **Normal auth:** run `npm run dev:auth`; expect session restore or sign-in. After a valid isolated login, expect `/map/context` to load only released data inside the user's area scope.

## Data and production limitations

- Real NISAR artifacts and reviewed agent outputs must be ingested and scientifically validated before the real map can display them.
- Facilities, roads, closures, shelters, population, service status and night-light inputs remain independently availability-gated.
- Live PostGIS integration requires a disposable database; isolated service stand-ins are not equivalent.
- Public release requires artifact-bound approval, licence/QA review, high-risk-cell review, spatial cohort controls and snapshot-differencing analysis. It remains hard-suppressed.
- Shared multi-worker session, revocation and login-rate-limit storage is still required for production.
- Browser/WebGL interaction, visual fidelity, responsive layout and authenticated browser E2E remain manually unverified.
- Service/facility/route/shelter domains are not composed into `/map/context`; they remain independently availability-gated.

## Final feature-completion audit

| Visible feature | Classification | Basis |
|---|---|---|
| Login-free preview and synthetic disclosure | IMPLEMENTED — BROWSER VERIFICATION PENDING | Boot isolation and production guard are automated; appearance is manual. |
| Normal session/sign-in/sign-out | IMPLEMENTED — BROWSER VERIFICATION PENDING | Backend auth, CSRF and session tests pass. |
| 2D, 3D and split map modes | IMPLEMENTED — BROWSER VERIFICATION PENDING | Handlers and engine integration exist; WebGL behavior is manual. |
| Satellite/street basemap, focus, fly, orbit and reset controls | IMPLEMENTED — BROWSER VERIFICATION PENDING | All visible controls have handlers; visual behavior is manual. |
| Incident ranking, selection and area navigation | IMPLEMENTED — BROWSER VERIFICATION PENDING | Component interaction and backend scope tests pass. |
| Radar date selection and safe playback | IMPLEMENTED — BROWSER VERIFICATION PENDING | Automated playback skips missing intervals, cleans up timers and stops at the end. |
| Layer visibility and legend | IMPLEMENTED — BROWSER VERIFICATION PENDING | State handlers exist; real raster rendering is also BLOCKED BY MISSING DATA. |
| Alerts panel | IMPLEMENTED — BROWSER VERIFICATION PENDING | Released/scoped alert backend tests pass. |
| Sources catalogue | IMPLEMENTED — BROWSER VERIFICATION PENDING | Cursor mapping plus loading, empty, metadata and error states pass automated tests. |
| Incident evidence, insights and budget panels | IMPLEMENTED — BROWSER VERIFICATION PENDING | Bundle mapping and isolated backend integration pass. Real outputs remain BLOCKED BY MISSING DATA. |
| Population and service evidence | BLOCKED BY MISSING DATA | Unknown/unavailable states are implemented; reviewed inputs are absent. |
| Facilities, shelters and routes | BLOCKED BY MISSING DATA | No operational or safety claims are generated without validated inputs. |
| Real NISAR tiles and empirical damage candidates | BLOCKED BY MISSING DATA | Contracts and access controls exist; real artifacts and scientific validation do not. |
| Timeline playback through missing intervals as if observed | NOT IMPLEMENTED | Intentionally excluded: missing acquisitions are not observations. |

## PR preparation status

The original divergent branch remains unchanged at `268faf2`. Its uncommitted work is preserved independently in recovery stash `e4b7ae148098aa42be689e289c5e3d7de947f42a`; the earlier recovery stash `4a8bff7e23b963c6714d6e2a16b0fc3b4d330285` also remains untouched.

The fresh integration branch was initially created directly from `origin/dev` at `146cb4c`. While validation ran, `origin/dev` advanced to `0e3bf34`; a second verified recovery snapshot was created and the branch was fast-forwarded to that commit before the M4 changes were restored. This avoided a wholesale merge of the old divergent M4 branch. The four old M4 commits were handled as follows:

- `ebc9b56`: not cherry-picked. Current dev contains its hardened PostGIS, authentication, audit, radar, geospatial and worker foundations. PR #43 subsequently supplied the U-06 PostGIS agent-output endpoints, migration, loader and tests, so those dev implementations were retained.
- `cf85d97`: not applied; it was line-ending normalization rather than functionality.
- `2d05106`: selectively integrated the authenticated `/map/context` composition, frontend mapping, Cesium radar layers, panels, tests and contract addition.
- `268faf2`: selectively integrated the development-only preview gate and tests.

Current dev supplies the newer source registry, areas, population/facility handlers, alerts, U-05 agents, U-06 publishing and PostGIS endpoints, building/geospatial pipelines, radar/security fixes and hard-suppressed public map. Those implementations were retained. M4 adds the composed `/map/context` service and frontend integration without running migrations or loaders.

The resulting diff contains only the selective M4 integration, tests and documentation; `0006_agent_outputs` is part of the recorded dev base. Authentication, CSRF, RBAC, area scoping, 72-hour release rules and public-map suppression were not weakened. Automated validation passes, while migration execution, live PostGIS, authenticated browser E2E and manual visual checks remain separately unverified.

## Readiness summary

- **Local synthetic demo:** code and automated boot behaviour are ready; manual browser confirmation is pending.
- **Authenticated frontend/backend integration:** contracts and isolated tests pass for the composed bundle, sessions, scope and error handling; authenticated browser E2E and live PostGIS remain pending.
- **Real PostGIS/NISAR:** not ready; disposable PostGIS verification, real inputs and empirical validation are outstanding.
- **Production:** not ready because of the data, humanitarian review, multi-worker security-state and browser/E2E limitations above.
