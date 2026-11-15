# 26 · 3D map UI and frontend

Status: 15 Nov 2026 (Thanoban). **Replaces the light prototype as the UI source of truth.** The old prototype is archived at `docs/design/archive/civisar-prototype-v1-light.html`.

## 1. Files

| File | What it is |
| --- | --- |
| `docs/design/civisar-3d-map-mockup.html` | Clickable mockup of the main map screen. **UI source of truth.** |
| `docs/design/civisar-3d-sample.json` | All sample data, shaped like the future API. Each top-level key maps to one endpoint. |
| `docs/design/.env.cesium.js` | Your own Cesium ion token (`window.CESIUM_ION_TOKEN = "…"`). Git-ignored by the `.env.*` rule. Never commit it. |
| `docs/design/archive/` | Old designs, kept for history only. |
| `frontend/` | The real React app, built from the mockup (section 6). |

Run the mockup: in `docs/design`, run `python -m http.server 8765`, open `http://localhost:8765/civisar-3d-map-mockup.html`. Without a token it still works (flat ground, no 3D buildings).

## 2. Screen layout

Map-first. The map fills the screen; everything else is a glass panel at the edges, nothing over the scene centre.

- **Top bar:** brand, pages (Map, Alerts, Areas, Sources; the last three are placeholders), Satellite/Streets base map, 2D/3D/Split, Focus mode, "Fly to top incident", signed-in user.
- **Left rail + drawer:** Incident ranking, Decision assistant, Rebuild budget, Layers, Legend (6 items, on demand).
- **Right panel (incident):** tabs Summary, Impacts, Shelters, Power, Insights. Opens a Building detail (click an OSM building) or a Shelter detail (click a shelter).
- **Bottom dock:** camera flight phases (Regional, Descent, Arrival), satellite pass date slider (missed passes marked, "building changes appear 72 h after the pass"), Orbit 360, Reset.
- Compact type: 13.5 px body, Inter + JetBrains Mono. Colour only for evidence, damage class, route status, fire and power.

## 3. Map and camera

- **Engine: CesiumJS** for 3D, 2D and split (one engine keeps selection, date and layers in sync).
- Start on the globe, fly to the South Lebanon bird view, then a cinematic fly-to on pin click: one continuous eased flight (descend, tilt, slight turn, slow arrival). Reduced-motion users get an instant cut.
- Controls: drag to orbit, scroll to zoom, Orbit 360, Reset. No camera panel.
- Base map: Esri World Imagery (free) or OpenStreetMap streets, plus an Esri "Streets & labels" overlay. Credit line shows source and that capture dates vary.
- Terrain and OSM 3D buildings from Cesium ion (free Community account). Building colours come from the OSM `building:material` / `roof:material` / `building` tags, else a neutral stone tone. Never random, never invented buildings.

## 4. Layers and effects

| Layer | How it shows |
| --- | --- |
| Damage candidates | Hatched ground cell + hatched pulsing volume around the building, ground pulse ring, dust haze (destroyed/severe), label "class (candidate) · evidence". Overlays never change building colours. |
| Second sensor | Dashed green ring. |
| NISAR change cells | Purple outline. |
| Fires | Real fire points only: layered core, flames, tongues, embers, smoke and plume moving with wind gusts, flickering ground glow. Label "illustrative effect". 375 m dashed uncertainty ring. |
| Night lights | Dark cells hatched violet: "possible power loss" (never "blackout"). Off by default. |
| Population | WorldPop cells with people ranges. |
| Facilities | Badges: H hospital, + clinic, S school, W water, F fuel. |
| Candidate shelters | Dashed-outline pins, always visible. Route from the selected incident to each shelter. |
| Routes | Follow real OSM roads (free OSRM demo server; falls back to the sample lines if it can't be reached). Available = white line "not verified". Any part within ~35 m of a damage candidate = red dashed "possibly blocked (candidate)". Recomputed when the date changes. |

Every layer must show in **2D, 3D and split**.

## 5. Agent outputs (suggest only, the officer decides)

1. **Incident ranking:** score range and "why ranked here" factor breakdown.
2. **Insights:** 3-5 findings with evidence label and source date.
3. **Decision assistant:** overview counts, next checks (Unverified tag, mark checked, dismiss), route options with length / nearest damage / nearest fire, shelters to consider, data gaps.
4. **Rebuild budget:** low–high range per area with assumptions, "indicative, not a quote".
5. **Summary card:** People, Facilities, Roads, Power as ranges, each with "Show on map", plus "Check before acting".
6. **Impacts, Shelters, Power** tabs as in the mockup. Shelter detail gives coordinates (decimal and DMS, copy), OSM link, road distance and route warning.

## 6. Frontend build (`frontend/`)

- React + Vite + TypeScript, **CesiumJS** (replaces MapLibre).
- **No sign-in (decided 15 Nov 2026, PR #47).** `/` is the RescueForce landing page and `/map` the dashboard, both public with labelled sample data. The sign-in screen was removed. See doc 33 for what is real, sample and live.
- Data comes from `src/services/api.ts`. Real sessions load the authenticated, released and area-scoped `/api/v1/map/context` bundle. Explicitly synthetic sessions load the sample JSON copied to `frontend/public/sample/civisar-3d-sample.json` and show the "Sample data" badge; real failures never silently become fixture success.
- Cesium token: `VITE_CESIUM_ION_TOKEN` in `frontend/.env.local` (git-ignored).

## 7. Real vs sample

Real library behaviour: globe, terrain, OSM buildings, camera flights, particles, imagery, OSRM road routing. Sample: every incident, score, damage cell, fire point, night-light and population cell, facility, shelter, capacity, budget and suggestion. Resident counts in building detail are a rough sample formula.

## 8. Rules (unchanged)

Evidence labels Observed / Reported / Corroborated / Unknown. Ranges, not single numbers. Never "safe". No live vehicle or phone tracking. No sign-in in the public app (15 Nov 2026). Damage and routes are always "candidate" / "not verified".

## 9. Camera motion (agreed 15 Nov 2026)

- **Start:** the whole Earth on black space with stars (no sun/moon sprites). Wait until the globe imagery has loaded (max 6 s), hold ~1.5 s, then a 7 s flight rotates the globe into the South Lebanon bird view.
- **Fly-to:** Regional → Descent → Arrival → **360° view**. One flight at a time: a newer flight cancels the older one. If the camera is already low, it rises to a regional height first so it never skims through terrain.
- **Arrival:** one slow full turn around the incident (~30 s, eased in), then stop. The camera stays **anchored** on the incident: drag orbits around it, scroll zooms towards it. Grabbing the map stops the turn but keeps the anchor.
- **Orbit 360** button: continuous turn from where the camera is, no jump. **Reset** and **Show on map** release the anchor first.
- All motion is time-based (same speed at any frame rate). Reduced-motion users get instant cuts and no automatic turn.

## 10. When an area gets affected (response flow)

Proposed 15 Nov 2026, agreed in chat. Every step keeps the rules: candidates, not facts; ranges; never "safe"; the officer decides.

1. **Detect.** Each new satellite pass (NISAR, Sentinel-1), FIRMS fire update and Black Marble night-light update is compared with the previous one. New change cells, fires or dark cells create a **candidate incident**. Evidence starts as Observed (sensor) or Reported (field or media report).
2. **Group and score.** Candidates within about 1.5 km merge into one incident. The ranking agent gives a score range with its "why ranked here" factors. A pin and an alert appear.
3. **Assess impact (automatic).** As the Summary tab: people (WorldPop range), facilities inside or near damage / fire / dark cells, roads possibly blocked, possible power loss, rebuild budget range.
4. **Suggest, never decide.** The decision assistant lists next checks, route options on real roads and the nearest candidate shelters (location, capacity range, route warnings). All tagged Unverified.
5. **Officer acts.** Mark checks done, dismiss suggestions, choose a route and a shelter. Every action is logged with who and when (in the backend). No vehicle or phone tracking.
6. **Verify and update.** A field report or a second satellite agreeing upgrades evidence to Corroborated; a contradiction drops it to Unknown. The 72 h building-change delay and missed passes are shown, never hidden.
7. **Monitor.** On the next pass the incident updates (grows, shrinks or settles), routes are recomputed, and new blocked roads or dark cells raise a new alert.
8. **Close and hand over.** A coordinator marks the incident resolved and can be printed as an area brief with sources. Rebuild planning uses the budget range, labelled "indicative, not a quote".

**Decided:** only a **coordinator** (or admin) can mark an incident resolved; officers can mark checks done and propose closing.

**Decided:** alerts are shown **in the app only** (alert feed and pins). No SMS or email.
