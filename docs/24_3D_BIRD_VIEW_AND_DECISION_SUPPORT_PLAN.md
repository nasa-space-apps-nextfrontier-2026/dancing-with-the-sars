# 3D bird view, 360 scene and decision support: new direction

[Blueprint index](README.md) · [UI design](UI_DESIGN.md) · [Plan](PROJECT_PLAN.md) · [Integration](21_ML_BACKEND_FRONTEND_INTEGRATION.md)

Written 14 November 2026 from Thanoban's new idea. It gives the other team members the full context so they can build from it. **Read section 2 first:** some parts of the idea conflict with decisions already made, and some cannot be done exactly as described. Nothing here changes the existing plan until the team agrees (section 12).

## Update 14 November 2026 (later): decisions and the final data list

Thanoban reviewed this plan and decided:

1. **Good enough is fine.** The scene and the budget do not need to be exact. About **70% correct** (a believable, data-grounded average) is the target. Exact cost, exact video realism and per-building truth are **not** required.
2. **The rebuild budget and duration estimator is adopted** as an *indicative planning range* (section 9). It replaces the earlier "needs a decision" status. The scope row "No rebuilding" in [PROJECT_PLAN.md](PROJECT_PLAN.md) section 3 is therefore superseded for this feature; the owner of that file should update it. Ranges only, never a quote.
3. **Only free data is used.** The final list is section 15. Paid or unverified sources (Google Photorealistic 3D Tiles, Maxar, Mapillary, Google Open Buildings, Overture heights) are dropped.
4. **Udula takes the new data and agent work** after finishing the ML. Tasks: [25_NEW_PLAN_TASKS.md](25_NEW_PLAN_TASKS.md).

Everything else in this document stays as written, including the safety rules and the fidelity badge.

## 1. The idea in one page

Instead of only a flat Google-Maps-style map, officers get a **3D "Google Earth" view** with these parts:

| # | Part | What the officer gets |
|---|---|---|
| A | **Bird view (option)** | Tilt and rotate the map into a 3D view of the area: terrain, extruded buildings, lit night scene |
| B | **360 scene** | A game-like scene (three.js) they can orbit, fly and look around in 360 degrees, showing what the data says about a place: damaged building areas, fire, lights out |
| C | **Dashboard controls** | Game-style controls (move, rotate, zoom, tilt, camera presets, time slider) in the dashboard |
| D | **Real fire, not an emoji** | Cheap animated flame and smoke instead of the small emoji marker |
| E | **Many incidents: rank and insights** | When many incidents happen, the system ranks them and explains why |
| F | **Decision assistant** | An AI helper that acts like a calm duty officer: it suggests options with reasons and risks. The human decides |
| G | **Rebuild budget and duration agent** | An agent that estimates cost and time to rebuild |
| H | **Better colours and UX** | A calmer colour theme designed around how people behave under stress |
| I | **OpenStreetMap** | Use OSM as the base for buildings and roads |

## 2. Honest limits and conflicts (read this first)

| Idea | Problem | What we do instead |
|---|---|---|
| "Looks exactly like what happened, like a real video" | A satellite does not see what happened. NISAR shows radar change (about 20 m), night lights show 450 m pixels, FIRMS shows heat points. Nobody has footage or per-building truth. A realistic video would look like evidence but would be invented | A **data-driven reconstruction**: every visible element is tagged *From data*, *Inferred* or *Illustrative*, and the scene always carries a "Reconstruction, not footage" badge. Never claim "exactly what happened" |
| Showing "that building got affected" | The damage model works on H3 cells of about 0.1 km², not on single buildings. Painting one building as collapsed would claim precision we do not have | Tint or hatch the **cell**, show rubble hints only where two independent sources agree, and state the cell size in the panel |
| "Google Earth" imagery | Google Earth and Google Maps tiles cannot be used here (licence). Free imagery is 10–30 m (Sentinel-2, HLS, Landsat via NASA GIBS), not sub-metre | Stylised 3D buildings from OSM over free satellite imagery. It will look like a clean city model, not a photo |
| 360 view "like a real accident" | Realistic casualties or people would be harmful and fabricated | No people, no casualties, no gore. Buildings, terrain, lights and fire only |
| Rebuild budget and duration agent | The project scope says "No rebuilding: reconstruction plans and rebuild tracking are out of scope" ([PROJECT_PLAN.md](PROJECT_PLAN.md) section 3). Costs also depend on facts we do not have | **Adopted by Thanoban (14 Nov) as an indicative planning range**, a stretch feature after the core demo (section 9). The scope rule in the plan file still needs to be updated by its owner |
| Public, building-level 3D | The safety rules forbid a public list of what is still standing and require delayed, area-level public output | 3D building-level views are **logged-in only**. The public map stays r8, delayed and approved by a person |
| Real-time feel | Radar passes every 12 days, fires several times a day, lights daily. No live tracking is allowed | The scene shows the **latest data and its age**, plus a time-lapse of real passes. Never a live feed |

What we can promise honestly: an immersive, understandable, data-grounded 3D view with a time-lapse of real satellite change, fires and lights. That is already a strong demo.

## 3. Scope by phase (48-hour reality)

Rashiru already carries about 85 hours of core work, so this plan is mostly **stretch after the feature freeze (H38)** unless the team cuts something else.

| Phase | Content | When | Effort (rough) |
|---|---|---|---|
| **P0** | Bird view toggle: pitch and rotate the existing MapLibre map, extrude OSM buildings, tint damage cells, particle fire sprite instead of the emoji, new colour tokens | Inside the 48 h only if core is green | 6–10 h |
| **P1** | three.js scene as a MapLibre custom layer: terrain, extruded buildings from OSM, damage cell volumes, fire particles, lights-out night shading, time slider over the 11 NISAR passes | After H38 / post-hackathon | 25–35 h |
| **P2** | First-person and 360 camera, game-style controls, camera presets, screenshot and share of a view | After P1 | 15–20 h |
| **P3** | Incident ranking and insights; decision assistant (rule-based first) | Ranking can start with P0 (it reuses the severity parts already planned) | 12–20 h |
| **P4** | Rebuild budget and duration estimator | Only after a team decision (section 9) | 15–25 h |

Cut order if time is short: P4, P2, P1, P3 assistant text, keep P0 and the ranking.

## 4. Bird view and 3D scene

### 4.1 Technology (recommended, all free and open)

| Layer | Choice | Why |
|---|---|---|
| Map and globe | **MapLibre GL JS** (already in the scaffold), globe projection and 3D terrain | One map stack, no new engine, BSD licence |
| 3D objects | **three.js** (MIT) as a MapLibre **custom layer**, sharing the same camera | Gets buildings, fire, lights and camera control without a second map |
| Terrain | NASADEM (already a dataset) turned into terrain tiles, or open "Terrarium" terrain tiles | Free, no key |
| Imagery | NASA **GIBS** (true colour, HLS, night lights) | NASA data stays the visible base |
| Buildings and roads | **OpenStreetMap** via HOTOSM exports, served as **PMTiles** (see 4.4) | Already in the data plan |
| Alternative | CesiumJS (Apache 2.0) for a true globe with 3D Tiles | Heavier; its free terrain and buildings come from Cesium ion, which has terms and quotas. Keep as plan B |

Avoid: Google Earth or Maps tiles, Mapbox (paid terms), and any Chinese provider (Space Apps rule).

### 4.2 What the scene shows and where it comes from

| Scene element | Source | Visual | Tag |
|---|---|---|---|
| Terrain | NASADEM | Shaded relief, slopes | From data |
| Buildings | OSM footprints (HOTOSM). Height from `building:levels`, else GHSL height divided by 3 m, else a default | Extruded boxes, flat roofs, neutral colour | From data / Inferred (height) |
| Damage cells | NISAR damage table, H3 r9 cells, classes possible / moderate / destroyed-or-severe (candidate) | Hatched, lightness-stepped overlay on the cell footprint, never a collapsed model of one building | From data |
| Two-sensor agreement | Sentinel-1 agrees flag (`corroborated`, 13 cells today) | Stronger hatch plus a "second sensor agrees" mark | From data |
| Rubble hint | Only where the cell is `corroborated` and a person approved it | Low debris mesh inside the cell | Illustrative |
| Fire | FIRMS detections (375 m points, with time and satellite) | Particle flame and smoke at the detection, size set by detection confidence, radius shows the 375 m uncertainty ring | From data (position) / Illustrative (flame look) |
| Lights out | Night-light function: possible power loss cells | Night scene where those cells are dark and neighbouring cells stay lit | From data |
| Roads | OSM roads | Thin lines; closed or unknown segments from the routing function | From data |
| Time slider | 11 NISAR passes (track 151D) plus fire and light dates | Play, pause, step; the scene changes state; missed passes shown as gaps, never interpolated | From data |

### 4.3 Fidelity badge

Every screen of the scene shows: **"Reconstruction from satellite data, not footage"**, the date of each layer, and a legend with the three tags. The 72-hour hold on new radar detections applies here exactly as in the map.

### 4.4 Data delivery

- Buildings and roads: one PMTiles file for the demo box (south Lebanon, 35.0–36.0 E, 33.0–33.6 N). The browser asks for tiles by range request, so no tile server and no hammering of the public OSM servers.
- Damage cells and alerts: the existing API (`/areas`, `/areas/{id}/damage`, `/alerts`), see [ML wiring](progress/ML_WIRING.md). A new bulk endpoint returning cells as GeoJSON for the visible area is needed (small contract change; see section 11).
- Never send the raw radar images to the browser. Send only the aggregated cell results the user's role may see.

### 4.5 Performance budget

| Item | Target |
|---|---|
| Frame rate | 60 fps on a normal laptop with integrated graphics; 30 fps minimum on a tablet |
| Buildings in view | Instanced meshes, merged geometry per tile, about 150,000 triangles in view at most |
| Fire | One GPU particle system, 300–600 particles per fire, sprites (billboards), no per-fire lights |
| Level of detail | Far view: tinted footprints only; near view: extruded boxes |
| Fallback | If WebGL or frame rate fails, switch automatically to the 2D map and say so |
| Accessibility | Respect "reduce motion": no flame animation, static icon; no flashing above 3 per second |

## 5. Camera and controls

A control panel in the dashboard, not hidden shortcuts. Game-style, but simple.

| Control | Mouse / keyboard | On-screen button | Touch |
|---|---|---|---|
| Move (pan) | Left drag, W A S D | Four arrow buttons | One finger |
| Rotate and tilt | Right drag, Q E | Rotate left / right, tilt up / down | Two fingers twist |
| Zoom | Wheel, + and - | Plus and minus | Pinch |
| 360 look-around | Mouse look in first-person mode | Hold-and-drag look pad | Gyroscope or drag |
| Camera presets | Number keys 1–4 | Preset buttons | Preset buttons |
| Time | Space = play, arrows = step | Time slider | Slider |
| Reset | R | Home button | Home button |

Camera presets: **1 Overview** (high, looking down), **2 Bird view** (45 degrees, orbiting the selected place), **3 Street level** (eye height, first-person), **4 Incident focus** (auto-framed on the selected alert with the fire ring and the damage cell). A "Back to 2D map" button is always visible.

Rules: the camera cannot leave the demo area, cannot go below terrain, and every mode has an exit.

## 6. Many incidents: ranking and insights

The plan already defines the **five severity parts** ([PROJECT_PLAN.md](PROJECT_PLAN.md) section 6.3): damage level, people there, critical facilities hit, power or water lost, roads cut. This plan adds fire and freshness and turns them into a ranked list.

### 6.1 Priority score (transparent, deterministic)

Each incident gets a score from 0 to 100 built from named parts. The officer can see and change the weights.

| Part | Source | Default weight |
|---|---|---|
| People affected (range, uses the high end for ranking and shows both) | People function | 30 |
| Critical facility hit or cut off (hospital, water, power) | Facility function | 20 |
| Damage level and evidence strength (candidate, corroborated) | Damage table | 15 |
| Fire near people or facilities (distance, detection confidence) | FIRMS events | 15 |
| Services lost (power, water, internet) | Services functions | 10 |
| Time since detection (older and unreviewed rises slowly) | Alert time | 5 |
| Access (route options available, unknown road segments) | Route function | 5 |

Rules: the list shows **rank, score, the top two reasons, what is unknown, and the age of each input**. A part with no data counts as unknown, not zero, and the score is shown as a range when unknowns are large. Ties are broken by people affected. Ranking never hides an incident; it only orders them.

### 6.2 Insights

Short, template-based sentences built from computed values, each with source and date. Examples: "3 of the 5 highest-ranked incidents are within 2 km of a lost-power area", "Fire detected 400 m from a clinic; no route data yet", "Two satellites agree on 1 of 49 power-loss cells". No generated numbers.

## 7. Decision assistant ("duty officer helper")

### 7.1 What it is

An assistant that helps an officer think under pressure. It **proposes options; it never decides, never dispatches, never changes data**. The officer can follow, change or ignore a suggestion, and every suggestion and choice is logged.

### 7.2 What it produces for a selected incident

| Output | Content |
|---|---|
| Situation line | One calm sentence: what the data shows, how old it is, how sure we are |
| Options (2 or 3) | For example "Send medical team and water to Area A", "Hold and verify with a field check", "Prepare evacuation routes". Each with reasons, what it needs (from the area summary: what to bring), risks, and unknowns |
| Trade-offs | What is gained and what is given up with each option, in plain words |
| What we do not know | Missing data, old data, single-sensor evidence, unknown road segments |
| Checklist | Verification steps (field check, protection and ordnance check before shelters, confirm route closures) |
| Next review | When to look again, based on the next data update |

### 7.3 How it is built (safe by design)

| Layer | Approach |
|---|---|
| Core (build first) | **Deterministic rules and templates** over the computed values: ranking, option generation from fixed playbooks (medical, water, power, evacuation, verification), trade-off text. No language model needed |
| Optional text layer (later) | A language model may only **rewrite** the structured result into plain language. It receives only the already-computed, role-allowed values, cannot invent numbers, and its output is labelled "AI explanation, not authoritative" |
| Data protection | Restricted data (shelter locations, routes, building-level results) is **never sent to an outside service**. Use a local or self-hosted model, or no model. This matches the existing rule for the stretch Gemini box |
| Identity | It presents as "CIVISAR assistant", never as a real person or a real officer |
| Language rules | Never "safe", never "confirmed damage"; use "no reported closure", "candidate", "fire detected". Offer options, not orders |
| Authority | Read-only. No automatic action. Officer approval is a separate, logged step |
| Role limits | An analyst gets analysis only; an officer also gets routes; a coordinator also gets shelters. The assistant respects the same role filter as the API |
| Audit | Log: incident, inputs used (ids and dates), options shown, what the officer chose. No personal data beyond user id |

### 7.4 Interaction

A side panel in the dashboard: the situation line and options first, then "Ask" with a short list of **fixed questions** ("What changed since last pass?", "Which route options exist?", "What should we bring?", "Why is this ranked first?"). Free text is a later stretch.

## 8. Fire, light and effects (affordable)

| Effect | Cheap method |
|---|---|
| Flame | Camera-facing particle sprites with an additive blend and a small texture atlas (one draw call per fire). Libraries such as three.quarks or a hand-written GPU particle shader are enough |
| Smoke | 100–200 soft sprites that rise, fade and drift; wind direction optional, from the weather setting if present |
| Fire size | Scales with detection confidence and radiative power (FRP) from FIRMS; the 375 m uncertainty ring is always drawn |
| Night scene | A darkened basemap with emissive window textures on buildings in lit cells; cells with possible power loss lose their emissive glow |
| Damage cell look | A pattern overlay (hatch), not a colour only, so it is readable for colour-blind users and in 3D |
| Reduced motion | Static flame icon with a label |

No video playback, no physics simulation, no destruction animation.

## 9. Rebuild budget and duration estimator (adopted as an indicative range)

Thanoban adopted this on 14 November 2026 with a **70% accuracy target**: a believable average range is enough. It is a **separate, later feature**, labelled "planning indication only".

Design:

| Aspect | Design |
|---|---|
| Inputs | Damage candidate class and cell area, building footprint area and levels (OSM, GHSL fallback), facility type, local unit costs |
| Method | Indicative range = affected floor area × share by damage class (reuse the displaced shares: destroyed and severe 100%, moderate 50%, possible 20%) × cost per square metre range. Duration = work volume divided by an editable crew capacity, with a start delay for assessment and clearance |
| Output | A low–high cost range and a low–high duration range, with the assumptions shown and editable. **Never a single number, never a quote** |
| Sources | Public cost references (for example World Bank and UN damage and needs assessments for Lebanon, published local construction cost indices). Exact sources to be checked at build time; none is assumed correct here |
| Limits | Radar misses damage, cell size is 0.1 km², heights are estimated, and costs change fast. The panel says "Planning indication only" |
| Safety | Not shown on any public view; analyst and coordinator roles only |

## 10. Colour theme and UX around how people behave under stress

The design system already has calm neutral tokens, NASA blue for NISAR and actions, violet for radar, amber-brown for attention (not red), shapes and letters next to every colour, light and dark themes ([UI_DESIGN.md](UI_DESIGN.md)). These are the improvements to add.

| Principle (how people behave) | Change |
|---|---|
| **Stress narrows attention and reduces reading** | One clear primary action per screen, a short "what matters now" strip (top three ranked incidents), large targets (at least 44 px), plain words, numbers shown as ranges with one headline |
| **Alert fatigue** | Group alerts by area and type, show counts, no flashing, no sound by default, an "acknowledge" state that stays visible |
| **Red everywhere makes everything look equally urgent** | Keep amber-brown for attention; reserve the strongest colour for the one top-ranked incident; use lightness steps, not many hues |
| **Colour meaning must be learned once** | A fixed meaning per colour: blue = NASA data and actions, violet = radar change, amber = needs attention, grey = unknown. Unknown is never green |
| **Night shifts and tired eyes** | Dark theme as the default in the control room, warm low-glare greys, no pure white blocks, adjustable brightness; the 3D night scene is dark but readable |
| **Cognitive load** | Progressive disclosure: summary first, details on request; keep the 3D view uncluttered (layer presets: Overview, Damage, Services, Fire) |
| **Trust** | Show data age and evidence label on every element; the fidelity badge in 3D; no false precision |
| **Motion sensitivity** | Respect reduced motion; no strobe or rapid flicker (keep flame animation slow and smooth) |
| **Accessibility** | Contrast at least 4.5:1 for text, 3:1 for graphics, colour-blind-safe damage palette (already lightness-stepped), keyboard access to every 3D control |

Deliver as new tokens in the design system (`tokens.json`) and a short usability test with two or three people who are not on the team (can they find the top incident in under 10 seconds?).

## 11. Technical changes needed

| Area | Change | Owner (suggested) |
|---|---|---|
| Frontend | MapLibre globe, terrain and 3D building layer; three.js custom layer; control panel; time slider; fidelity badge; new colour tokens | Rashiru |
| Frontend | Ranking list, insights cards, assistant side panel | Rashiru |
| API | Bulk cells endpoint for the visible area (GeoJSON, role and scope filtered, 72 h gate); incidents endpoint with ranking parts; no new data stored | Rashiru, contract change first |
| Data | One PMTiles file of buildings and roads for the demo box; terrain tiles from NASADEM | Rashiru |
| ML side | Provide fire confidence, FRP, time and satellite on every fire event; night-light lit/dark state per cell | Thanoban (small additions to `worker/services`) |
| ML side | Damage cells plus the second-sensor flag, already published | Udula, done |
| Docs | Update the design system with the new screens and tokens | Rashiru with Claude Design |
| Tests | 3D view falls back to 2D; no restricted data without role; assistant never invents numbers; ranking shows unknowns; reduced-motion honoured | All |

Contract rule: any new field or endpoint goes into `docs/contracts/` first ([21](21_ML_BACKEND_FRONTEND_INTEGRATION.md)).

## 12. Decisions needed from the team

| # | Decision | Recommendation |
|---|---|---|
| 1 | Adopt the 3D bird view inside the 48 h or after the freeze? | P0 inside only if core is green; P1 and later after the freeze |
| 2 | Allow the rebuild budget agent despite the "no rebuilding" scope rule? | **Decided yes (14 Nov), as ranges.** Update [PROJECT_PLAN.md](PROJECT_PLAN.md) section 3 |
| 3 | Assistant: rules only, or add a language model for the wording? | Rules first. Add a model only if it can run without sending restricted data outside |
| 4 | Three.js on MapLibre, or CesiumJS? | MapLibre plus three.js (one stack, lighter, fully free) |
| 5 | Who owns the 3D work? Rashiru already has about 85 hours of core work | Give P0 and the ranking to Rashiru; give P1 and P2 to whoever has free time after the freeze (Udula and Thanoban finish the ML early) |
| 6 | Exact wording for the fidelity badge and the three tags | Adopt as written in section 4.3 |

## 13. Acceptance checks

- The 3D view shows only what the officer's role may see; a logged-out user gets the public r8 map only.
- Every 3D element carries a tag (From data, Inferred, Illustrative) and the fidelity badge is always visible.
- A damage cell is never drawn as a single collapsed building.
- Fire shows the 375 m uncertainty ring and the detection time; no cause is stated.
- The time slider uses only real passes; a missed pass is shown as a gap.
- Frame rate and fallback targets in section 4.5 are met on a normal laptop.
- The assistant gives options, not commands; it logs choices; it never states a number that the data layer did not provide.
- The ranking list shows reasons, unknowns and data age; the weights are visible.
- No Google tiles, no Chinese services, no restricted data sent outside; OSM attribution (ODbL) shown.
- Reduced-motion setting removes flame animation.

## 14. Risks

| Risk | Handling |
|---|---|
| The 3D view looks more certain than the data | Fidelity badge, tags, cell-size note, no per-building collapse |
| Time cost too high for 48 hours | Phases and cut order in section 3; P0 only inside the hackathon |
| Performance on weak laptops | Budget in 4.5, level of detail, automatic 2D fallback |
| Misuse of building-level views | Logged-in roles only, 72 h hold, audit log, no public building-level data |
| Assistant gives a bad suggestion | Read-only, evidence and unknowns shown with every option, officer decides, choices logged |
| Rebuild estimate taken as a quote | Ranges only, editable assumptions, "planning indication" label, adopted only after the team decision |
| Licence problems | Only OSM (ODbL), NASA open data, MIT and BSD libraries; check every tile source before use |

## 15. Final data list (free only, decided 14 November 2026)

This replaces the longer discussion above. Use only these.

| Need | Source | How we use it | Check before use |
|---|---|---|---|
| Building shapes, types, facilities, roads | **OpenStreetMap via HOTOSM** (HDX `hotosm_lbn_buildings`, `hotosm_lbn_roads`) | Footprints and type; ODbL attribution | None |
| Building height, first choice | **3D-GloBFP** (per-building height, 2020, Zenodo; Asia part DOI `10.5281/zenodo.11397015`) | Height per footprint, as a range | **Check the licence on the Zenodo page**; **check the height accuracy on Lebanon** (section 15.2) |
| Building height, fallback | **GHSL building height** (JRC, 100 m grid) | Average height of the cell when no per-building height | Attribution to JRC |
| Height where it exists | OSM `building:levels` and `height` tags | Overrides the estimates | Only about 0.28% of buildings have it |
| Terrain | **NASADEM** (NASA) | 3D terrain and slope | None |
| Ground colour | **NASA GIBS** HLS 30 m true colour; optional Sentinel-2 10 m from Copernicus Data Space (free account) | Texture under the 3D scene | Cloud-free date |
| Real events | Our data: NISAR damage cells, FIRMS fires, Black Marble lights, WorldPop people | Scene states, ranking, summaries | Already built |

Height order for every building: **OSM tag, then 3D-GloBFP, then GHSL, then a default for the building type.** Floors = height divided by 3 m. Every height is stored as a low and high value with its source.

### 15.1 The building table (one row per building; the agents read it)

| Column | Meaning |
|---|---|
| `building_id` | OSM id |
| `h3_r9`, `h3_r8` | cell the footprint centre falls in |
| `footprint_m2` | area from the OSM outline (projected CRS, not degrees) |
| `height_low_m`, `height_high_m`, `height_source` | range and where it came from (`osm`, `globfp`, `ghsl`, `default`) |
| `floors_low`, `floors_high` | height range divided by 3 m |
| `use` | OSM building type (residential, school, clinic, ...), `facility_flag` |
| `residents_low`, `residents_high` | WorldPop people of the cell spread by floor area (range) |
| `damage_class`, `evidence_label`, `second_sensor_agrees`, `run_id` | from Udula's damage table for the cell the building sits in (a cell result, not a building result) |

### 15.2 Accuracy targets (70% is enough)

| Item | Target | If not met |
|---|---|---|
| Building height | At least 70% of about 30 checked buildings within one storey (3 m) of a known value | Widen the ranges and fall back to GHSL or the type default; say so in the panel |
| Footprint and type | OSM as is | Report completeness for the demo box |
| Budget range | Planning range, about plus or minus 30 to 50% is acceptable | Show wider ranges and the assumptions |
| 3D look | Believable city model of the right place | Fidelity badge stays |
