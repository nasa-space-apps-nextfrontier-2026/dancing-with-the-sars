# Frontend design and screen plan

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Implementation contract

React + Vite + MapLibre GL JS, IBM Plex Sans text and IBM Plex Mono numbers/dates/sources. Source: UI_DESIGN.md §§1–7 and ARCHITECTURE.md Part 4. Readable light/dark themes, neutral background, NASA blue main actions/NISAR, violet candidate radar change, amber-brown attention. Outlined points and hatched area layers preserve map readability. Tokens are CSS variables; exact remote mockup colour/spacing values remain VERIFY because the external artifact could not be opened. Do not invent pixel-perfect fidelity.

ARCHITECT RECOMMENDATION: TypeScript client generated from reviewed OpenAPI, local fixture adapter selected by explicit demo flag, never a silent real-data fallback. Display “Illustrative demo data” on every synthetic map, panel and export. A mixed-source response flags individual synthetic values and the whole screen. Client calculations may format, not fabricate domain estimates. Source UTC timestamps render alongside explicit local timezone in alert details.

## All eleven views

| View | API under /api/v1 | Priority | Owner task | Source | Acceptance |
|---|---|---|---|---|---|
| Sign-in | POST/GET /session; GET /roles | MVP | M4-01 | UI_DESIGN.md §6 | Form keyboard accessible; errors scrubbed; role never chosen in client; expired session clears private state |
| Logged-out public-safe view | GET /public/map; /status; /sources | MVP | M4-01 | UI_DESIGN.md §6 | No route/shelter/brief/dispatch/private layer data in requests or payloads; sign-in explanation |
| ScreenMainMap | GET /layers; /layers/{id}/tiles/...; /alerts; /areas/{id}/summary; /status | MVP | M4-02 | UI_DESIGN.md §§3/3.1 | Agent results first, NASA data next; CORE tag, HH/HV/HH−HV, track/opacity, folding side rails [, ], active legend, missing passes |
| ScreenAlertDetail | GET /alerts/{id}; POST /alerts/{id}/reviews; POST /routes | MVP | M4-03 | UI_DESIGN.md §3.1 | Fire wording, no cause, local+UTC time, NOAA-20/21 product; restricted synthetic 1/3 km rings; compare routes and summary actions |
| ScreenAreaSummary | GET /areas/{id}/summary; POST /briefs; POST /routes; GET /shelters | MVP | M4-03 | UI_DESIGN.md §§2/3.1 | People first; ranges, vulnerabilities, source-linked what-to-bring; no invented counts; role-filtered nearest options |
| ScreenAreaBrief | POST /briefs; GET /briefs/{id}/print | MVP A4/print-to-PDF; offline later | M4-03 | UI_DESIGN.md §§2/3.1 | One black-on-white A4 page, numbered source footnotes, acquisition/save dates, QR to authenticated view without token/coordinates |
| ScreenRoutes | POST /routes; GET /routes/{id}; /routes/{id}/status; POST /closures | MVP | M4-03 | UI_DESIGN.md §3.1; PROJECT_PLAN.md §6.5 | A/B/C solid/long dash/dot-dash; seven facts fixed order, in/out, vehicle type, local turn list, new-closure banner, never safe |
| ScreenShelters | GET /shelters; POST /shelters/capacity; /shelters/{id}/field-checks | MVP buildings; open land may reduce | M4-03 | UI_DESIGN.md §3.1; PROJECT_PLAN.md §6.7 | Coordinator only; all four space settings; buildings first; capacity uncertainty; candidate sentence and protection/ordnance warning |
| ScreenInspector | GET /areas/{id}/values; /layers/{id}/timeseries; /areas/{id}/validation; /values/{id}/trace | MVP; validation conditional | M4-02 | UI_DESIGN.md §3.1 | All agents/Time series/Validation tabs; Escape closes; focus returns; source trace; unavailable validation explicitly shown |
| ScreenSources | GET /sources; /sources/{id}; /values/{id}/trace | MVP | M4-03 | UI_DESIGN.md §3.1 | Large NISAR core tile and pass strip; NASA next; provenance, dates, terms, uncertainty and actual model tests |
| ScreenMobile | Same authorized alert/summary/routes contracts | MVP basic responsive; PWA deferred | M4-04 | UI_DESIGN.md §1/3 | Phone browser alerts/summary/routes; readable focus order, offline/cached status; no separate native app |


## All fourteen shared components

Every row traces to UI_DESIGN.md §4, with §5 for wording/style; API links are draft contract mappings. Components are MVP except optional offline enhancements.

| Component | Contract/API | Owner task | Acceptance |
|---|---|---|---|
| EvidenceLabel | MetricValue / AlertDetail / all derived outputs | M4-01 | Four words and distinct icons/shapes; no colour-only meaning |
| DamageClass | GET /areas/{id}/damage | M4-02 | Hatched square/diamond/triangle/dashed circle; every class candidate; combined severe/destroyed if model cannot distinguish |
| FacilityStatus | GET /areas/{id}/facilities | M4-03 | H/C/S/W/P symbols; reported working only; no-damage ≠ open |
| RangeValue | MetricValue in summary/people/values | M4-01 | Round display to 100 below 10,000 and 1,000 above; preserve raw low/high for trace; never display null as zero |
| SourceLine | SourceRecord / GET /values/{id}/trace | M4-01 | Dataset, detail, date, NASA tag and DataAge; numbered print footnote |
| DataAge | GET /status and per-value freshness/cached | M4-01 | Date first; Fresh dot/Aging ring/Stale diamond/Cached dashed ring; show last-success and failures |
| AlertCard | GET /alerts | M4-02 | Type, area, source, time, label; attention bar not flashing or red |
| RouteOption | POST /routes and GET /routes/{id} | M4-03 | Seven fixed facts plus unknowns/revision warning; never safe |
| ShelterCard | GET /shelters | M4-03 | Rank/capacity assumptions/For checking; only authorized response |
| TimeSlider | Layer.available_acquisitions and GET /layers/{id}/timeseries | M4-02 | Actual pass dates only; gap dotted; before dashed/after solid; Before/Change/After/Swipe; swap dates requires valid ordering |
| LayerToggle | GET /layers and layer metadata | M4-02 | Symbol, source date and age; server denies private layer regardless of UI state |
| MapLegend | GET /layers plus active client state | M4-02 | Only active layers; above 8 layers Focus mode dims data backgrounds; patterns preserved |
| SystemStates | GET /status; all errors | M4-01 | Distinct loading/no-data/Unknown/Stale/offline/delay/denied states; visible synthetic badge |
| Button | Screen primary endpoint/action | M4-01 | One primary action per view; accessible name, disabled/busy/focus states and keyboard activation |


## Interaction and accessibility acceptance

Map→area callout→summary→print is at most three actions; alert→detail→compare routes at most two. Authorized facility/area→route intent is one action, but server still checks role and scope. Route/shelter options must not preload in analyst state. Main top bar exposes freshness for NISAR/Sentinel-1/lights/fires/internet, including unavailable sources. Left/right rails collapse without losing focus, shortcuts do not fire while typing. Inspector Escape restores triggering focus. Before/after/swap/swipe respect missing passes and preserve explicit acquisition dates.

ARCHITECT RECOMMENDATION: WCAG 2.2 AA target, visible focus, semantic landmarks, labelled inputs, keyboard-accessible non-map lists, contrast checks in both themes, reduced motion, minimum comfortable touch targets. Check phone widths 360/390 px, desktop 1280 px and 200% zoom. A map-only interaction must have an equivalent list/control. No red/flashing urgency animation.

A4 brief contains people first, what-to-bring basis, vulnerable groups, facility/hazard caveats and numbered citations; no secret route/shelter details for analyst exports. QR encodes authenticated application path only, never an access token or exact coordinates. Basic browser Save as PDF is the MVP export; server PDF generation and offline persistence are deferred. At H38 audit every displayed metric against its fixture/real lineage and source date.

## Public and offline policy

Public view serves only publication-approved r8 aggregates with additional suppression. No sensitive population concentration or undamaged critical-site inventory appears in tiles, inspector or hidden JSON. Logged-out preview has explanatory sign-in affordances. No public brief, route, shelter or dispatch endpoint is introduced.

PWA installable public shell is stretch; restricted offline storage is post-hackathon. Protected responses use no-store, no service-worker cache, no browser localStorage tokens. On logout/role change remove private map sources, in-memory query caches, print models and any temporary download URLs. Offline mode shows last-known timestamps only where policy allows retention; it never claims a cached route is current.
