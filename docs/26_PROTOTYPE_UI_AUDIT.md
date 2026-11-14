# Prototype UI audit

Reference: `docs/design/civisar-prototype.html` (the prompt's `doc/design` path uses the wrong directory name). SHA-256: `ABA74D61000B83956D61CE4A50A1CBDDB03C81C714F433C804FC417122A2D037`. The 162,316-byte single file contains four style blocks, about 340 CSS rules, three script blocks and ten views. It was not edited.

## Screens, components and states

| View / lines | Prototype elements | React mapping and current status | Visual verification |
|---|---|---|---|
| Main map `393–447` | Header, map, five-button dock, agent/layer/alert/legend/time overlays, callout, zoom, alert pill | `PrototypeMain`, `AreaExplorer`, `MapPanel`; dock and overlays mapped, but callout, timeline form, map art and exact header incomplete | NOT VERIFIED |
| Alert `448–529` | Map, alert detail side panel, rings, nearby facilities/routes | `AlertDetail` route; content placeholder | NOT VERIFIED |
| Area `530–606` | Area cards, people/services, evidence, sources | `AreaSummary` route; placeholder | NOT VERIFIED |
| Brief `607–670` | Black/white printable report | `AreaBrief` route; placeholder | NOT VERIFIED |
| Routes `671–743` | Rail, route comparison, turn list, route selection | `RouteScreen`; unavailable state | NOT VERIFIED |
| Shelters `744–795` | Candidate list, capacity controls, map | `Shelters`; role protected unavailable state | NOT VERIFIED |
| Inspector `796–840` | Floating panel, agent rows and tabs | `Inspector`; empty state | NOT VERIFIED |
| Sources `841–897` | NASA cards, provenance and timeline | `Sources`; placeholder | NOT VERIFIED |
| Sign-in `898–941` | Demo sign-in dialog | `SignIn`; actual server auth retained | NOT VERIFIED |
| Phone `942–1002` | Three mobile mockups | No separate React route; responsive main shell only | NOT IMPLEMENTED |

Reusable prototype components include `.cv-btn`, `.cv-seg`, `.cv-tabs`, `.cv-ev`, `.cv-dmg`, `.cv-fac`, `.cv-range`, `.cv-age`, `.cv-src`, `.cv-card`, `.cv-panel`, `.cv-banner`, `.cv-tag`, `.cv-sw`, `.cv-layer`, `.cv-alert`, `.cv-time`, `.cv-route`, and `.cv-table`. Four style blocks were extracted to `frontend/src/prototype.css`; the Google font import was moved to the top for valid CSS processing, with value declarations preserved. The app uses IBM Plex Sans 400/500/600/700 and IBM Plex Mono 400/500/600 from Google Fonts, with system fallbacks. Remote font availability is unverified.

## Tokens and assets

Light tokens include background `#f3f4f1`, surface `#ffffff`, ink `#121c1c`, accent `#1d5a86`, radar `#6b3fa0`, line `#d4d8d2`; dark tokens include background `#0e1316`, surface `#151c20`, ink `#e6ebe9`, accent `#73b5e3`, radar `#c39be8`. Spacing is 4/8/12/16/24/32 px; radii 3/6/10/999 px; floating shadow uses two layers. Base typography is 14/20 px; headings 28/34, 18/24 and 15/20 px; data uses 12/16 px Mono. All remaining token values are retained in `frontend/src/prototype.css` from lines 1–3 of the prototype.

No separate image or icon asset file is referenced. The prototype generates line SVG icons and an illustrative SVG south-Lebanon map in `Civisar.icon`/`Civisar.map` (`1003–1242`). The React implementation retains MapLibre, so this map artwork was not copied into an operational map. Icon replacement is incomplete: dock glyphs are currently text symbols and visually differ. The only external dependency is Google Fonts. No external JS library is used by the HTML.

## Navigation, interaction and responsive inventory

Header navigation: Map, Alerts, Areas, Routes, Shelters, Sources. Additional `data-go` destinations: brief, inspector, sign-in and phone. The scripts hydrate shared headers/icons/maps/evidence/timeline, switch hash-based views, toggle five map panels, filter alerts, select layers/passes, open callouts, select routes, recalculate illustrative shelter capacities, switch theme, show toast/user menu, and handle Escape/left/right keys. `data-flag` names 17 layer toggles; `data-af` names six alert filters. Mock numbers, alerts, facilities, damage classes, routes and capacity calculations are demonstrations and cannot become verified app data.

CSS breakpoints are `max-width:1380px` (freshness/search/nav adjustment) and `max-width:1180px` (freshness hidden). No general mobile layout media query appears in the prototype; `v-phone` is a separate illustrative view. Reduced-motion rules disable skeleton and pulse animation. React adds a `max-width:768px` adjustment; fidelity at 1440×900, 1366×768, 1024×768, 768×1024 and 390×844 remains unverified.

The full interaction mapping and discrepancies are in [27_PROTOTYPE_INTERACTION_MATRIX.md](27_PROTOTYPE_INTERACTION_MATRIX.md). The original JS is not imported into React, because it would insert mock scientific claims and bypass typed state/API boundaries.
