# CIVISAR frontend

> **UI changed (15 Nov 2026, Thanoban):** the UI source of truth is now the dark 3D map mockup `docs/design/civisar-3d-map-mockup.html` (spec: `docs/26_3D_MAP_UI_AND_FRONTEND.md`). The old light prototype is archived in `docs/design/archive/`. MapLibre was replaced by CesiumJS.

## Run

```bash
npm install
npm run dev        # login-free, labelled synthetic preview at http://127.0.0.1:5173
npm run dev:auth   # normal cookie-session authentication
```

- **Preview is development-only.** It never authenticates or opens protected real-data endpoints; production builds retain the session gate. `npm run dev:auth` calls `POST /api/v1/session` through the backend proxy on :8000.
- **Cesium token (free):** put `VITE_CESIUM_ION_TOKEN=...` in `frontend/.env.local` (git-ignored), or paste it in the box the app shows. Without it the map still works: flat ground, no 3D buildings.
- Checks: `npm run lint`, `npx tsc -b`, `npm test`.

## Layout of the code

| Path | What |
| --- | --- |
| `src/app/App.tsx` | Session check and the sign-in gate. |
| `src/features/signin/SignIn.tsx` | Sign-in screen (same dark glass design). |
| `src/features/map/MapScreen.tsx` | Top bar, rail, dock, token box; owns UI state and drives the engine. |
| `src/features/map/panels.tsx` | Incident panel (Summary, Impacts, Shelters, Power, Insights), building and shelter detail, ranking, decision assistant, budget, layers, legend. |
| `src/features/map/engine.ts` | All CesiumJS code: globe, terrain, OSM buildings, overlays, fire/damage effects, OSRM road routes, camera flights, 2D/3D/split. |
| `src/features/map/analysis.ts` | Pure helpers (distances, ranges, impacts, route stats). Unit-tested. |
| `src/services/api.ts` | Session API and map data. Real sessions load the released/scoped `/map/context` bundle; explicitly synthetic sessions load `public/sample/civisar-3d-sample.json`. |
| `src/styles.css` | Tokens and components copied from the mockup. |

## Build rules

- Match the mockup: same layout zones, wording, tokens. Colour only for evidence, damage class, route status, fire and power.
- Evidence labels are exactly Observed, Reported, Corroborated, Unknown. Ranges, not single numbers. Never write "safe". "Possible power loss", not "blackout". Routes and damage are "not verified" / "candidate".
- Every map layer must appear in 2D, 3D and split view.
- Keep the "Sample data" badge while sample data is shown. No vehicle, convoy or phone tracking.
- Cesium is pinned to 1.121.0 (engine 11.0.0, widgets 8.0.0, zip.js 2.7.54 via `overrides`) because newer transitive versions break the Vite build. Change them together.
- Branch `feature/m4-<name>` from `dev`, PR into `dev`.
