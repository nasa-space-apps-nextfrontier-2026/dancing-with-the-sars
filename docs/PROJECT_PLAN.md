# CIVISAR: Project Plan

NASA Space Apps Challenge 2026, challenge **"Dancing with the SARs"** (NASA-ISRO NISAR).

This document records what we are building and why. It is a product and research plan only, with no software architecture or code. Those come later. The full dataset list is in [DATASETS.md](DATASETS.md).

> Status: planning. Facts marked **(unverified)** came from secondary sources and must be checked before we rely on them.

---

## 1. Summary

CIVISAR is a satellite-powered emergency decision-support map for **war-affected regions**. It uses NISAR radar data, plus other NASA and partner-agency data, to answer:

> What was damaged, how serious is it for the people there, which services were lost, what do emergency teams need to bring, and which route can they take to get there or to get people out?

Users are emergency services, dispatch officers, humanitarian coordinators and analysts. It is not a public app and never a targeting tool.

## 2. How it fits the challenge

The challenge asks for an **interactive application that uses NISAR radar data to track and visualize one or more types of surface change**, and turns complex radar observations into actionable insights for decision-makers. It names human activities and impacts on infrastructure and communities, and suggests:

| Challenge suggestion | How CIVISAR covers it |
|---|---|
| Use NISAR data (required) | NISAR L2 GCOV/GSLC change detection is the core damage layer |
| Different polarizations and frequencies | Compare HH and HV backscatter change. Cross-check with Sentinel-1 (C-band, via NASA OPERA). |
| Time series from different dates | Time slider over NISAR's 12-day repeat passes |
| Ancillary data (population etc.) | Population, facilities, roads, night lights, fires |
| Human drivers and impact on communities | War damage is human-caused surface change, and the whole tool is about impact on people |
| Interactive maps, image sliders, storytelling | Before/after swipe, combined map, click panel, plain-language briefs |
| Hypothesise the physical drivers | Explain what the radar sees: collapsed buildings change roughness and geometry, which shows as backscatter and coherence change |

## 3. Scope decisions

| Decision | Detail |
|---|---|
| War only | No floods, earthquakes or other natural disasters. |
| Small data set | 14 sources only, each feeding a map layer or an agent result (see [DATASETS.md](DATASETS.md)). |
| No rebuilding | Reconstruction plans and rebuild tracking are out of scope. |
| No live vehicle tracking | Not possible with this data (NISAR and Sentinel-1 give snapshots every 6 to 12 days), and dangerous in a war. |
| No Chinese sources | Space Apps rules bar China or Chinese-owned entities. |
| Resources tab data first | At least one dataset from the challenge Resources tab is needed. Ours is **NISAR** (🟢 linked on the tab). Four more NASA datasets come through the tab's tools, NASA Earthdata Search and ASF Vertex (🔵): OPERA RTC-S1, Black Marble, FIRMS and NASADEM. So 6 of our 14 datasets come from the tab or its tools. Everything used is cited. |
| APIs from the tab tools | NISAR and NASA data are found with the **ASF Search API** (behind ASF Vertex) and the **CMR API** (behind Earthdata Search). They are downloaded with **earthaccess** and an **Earthdata Login** token, as the NISAR Data User Guide describes. Full API plan in [DATASETS.md](DATASETS.md) section 5. |
| One combined map | One map with switchable layer groups and one click panel. |

## 4. What already exists

UNOSAT, Conflict Ecology, UNDP RAPIDA, Copernicus EMS, Microsoft HASTE, NASA ARIA and open Sentinel-1 methods already map war damage. WorldPop gives population, OSM gives roads, and night-light maps show blackouts.

CIVISAR **uses damage as an input** and goes on to the emergency response: how serious it is for people, what they lost, what responders need, where they can go and how to get there. We still produce NISAR damage mapping (the challenge requires it) and check it against UNOSAT and UNDP data.

## 5. Demo area: south Lebanon (design is global)

**The hackathon demo is south Lebanon only**, because judges need one deep, checked example. NISAR coverage was checked on 13 November 2026: 336 granules on three tracks. GCOV passes: track 151 descending has 11 passes (24 Jun to 3 Nov 2026), track 172 ascending 10, track 100 ascending 8. Track 151 is the main time series. Reference damage data comes from UNDP/CNRS-L and UNOSAT. Public NISAR data starts 17 June 2026, so it mostly shows the period after fighting paused.

**How it grows worldwide later.** Every dataset we use is global or near-global, so the same system can watch any area where war is happening:

1. **Watch list of conflict areas, made automatically.** Areas with recent conflict events (ACLED, weekly) are added to the watch list. Analysts can also add areas by hand.
2. **Daily global pre-alerts.** Fires (FIRMS) and sudden night-light drops (Black Marble) are checked every day inside watched areas.
3. **Radar confirmation.** When a new NISAR or Sentinel-1 pass covers a watched area, change detection runs on it.

Radar processing for the whole planet every pass is not needed and is too heavy. Running it only inside watched areas keeps it global and practical. In the demo, south Lebanon is the one watched area.

## 5a. Automatic detection and alerts

The system finds changes by itself. Nobody has to select an area first.

| Trigger | Source | How often | What happens |
|---|---|---|---|
| **Fire detected** | FIRMS VIIRS active fire (near real time) | Several times a day | Fire alert for the area (see below) |
| Night-light drop | Black Marble NRT | Daily | Possible power loss alert |
| Internet outage | IODA | Real time | Comms-loss alert |
| Building change | NISAR (12 days), Sentinel-1 OPERA RTC (a few days) | Each pass | Change area flagged with damage class |
| Conflict event reported | ACLED | Weekly | Context, corroboration |

Alerts appear on a **new alerts list** and on the map. When two independent sources agree (for example a FIRMS fire and a later radar change at the same place), the alert is upgraded to **corroborated**.

### Fire alerts sent to officers
When a fire is detected near people or critical facilities, CIVISAR builds an alert for logged-in officers with:

- where the fire is and when it was detected, with the satellite source;
- people living around it (range) and facilities nearby (hospital, school, fuel, power);
- **available route options** for fire and rescue units to reach it, and for people to leave the area (section 6.5);
- services already lost in that area (power, water, comms).

A satellite fire detection is a heat signal, not proof of a strike. The alert says "fire detected", with its confidence level, and never claims the cause.

## 6. Features

### 6.1 Damage and severity
- Candidate damage from NISAR: backscatter change (GCOV), coherence loss (GSLC), cluster size, and persistence across passes. Sentinel-1 (OPERA RTC) adds dates between NISAR passes.
- Map to UNOSAT classes: destroyed, severely damaged, moderately damaged, possibly damaged.
- Validate against UNOSAT and UNDP data for the same area.
- Radar shows candidates, not confirmed damage, and the wording says so.

### 6.2 Affected buildings and facilities
- Building types from OSM / HOTOSM: hospitals, clinics, schools, homes, places of worship, water plants and pumps, power substations, halls and warehouses.
- Overlay reported attacks on facilities (Insecurity Insight).
- Facility status: damaged, working or unknown, with source and date.
- **Never infer "working" from radar alone.** "No detected damage" is not "open".

### 6.3 People affected and how serious it is
- Population per area from WorldPop, shown as ranges.
- Estimated displaced: people living in destroyed or severely damaged buildings (UNOSAT housing-unit approach: destroyed and severe 100%, moderate 50%, possible 20%).
- Per-neighbourhood severity rank, with its five parts shown separately so responders see why: damage level, people there, critical facilities hit, power or water lost, roads cut.

### 6.4 Services lost
- **Power:** night-light loss from Black Marble NOAA-20/21.
- **Water:** damaged water plants and pumps, and the chain substation → pump → hospital.
- **Health:** nearest working hospital, and who has lost access to one.
- **Communications:** internet outages from IODA.
- **Fires:** active fires from FIRMS.

### 6.5 Emergency routing: both directions, officer chooses

Routing works in **two directions**:

1. **Inbound (dispatch):** get emergency units from their base (ambulance station, civil defence, aid depot) **to the affected area**.
2. **Outbound (evacuation and referral):** get injured or displaced people **from the affected area to** the nearest working hospital or a shelter site.

For each request CIVISAR returns **several route options, not one**. The officer compares them and picks the best one for the situation. Each option shows:

| Route attribute | Why it matters |
|---|---|
| Distance and estimated travel time | Speed |
| Confirmed closures avoided | All options avoid confirmed closures |
| Number and length of **unknown-status** segments | Risk of hitting an unreported blockage |
| Bridges crossed and their status | Bridges are single points of failure |
| Passes near damage clusters, fires or reported attacks | Hazard exposure |
| Date of the newest evidence along the route | How fresh the information is |
| Suitable for heavy vehicles (if road data allows) | Fire engines, water trucks |

The officer selects a route and starts navigation (in-app turn-by-turn, or hand-off to the phone's map app). If a new closure is confirmed, affected routes are flagged and alternatives offered.

Rules: routes are labelled **"no reported closure", never "safe"**. Only logged-in, authorised responders see routes.

### 6.6 Area summary for officers

Each flagged area (from section 5a) has a short summary that answers **"what happened here and what should we bring?"** It stays simple:

| Section | Content |
|---|---|
| People affected | e.g. "About 4,000–6,500 people live here. About 1,200–2,000 probably displaced." |
| Vulnerable groups | Children, elderly, women (ranges) |
| Services lost and what to bring | Water lost → bring water. Power lost → bring generators and lights. Health access lost → send a medical team. Comms down → bring radios. |
| Facilities hit | e.g. 1 clinic damaged, 2 schools possibly damaged |
| Hazards | Fires, reported attacks, unknown road segments |
| Nearest options | Nearest working hospital, candidate shelter buildings |
| Route options | From section 6.5 |
| Evidence | Source and date of every line |

No detailed logistics counts (such as toilets or tap stands). The summary can be shared as a short printable or offline brief.

### 6.7 Shelter and urgent-site finder

**Demand:** displaced people from section 6.3.

**Supply: buildings first, then open land.** In an emergency the quickest shelter is usually an existing building near the affected people, not a new camp.

1. **Nearest suitable buildings** (first choice): any large building with no detected NISAR change near the affected area: schools, halls, community centres, places of worship, sports halls, warehouses, public buildings. Usable floor area is estimated from the OSM footprint × number of levels (`building:levels`), minus a share for walls and corridors.
2. **Open land** (second choice): flat (NASADEM slope), open land with no buildings (OSM land use), near a road, away from damage clusters.

**Capacity uses emergency figures, not long-term camp figures.** The 45 m² per person figure is for long-term planned camps and is too high for an emergency. CIVISAR uses an adjustable setting:

| Mode | Space per person | Source |
|---|---|---|
| Emergency in a building (default) | **3.5 m² covered** (warm climate); 4.5–5.5 m² in cold weather | Sphere minimum covered living space |
| Short-term open site, services outside | 30 m² of site area | Sphere minimum without household plots |
| Planned camp | 45 m² of site area | Sphere / UNHCR |

The officer can change the setting, including warm or cold weather.

Example: "School X: about 2,400 m² usable floor, holds about 680 people at 3.5 m². 900 m from affected area, 1.1 km from nearest working clinic, no detected damage."

Each site also shows distance to affected people, nearest working water and health care, road access, and any hazard warnings. Sites are ranked by how many affected people they can take within a short distance.

Sites are **candidates for checking**. The tool cannot see military danger or unexploded ordnance inside a building. They go only to authorised coordinators, and a protection and explosive-ordnance check is required before use.

### 6.8 Population movement trend (aggregated)

Individuals are never tracked. The movement trend combines:

| Signal | Data | How often |
|---|---|---|
| Daily movement range change | Meta Movement Distribution Maps (HDX, CC BY) | Every 2 weeks |
| Reported displacement | IOM DTM API / HDX | Weekly |
| Lights dropping or appearing | Black Marble NRT | Daily |
| New tent or camp areas | NISAR or Sentinel-1 change on open land | Each pass |
| Estimated displaced | Section 6.3 | Each pass |

Output reads like "people leaving Area A, arriving around Town B", at area level only. Always aggregated and delayed. Exact camp locations are never public.

### 6.8a Comms-loss layer
Internet outages from IODA (real time, country and region level), so summaries can say "internet down since X".

### 6.8b Strike context
ACLED conflict events and FIRMS fires shown next to each radar change. Two independent sources agreeing upgrades a change to "corroborated".

### 6.9 Time view and storytelling
- Time slider over NISAR passes: watch damage appear and spread.
- Before/after swipe of radar images, with GIBS true colour for context.
- Polarization view: what HH and HV each show, as the challenge suggests.
- Short plain-language "what the radar shows and why" notes.

## 7. The combined map

**UI design:** https://claude.ai/artifact/6or9wWJWrdVx1kz3LQzbdw#components. All screens, components and outputs are explained in [UI_DESIGN.md](UI_DESIGN.md). CIVISAR is a web app only (it works in a phone browser and can be installed with offline briefs). There is no separate mobile app.

One base map (NASA GIBS backgrounds) with two kinds of switchable layers: the data itself, and the results the agents produce from it.

### 7.1 Data layers

Marks: 🟢 linked on the Resources tab, 🔵 found and downloaded through a Resources tab tool, ⚪ other source.

| Layer | Dataset | Mark |
|---|---|---|
| NISAR change (time slider, HH/HV) | NISAR GCOV, GSLC | 🟢 |
| Sentinel-1 change | OPERA RTC-S1 | 🔵 |
| Night lights before / after | Black Marble NRT | 🔵 |
| Fires | FIRMS | 🔵 |
| Internet outages | IODA | ⚪ |
| People density | WorldPop | ⚪ |
| Buildings and facilities | OSM / HOTOSM | ⚪ |
| Roads | OSM / HOTOSM | ⚪ |
| Conflict events | ACLED | ⚪ |
| Reported attacks | Insecurity Insight | ⚪ |
| Validation overlay (analyst view) | UNOSAT, UNDP | ⚪ |

NASADEM (🔵) is not its own layer; the Shelter agent uses it for its slope check.

### 7.2 Agent result layers

Each result carries its evidence label (section 9).

| Layer | Agent | Shows |
|---|---|---|
| 🔴 Damage classes | Damage | Buildings coloured destroyed / severe / moderate / possible |
| 🏥 Facility status | Facility | Each hospital, school, water or power site: damaged, working or unknown |
| ⚡💧 Services lost | Services | Areas with power, water or comms lost |
| 👥 Affected and displaced | People | Ranges per area |
| ⛺ Shelter candidates | Shelter | Nearest suitable buildings and open land, with capacity |
| 🛣 Route options | Route | Inbound and outbound options (logged-in responders only) |
| 📍 Movement trend | Movement | Leaving / arriving areas (aggregated) |
| ⚠ New alerts | Alert | Pins for new fires, light drops, outages and radar changes |

Clicking any building or area opens one panel with every agent's result for that spot, the area summary (section 6.6) and the sources behind each line.

## 8. AI agents

All numbers come from real data and GIS calculations. The AI never invents numbers.

| Agent | Job |
|---|---|
| Agent | Job | Reads |
|---|---|---|
| Damage | NISAR change analysis and severity classes | NISAR, OPERA RTC-S1, UNOSAT/UNDP (check only) |
| Facility | Facility type and status | OSM, Damage results, Insecurity Insight |
| Services | Power, water, health access, comms, fires; what to bring | Black Marble, IODA, FIRMS, Facility results |
| People | Population, affected and displaced, severity rank | WorldPop, Damage results, IOM DTM |
| Shelter | Finds buildings and open land, calculates capacity | OSM, NASADEM, Damage and People results |
| Route | Inbound and outbound route options, recalculation on new closures | OSM roads, Damage results, FIRMS |
| Movement | Area-level movement trend | Meta movement, IOM DTM, Black Marble |
| Alert | Finds new changes by itself and raises alerts | FIRMS, Black Marble, IODA, NISAR, OPERA RTC-S1, ACLED |
| Corroboration | Matches radar changes with reports, tracks source independence | ACLED, Insecurity Insight, FIRMS |
| Orchestrator | Connects agents: a new closure updates routes, then reports. A derived claim never carries a higher evidence level than its weakest input. | all results |
| Report | Writes the area summary and briefs in plain language, with sources | all results |
| Safety | Blocks anything that breaks the rules in section 10 | all outputs |

### 8.1 Making the data easy for agents

So agents can work reliably and quickly, the data follows simple shared rules (data conventions, not software architecture):

1. **One area grid.** Every result is stored per neighbourhood or grid cell with a stable ID, so any agent can join layers by ID.
2. **Pre-computed tables.** Damage, population, services, facilities and shelters are calculated once per NISAR pass and stored as tables. Agents read the tables instead of processing raw radar every time.
3. **Every value has a label, source and date.** Each number carries its evidence level (section 9), dataset name and date, so agents can cite it and never present a guess as fact.
4. **Ranges, not single numbers.** Estimates are stored as low and high values.
5. **Dataset records.** Each dataset has a record (name, level, date, version, coverage, licence, URL, Resources tab mark, API used) as listed in [DATASETS.md](DATASETS.md), so agents can explain where data came from.
6. **Fixed question types.** Agents answer a known set of questions, for example: *how many people are affected in area X*, *what services were lost*, *route options from A to B*, *nearest shelter buildings with capacity*, *what changed since the last pass*. This keeps answers checkable.
7. **Safety tags on data.** Sensitive items (shelters, routes, undamaged critical sites) are tagged so the safety agent can block them automatically for unauthorised users.

## 9. Evidence labels

- **Observed**: seen directly in data.
- **Reported**: stated by an external source.
- **Corroborated**: radar change plus an independent report.
- **Unknown**: no evidence.

## 10. Safety and do-no-harm rules

1. Civilian objects only. No military sites, no front-line movement.
2. No public list of what is still standing.
3. New strike detections released with a delay of days and aggregated to neighbourhood level.
4. Shelters, displacement sites, routes and dispatch reports visible only to logged-in, authorised users.
5. No live vehicle, convoy or phone-location data.
6. Never label anything "safe".
7. The safety agent reviews every output. In the demo, try to extract shelter locations as an unauthorised user and show that it fails.
8. Do not publish identifiable population concentrations in an active-conflict context.

## 11. Known data limits

- NISAR standard products arrive 36 to 72 hours after acquisition, so CIVISAR is a day 2 to 3 and later tool.
- Public NISAR data is provisional for acquisitions before 21 October 2026 **(unverified)**.
- NISAR had no acquisitions from 28 July to 9 August 2026 **(unverified)**.
- Radar is less reliable over vegetation. Damage counts are minimums.
- OSM roads and building levels are incomplete in places, which affects routes and shelter capacity.

## 12. What to build (48-hour scope)

1. NISAR damage severity map with time slider for south Lebanon (required).
2. Affected population, displaced estimate and severity rank.
3. Facility types hit.
4. Route options in both directions (dispatch in, evacuation out), with the officer choosing one.
5. Area summary: people affected, services lost and what to bring.
6. Shelter finder: nearest buildings with capacity, then open land.
7. Night-light power layer and fire alerts.
8. Agent result layers on the map (section 7.2).

Smaller demo parts: movement trend, full agent system, polarization story.

## 13. Open items and next steps

1. Each team member makes a free Earthdata Login account (needed to download NISAR). Get the free FIRMS map key and ACLED account.
2. Pick NISAR before/after pairs on track 151 over south Lebanon (ASF Search API).
3. Download UNOSAT / UNDP reference data for the chosen area.
4. Check OSM completeness for roads, buildings and `building:levels` in the area.
5. Verify items marked **(unverified)**.
6. Settle the four differences between the UI design and this plan ([UI_DESIGN.md](UI_DESIGN.md) section 6), then write the architecture. Demo form decided: web app.
7. Prepare the safety-agent demonstration.
