# CIVISAR frontend

> **UI changed (15 Nov 2026, Thanoban):** the product is now called **RescueForce**. The UI sources of truth are the landing mockup `docs/design/rescueforce-landing-mockup.html` and the dark 3D map mockup `docs/design/civisar-3d-map-mockup.html` (spec: `docs/26_3D_MAP_UI_AND_FRONTEND.md`). The old light prototype is archived in `docs/design/archive/`. MapLibre was replaced by CesiumJS.

## Run

```bash
npm install
npm run dev        # login-free, labelled synthetic preview at http://127.0.0.1:5173
npm run dev:auth   # normal cookie-session authentication
```

- **Routes:** `/` is the RescueForce landing page (3D Earth story), `/map` is the dashboard, `/signin` is the sign-in page. Every "Try" / "Open RescueForce" link goes to `/map`.
- **Public demo, sign-in for real data.** The landing page and the dashboard with the labelled sample data are public (no account needed, 15 Nov 2026). Real data always needs sign-in (doc 07, CLAUDE.md: login required): the dashboard menu has "Sign in for real data"; once signed in, the dashboard loads the released, area-scoped `/api/v1/map/context` bundle and shows its errors instead of falling back to sample data.
- **Cesium token (free):** put `VITE_CESIUM_ION_TOKEN=...` in `frontend/.env.local` (git-ignored); set the same variable in the deploy build. Visitors are never asked for it. Without it the map works on flat ground; developers can add one from the dashboard's ⋯ menu.
- **Data:** signed out, the labelled sample file ("Sample data" badge); signed in, `/api/v1/map/context`. Inputs the backend lists as unavailable (facilities on the map, roads, night lights) show as Unknown, never 0. The Sources panel reads `/api/v1/sources`.
- **No external routing.** Route and shelter lines are sample drawings (routes and shelters are demo-only, doc 07); no public routing server is called (doc 03). Sample shelters use generic names, never real sites.
- Checks: `npm run lint`, `npx tsc -b`, `npm test`.

## Layout of the code

| Path | What |
| --- | --- |
| `src/app/App.tsx` | Routes: `/` landing, `/map` dashboard. |
| `src/app/usePageStyle.ts` | Loads each page's own stylesheet only while it is mounted (the two designs share class names). |
| `src/features/landing/` | Landing page: `Landing.tsx`, markup, `landing.css`, and `landingScene.js` (three.js Earth, GSAP scroll story, Lenis smooth scroll, fire and smoke). Ported from `docs/design/rescueforce-landing-mockup.html`. |
| `src/features/map/MapScreen.tsx` | Top bar, rail, dock, token box; owns UI state and drives the engine. |
| `src/features/map/panels.tsx` | Incident panel (Summary, Impacts, Shelters, Power, Insights), building and shelter detail, ranking, decision assistant, budget, layers, legend. |
| `src/features/map/engine.ts` | All CesiumJS code: globe, terrain, OSM buildings, overlays, fire/damage effects, sample route lines, camera flights, 2D/3D/split. |
| `src/features/map/analysis.ts` | Pure helpers (distances, ranges, impacts, route stats). Unit-tested. |
| `src/services/api.ts` | Session API and map data. Signed-in sessions load the released/scoped `/map/context` bundle; signed out loads `public/sample/civisar-3d-sample.json`. |
| `src/features/signin/SignIn.tsx` | Sign-in page for real data; "Continue with sample data" goes back to the public dashboard. |
| `src/styles.css` | Tokens and components copied from the mockup. |

## Build rules

- Match the mockup: same layout zones, wording, tokens. Colour only for evidence, damage class, route status, fire and power.
- Evidence labels are exactly Observed, Reported, Corroborated, Unknown. Ranges, not single numbers. Never write "safe". "Possible power loss", not "blackout". Routes and damage are "not verified" / "candidate".
- Every map layer must appear in 2D, 3D and split view.
- Keep the "Sample data" badge while sample data is shown. No vehicle, convoy or phone tracking.
- Cesium is pinned to 1.121.0 (engine 11.0.0, widgets 8.0.0, zip.js 2.7.54 via `overrides`) because newer transitive versions break the Vite build. Change them together.
- Branch `feature/m4-<name>` from `dev`, PR into `dev`.
