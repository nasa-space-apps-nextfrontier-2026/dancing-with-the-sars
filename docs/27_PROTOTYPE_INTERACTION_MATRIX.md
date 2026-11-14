# Prototype interaction matrix

> **Phase 5.1 update:** React now has routes for all ten prototype views and working source filters, inspector tabs, route direction, shelter density, sign-in, print and main dock controls. Prototype pass playback, map callouts, exact route/shelter selection and phone alert detail remain unavailable. See [Phase 5.1 report](30_PHASE5_1_UI_FIDELITY_COMPLETION.md) for current behavior and gaps. Earlier status rows below are the Phase 5 baseline.

| UI element | Prototype behavior / reference | React behavior | API / role | Status and test / mismatch |
|---|---|---|---|---|
| Header navigation | `topbar`, `data-go`, lines 1203–1212, 1284+ | React Router links | Route roles | Operational; visual header differs |
| Theme | Header and script theme switch | React theme state and root `data-theme` | None | Operational; automated dark visual check pending |
| Sign-in/logout | Prototype illustrative dialog | Cookie session and CSRF logout | `POST/GET/DELETE /session` | Operational; auth tests exist |
| Dock: Layers/Agents/Alerts/Time/Legend | `data-p`, main lines 397–405 | React panel state, real buttons | Signed-in main view | Operational toggle; panel test added; layout not visually verified |
| Agent accordion and actions | Main `ag`, lines 405–419 | Unknown rows, no invented counts | Reviewed results absent | NOT IMPLEMENTED; prototype claims excluded |
| Layer toggles (17) | `data-flag`, line 422 | Synthetic NISAR only; other layers unavailable | Reviewed layer API needed | PARTIAL; no fake layer enablement |
| Alert filters | `data-af`, main line 422 | Filters empty state by category | Reviewed alert API needed | Operational empty-state filter; test added |
| Alert pill/open | Main line 421 | Opens alert panel | None for empty state | Operational |
| Map callout | Main line 422, `callout` | Synthetic area selection result panel through `AreaExplorer` | `GET /areas/{id}/summary`, `GET /sources/{id}`; analyst + scope | Operational API; visual callout differs |
| Before/after/change/swipe, HH/HV/HH-HV, opacity | Timeline, lines 1214–1230, map scripts | Existing MapLibre synthetic grid controls | None beyond authenticated view | Operational; Phase 4 tests; timeline appearance differs |
| Individual passes / missing pass | `setPass`, lines 1278+ | Two window endpoints and explicit acquisition gap | Reviewed manifest needed | PARTIAL; no fabricated pass |
| Zoom/geolocation | Main map zoom icons | MapLibre native pan/zoom; decorative symbols do not accept clicks | None | MAJOR DEVIATION; symbols should be removed or wired before acceptance |
| Alert detail and nearby/rings | `v-alert` | Protected placeholder | Alerts/routes APIs unavailable | NOT IMPLEMENTED |
| Area summary and brief | `v-area`, `v-brief` | Protected placeholder and illustrative print | Area summary API exists on map; brief API absent | PARTIAL |
| Routes and shelters | `v-routes`, `v-shelters` | Protected unavailable views | Officer/coordinator; real APIs 501 | Correct safe state; prototype layout absent |
| Inspector tabs | `v-inspect` | Empty placeholder | Validated result API absent | NOT IMPLEMENTED |
| Sources | `v-sources` | Source limitations text and link | `GET /sources/{id}` on map | PARTIAL |
| Phone mockups | `v-phone` | No separate route | None | NOT IMPLEMENTED |
| Keyboard Escape/arrows | Script lines 1386+ | Native focus works; panel shortcuts absent | None | NOT IMPLEMENTED |

Visible decoration cannot be treated as validated evidence. Prototype route times, shelter capacities, damage counts and alert times were not transferred into operational logic.
