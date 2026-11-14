# Prototype visual verification

> **Phase 5.1 update (14 November 2026):** Chrome DevTools screenshot capture now works. The original Phase 5 blocker and the table below describe the earlier run. Current paired images for all ten base views at five sizes are in `docs/visual/phase5_1_current/`; the repeatable command is `node frontend/scripts/capture-visual.mjs`. The interactive overlay is `compare.html`. Shared header, dock icons, view structures and source screen have advanced. The reviewed 1440×900 main and area pairs still show major deviations, including the blank headless MapLibre canvas. Overall status is **MAJOR DEVIATION**. See [Phase 5.1 report](30_PHASE5_1_UI_FIDELITY_COMPLETION.md).

Reference checksum: `ABA74D61000B83956D61CE4A50A1CBDDB03C81C714F433C804FC417122A2D037` (`docs/design/civisar-prototype.html`).

**Final acceptance: NOT VERIFIED.** No matched screenshot pairs or image diffs were captured. The browser inventory reported its browser access host unavailable. A Windows Brave window showed that a local prototype tab exists, but window activation and user input interrupted capture. No pixel fidelity claim follows from the passing build or DOM tests.

| Viewport | Reference screenshot | React screenshot | Comparison |
|---|---|---|---|
| 1440×900 | Not captured | Not captured | NOT VERIFIED |
| 1366×768 | Not captured | Not captured | NOT VERIFIED |
| 1024×768 | Not captured | Not captured | NOT VERIFIED |
| 768×1024 | Not captured | Not captured | NOT VERIFIED |
| 390×844 | Not captured | Not captured | NOT VERIFIED |

All ten significant prototype views and their light/dark, panel, modal, filter and map states remain without paired screenshots. Known major deviations from source inspection: React has a separate navigation row; prototype has navigation in its 52px header. React uses MapLibre's non-geographic grid, while prototype draws an illustrative south-Lebanon SVG. React's dock uses text symbols in place of prototype SVG icons. Prototype alert/area/brief/routes/shelters/inspector/sources/phone layouts are not yet reproduced. The reference itself has only 1380px and 1180px media rules plus a separate phone mockup; mobile behavior needs review.

Implemented structural changes: extracted exact token/component CSS, adopted prototype colors/typography and main map dock/panel positions, preserved synthetic MapLibre controls and authenticated area/source flow. Automated tests cover dock open/filter behavior, auth, map controls and API data. No keyboard panel-shortcut or measured accessibility audit was completed. Native button labels and `aria-pressed` were added for the dock; a full focus-order and contrast check is pending.

Next visual run should use one browser engine at fixed DPR/zoom and loaded IBM Plex fonts, serve the original file and React app over HTTP, sign into React with a local synthetic account, align themes and panel states, capture each viewport and screen, then inspect overlays and diffs. Fix measured mismatches without changing the reference.
