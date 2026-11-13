# CIVISAR: UI Design and Outputs

**This is the CIVISAR UI design:** https://claude.ai/artifact/6or9wWJWrdVx1kz3LQzbdw#components

It is a design system made with Claude Design. It holds the screens, components, colours, type and wording rules. The screens are mockups with **illustrative demo data**, and every map in them carries a badge saying so. The real app rebuilds the map with a real map library and keeps the same symbols, tokens and wording.

This file explains what CIVISAR produces (its outputs) and where each output appears in the design. See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the features and [DATASETS.md](DATASETS.md) for the data.

---

## 1. App form

- **Web app only.** No separate mobile app. Users are officers and coordinators, mostly on laptops.
- **Works on phones in the browser** for the three field views: alerts, area summary and routes (screen *ScreenMobile*).
- **Installable with offline briefs** (PWA): saved area summaries and routes still open with poor signal, with the time they were saved.
- Light and dark themes. Dark is for night shifts. The print brief is always black on white.

## 2. What CIVISAR outputs

Every output comes from real data and GIS calculations. AI agents never invent numbers.

| # | Output | What it is | Made by | Shown in |
|---|---|---|---|---|
| 1 | **Data map layers** | NISAR change, Sentinel-1 change, night lights, fires, internet outages, people density, buildings, roads, conflict events, reported attacks, validation overlay | Processing steps (DATASETS.md section 5.3) | ScreenMainMap layer rail, "Data layers" |
| 2 | **Agent result layers** | Damage classes, facility status, services lost, affected and displaced, shelter candidates, route options, movement trend, new alerts | AI agents (plan section 8) | ScreenMainMap layer rail, "Agent results" (listed first) |
| 3 | **Area tables** | One row per neighbourhood or grid cell: damage, people, services, facilities. Each value has low/high range, evidence label, source and date. | Pre-computed once per NISAR pass | Read by agents; behind every panel |
| 4 | **Agent result records** | One small record per result, for example `{area, result, people_low, people_high, label, source, date}` | Each agent | ScreenInspector rows, SourceLine |
| 5 | **Alerts** | Fire detected, night-light drop (possible power loss), internet outage, building change from radar, conflict event reported | Alert agent, automatically | ScreenMainMap alert feed, AlertCard, ScreenAlertDetail |
| 6 | **Area summary** | People ranges, what to bring, vulnerable groups, facilities hit, hazards, nearest hospital and shelters, route options | Report agent | ScreenAreaSummary |
| 7 | **Print / offline brief** | One A4 page of the area summary, with numbered source footnotes and a QR code to the live view | Report agent | ScreenAreaBrief |
| 8 | **Route options** | 2–3 inbound or outbound options with seven facts each, and a turn list for the chosen one | Route agent | ScreenRoutes, RouteOption, route popup |
| 9 | **Shelter candidates** | Ranked buildings then open land, with capacity at the chosen space per person | Shelter agent | ScreenShelters, ShelterCard |
| 10 | **Sources and citations** | Every dataset with provider, use, newest date, cadence and the evidence label it produces; "Trace a value" from a number back to its agent and datasets | Dataset records (DATASETS.md section 7) | ScreenSources |

### 2.1 How outputs are stored (data rules, not architecture)

- Rasters (radar change, night lights): Cloud-Optimized GeoTIFF, one per pass.
- Shapes (buildings, areas, routes, alerts): GeoJSON, or vector tiles when large.
- Area tables and agent records: simple tables or JSON with stable area IDs, so every screen and agent joins by ID.
- Every stored value carries its evidence label, source, date and safety tag.

## 3. Screens

| Screen | Answers | Main outputs used |
|---|---|---|
| **ScreenMainMap** | What is happening across the whole area right now? | 1, 2, 5 |
| **ScreenAlertDetail** | A fire was detected. Who and what is around it, and how do we get there? | 5, 2, 8 |
| **ScreenAreaSummary** | What happened here and what should we bring? | 6, 8, 9 |
| **ScreenAreaBrief** | The same, as a one-page offline or print brief | 7 |
| **ScreenRoutes** | Which way in or out, and what is on each option? | 8 |
| **ScreenShelters** | Where could displaced people go? (candidates for checking) | 9 |
| **ScreenInspector** | Every agent result for this building or area, with sources | 4 |
| **ScreenSources** | Where does each number come from? | 10 |
| **ScreenMobile** | Alerts, area summary and routes on a phone | 5, 6, 8 |

Fewest clicks: any place, alert or facility → its routes (1 click). Alert → detail (1) → compare routes (2). Map → area callout (1) → summary (2) → print (3).

### 3.1 Screen notes

- **Main map.** Top bar with a data-freshness strip (NISAR, Sentinel-1, night lights, fires, internet). Layer rail on the left with Agent results first, then Data layers, NASA first. NISAR radar change has a CORE tag and HH / HV / HH−HV, track and opacity controls. Map in the middle with the time slider under it. Alert feed on the right, newest first, with type filters. Both side panels fold into narrow icon rails (`[` and `]`). Clicking an area opens a callout with people range, lost services, and buttons for Area summary, Routes and Shelters.
- **Time slider.** 11 passes on track 151 descending (24 Jun – 03 Nov 2026). Missed pass shown dotted, never filled in. Before (dashed) and after (solid) knobs. Views: Before, Change, After, Swipe.
- **Alert detail.** Map with 1 km and 3 km rings, nearby facilities and inbound routes. Panel with "Fire detected", evidence label, a line saying CIVISAR does not determine a cause, detection time (local and UTC), satellite and product, people within 1 and 3 km (ranges), facilities nearby, services already lost and route options. Actions: Compare routes, Area summary, Mark reviewed.
- **Area summary.** The people sentence first, then a "What to bring" row (water lost → water, power lost → generators and lights, health access lost → medical team, comms down → radios). Then vulnerable groups, facilities hit, hazards, nearest hospital and shelters, route options. Print brief, Export PDF and Save offline. No logistics counts.
- **Routes.** Inbound or outbound, from and to, vehicle type. Options A, B, C drawn solid, long dash and dot-dash with letter keys. Comparison table of the seven facts. Turn list and Start navigation inside CIVISAR. A banner and flag when a new closure lands on a route.
- **Shelters.** Space-per-person selector (3.5 m² default; 4.5–5.5 m² cold; 30 m² open site; 45 m² planned camp). Protection and explosive-ordnance banner. Ranked list, buildings first. Selected candidate written as one sentence with facts and sources. Action: Request field check.
- **Inspector.** Floats over the map; Esc closes it. Tabs: All agents, Time series (NISAR HH/HV backscatter for the spot), Validation. One row per agent with result, evidence label and source line.
- **Sources.** NISAR shown as the large core tile with its pass strip, other NASA data next, then the rest.

## 4. Components

| Component | Purpose |
|---|---|
| **EvidenceLabel** | Observed (solid, eye), Reported (outline, quote), Corroborated (double ring), Unknown (dashed, ?). On every result. Told apart by shape and word, not colour alone. |
| **DamageClass** | Destroyed (hatched square), Severely damaged (diamond), Moderately damaged (triangle), Possibly damaged (dashed circle). Always tagged "candidate". |
| **FacilityStatus** | Working (needs a report), Damaged, Unknown, and the separate "No detected damage. Not confirmed open." Markers H, C, S, W, P. |
| **RangeValue** | People estimates as ranges, e.g. 4,000–6,500. Rounded to 100 below 10,000, 1,000 above. |
| **SourceLine** | Dataset · detail · date + DataAge, with a NASA tag on NASA data. Becomes a footnote in print. |
| **DataAge** | Fresh (dot), Aging (ring), Stale (diamond), Cached (dashed ring). Date first, then age. |
| **AlertCard** | One automatic alert: type, place (area level), time, source, label. New alerts get an attention bar, never red or flashing. |
| **RouteOption** | One route with the seven facts in fixed order. Never "safe". |
| **ShelterCard** | One ranked candidate with capacity and "For checking". |
| **TimeSlider** | NISAR pass picker and before/after pair. |
| **LayerToggle**, **MapLegend** | Layer rows with symbol and data age; legend lists only active layers; Focus mode dims data layers when more than 8 are on. |
| **SystemStates** | Loading, no data, unknown, stale, offline, delay notice. |
| **Button** | One primary action per view (Start navigation, Compare routes, Print brief). |

## 5. Visual and wording rules (from the design)

- Quiet neutral background; NASA blue for NISAR and main actions; violet for radar change; amber-brown for attention, not red.
- Colour-blind safe: every status also has a shape, line style or letter.
- IBM Plex Sans for text, IBM Plex Mono for numbers, dates and sources.
- Maps stay readable: agent results above data layers, area layers hatched not solid, outlined points.
- Wording: never "safe" (use "no reported closure"); "Fire detected", never a cause; "Possible power loss", not "blackout"; radar damage is always a candidate; estimates are ranges; shelters are candidates for checking.
- New building changes appear **72 hours after a pass, at neighbourhood level**.
- No vehicle, convoy or phone tracking, and the routes screen says so.

## 6. Differences between the design and the plan (to decide)

| Topic | Plan says | Design says |
|---|---|---|
| Sign-in | Routes, shelters and dispatch reports only after login; demo shows a logged-out user blocked | "There is no sign-in screen" |
| Navigation | In-app turn list, or hand-off to the phone's map app | Navigation inside CIVISAR only, no hand-off to a phone app |
| Delay of new detections | Delayed by days | 72 hours after a pass |
| Fire sources | NOAA-20 and NOAA-21 | Alert card also lists S-NPP |

Until decided, the plan's safety rules (section 10) still apply.
