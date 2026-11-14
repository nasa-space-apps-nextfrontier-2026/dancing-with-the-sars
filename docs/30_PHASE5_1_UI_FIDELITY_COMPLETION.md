# Phase 5.1 UI fidelity continuation

Date: 14 November 2026. Branch: `feature/lead-fullstack-app`. Prototype: `docs/design/civisar-prototype.html`, SHA-256 `ABA74D61000B83956D61CE4A50A1CBDDB03C81C714F433C804FC417122A2D037`. The source prototype was not edited.

## Browser and comparison method

The earlier browser blocker was resolved with installed Chrome and Node 24's WebSocket client. `frontend/scripts/capture-visual.mjs` starts headless Chrome through DevTools, opens the HTTP-served prototype and Vite app, sets DPR 1 and fixed viewport sizes, and captures ten base views plus the main Layers and Alerts panel states. It writes 60 paired states (120 PNGs) and `compare.html` to `docs/visual/phase5_1_current/`. The overlay viewer changes the React opacity over the reference. Its pairs are useful for visual review; a successful capture does not imply a match. The required viewports are 1440×900, 1366×768, 1024×768, 768×1024 and 390×844. The source CSS has breakpoints at 1380 and 1180 pixels; the separate phone showcase is a view, not a responsive replacement for the other nine screens.

Playwright was not present. The online npm install stalled without output; offline npm installation failed with `ENOTCACHED` registry metadata. The Chrome CDP harness avoids a new package dependency. The browser profile is placed in the OS temporary directory so Vite does not watch Chrome's locked cookie database.

Start the servers from the repository root in separate terminals:

```powershell
.\.venv\Scripts\python.exe -m http.server 4174 --bind 127.0.0.1 --directory docs/design
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
cd frontend; npm run dev -- --host 127.0.0.1
```

For authenticated screenshots, configure a **local synthetic test account** through the documented demo-user workflow, then set `CIVISAR_VISUAL_USERNAME` and `CIVISAR_VISUAL_PASSWORD` only in the capture shell. The account needs coordinator role to show Routes and Shelters. Run `node frontend/scripts/capture-visual.mjs` from the repository root, then `node frontend/scripts/verify-visual.mjs` to verify all 60 pairs and their PNG dimensions. No password is stored in the harness, screenshot names or repository. When an account is absent, restricted React views redirect to sign-in and cannot be compared in the same state.

## Exact view inventory and visual findings

The prototype has `main`, `alert`, `area`, `brief`, `routes`, `shelters`, `inspect`, `sources`, `signin`, and `phone` (ten views). All now have React routes and modular screen components. The verified implementation status is below. Each comparison uses a fresh Chrome capture and the same viewport, DPR and light theme. Visual review covered 1440×900 screenshots and the 390×844 main view; the other pairs were captured for comparison, with detailed difference review still pending. At 390px, the reference itself clips its desktop navigation and timeline; the React main view also has mobile clipping and overlap. Thus **visual acceptance remains MAJOR DEVIATION**, not matched.

| View | React component | 1440×900 finding | Status / next action |
|---|---|---|---|
| Main map | `PrototypeMain`, `AreaExplorer`, `MapPanel` | Header, dock, agent panel and lower controls occupy roughly the right regions. The explicitly non-geographic synthetic MapLibre grid renders. Prototype's illustrated geographic map and dense agent cards remain absent. Timeline styling and pass marks differ. | MAJOR DEVIATION · render a safe, reviewed map layer and finish timeline/agent detail without implying synthetic cells have Lebanon coordinates. |
| Alert detail | `PrototypeAlert` | Split map/detail layout exists; real alert callout, rings, facility rows and route overlays have no approved data. | MAJOR DEVIATION · connect an authorized reviewed alert record and exact side-panel components. |
| Area summary | `PrototypeArea` | Card grid and right rail are close in size; typography and detail density differ. Only synthetic range and Unknown evidence are shown. The mini map displays a synthetic grid. | MAJOR DEVIATION · add reviewed services and source rows when contracts support them, then tune spacing. |
| Area brief | `PrototypeBrief` | A4 sheet and print action exist; prototype's report composition and source footnotes are not fully reproduced. | MAJOR DEVIATION · match print layout and verify printed PDF. |
| Routes | `PrototypeRoutes` | Map/detail split and inbound/outbound selector exist; prototype route cards, three alternatives and line geometry cannot be represented with the current contract. | MAJOR DEVIATION · wait for a verified private graph and closures. |
| Shelters | `PrototypeShelters` | Split layout and density selector exist; prototype candidate cards and capacity calculations lack reviewed site dimensions and safety checks. | MAJOR DEVIATION · connect authorized field-checked candidates. |
| Inspector | `PrototypeInspector` | Split layout and tabs exist; building selection, time series and validation cannot be populated without reviewed artifacts. | MAJOR DEVIATION · connect artifact metadata, QA and evidence after ML handoff. |
| Sources | `PrototypeSources` | Six NASA tiles, dataset table, filter and right rail are close in overall geometry. Source recency and citation are intentionally Unknown pending verification. | MINOR DEVIATION for layout; MAJOR DEVIATION for prototype content. Verify source dates and tune table/type. |
| Sign-in | `PrototypeSignIn` | Centered dialog and restricted-content explanation exist; prototype background and secondary SSO state differ. Actual server sign-in is used. | MAJOR DEVIATION · compare modal details and label unavailable SSO explicitly. |
| Phone showcase | `PrototypePhone` | Three phone frames exist, with safe empty states. Prototype's full alert/area/route details are not present. | MAJOR DEVIATION · implement authorized mobile detail content and verify clipping. |

## Component-level difference inventory

| Priority | Reference selector / source | React location | Observed difference and action |
|---|---|---|---|
| P0 | `#v-main .cv-mapsvg`, prototype map helper | `src/components/MapPanel.tsx` | The 1440×848 canvas initially rendered blank because MapLibre's default worker failed to load under Vite. An explicit bundled worker URL fixed grid rendering. The non-geographic synthetic grid still differs fundamentally from the geographic illustration; provide a safe reviewed basemap before calling this matched. |
| P0 | `#v-main .ag`, `.ag-b` | `src/features/prototype/PrototypeMain.tsx` | Prototype uses varied icons, counts and expanded details; React uses Unknown rows. Preserve the structure but populate only reviewed evidence. |
| P1 | `#v-main .cv-time`, `.cv-track` | `src/features/area/AreaExplorer.tsx`, `src/prototype.css` | React has endpoint slider and mode/polarization/opacity controls, but not the original pass marks or play behavior. Do not invent missing NISAR passes. |
| P1 | `.cv-top`, `.cv-tabs`, `.cv-fresh` | `src/app/App.tsx`, `src/prototype.css` | Shared 52px header and SVG icon sprite implemented. Real freshness stays Unknown. React account controls differ from illustrative prototype account. |
| P1 | `#v-area .wrap`, `#v-sources .wrap` | `PrototypeViews.tsx`, `PrototypeSources.tsx` | Major grids reproduced; card details, source-age typography and map artwork remain different. |
| P1 | `#v-alert`, `#v-routes`, `#v-shelters`, `#v-inspect` side rails | `PrototypeViews.tsx` | Correct split pattern but detailed mock data is withheld for accuracy and privacy. Build typed cards against reviewed backend outputs. |
| P2 | `#v-phone .cv-phone` | `PrototypeViews.tsx` | Frame dimensions/styles exist; content and responsive behavior differ. |

The 58 prototype SVG paths were extracted into `frontend/public/prototype-icons.svg` and rendered by `PrototypeIcon.tsx`. No third-party icon package was added. The shared header now uses the prototype's single-row layout. React base views use the original CSS tokens and component classes where practical. The prototype's illustrative coordinates, casualty implications, route alternatives, live source dates and facility status were not copied as real results.

## Interaction, backend and security status

Working: header navigation, theme toggle, sign-in, server session restoration, logout, 401/403 handling, role restriction, main dock toggles, expandable empty agent rows, alert filters, source table filtering/keyboard selection, inspector tabs, route direction selector, shelter density selector, print action, synthetic before/after/change/swipe, HH/HV/HH−HV, opacity, endpoint slider, and API-backed area/source selection. The map zoom controls are explicitly disabled in the synthetic preview, and header search is labelled unavailable. Prototype pass playback, exact map callouts, route picking, shelter selection, phone alert navigation and current-source copy are not implemented. These are not claimed complete.

Backend code and OpenAPI/JSON contracts were not changed. The synthetic radar artifact remains an offline Unknown result. No validated Udula/Thanoban radar outputs, raster URL, real PostGIS migration run or real NISAR pixels were supplied. Phase 6 can integrate reviewed artifacts through existing backend contracts, but this UI is not visually stable enough for release.

## Validation

Frontend build and lint passed. Vitest: 11 passed, including new source filtering and coordinator restriction/navigation tests. Backend pytest: 18 passed. Ruff, planning/OpenAPI/JSON schema validation, scaffold validation, narrow secret scan and `git diff --check` passed. HTTP prototype, Vite and backend servers responded locally; the browser captured both apps. A targeted Chrome run confirmed the MapLibre worker error, and a subsequent run showed the grid after the worker URL fix. No Playwright package, pixel-diff score, automated accessibility scan, complete keyboard audit, live PostGIS execution or printed-PDF review was performed. Mobile screenshot pairs exist, but clipping and focus order need explicit review. The prototype checksum and teammate branch pointers remained unchanged.

**Final visual acceptance: MAJOR DEVIATION.** The implementation is a substantial continuation and now covers all ten view structures, but the required pixel fidelity and functional coverage are not achieved. Follow-up is required before declaring Phase 5.1 complete.
