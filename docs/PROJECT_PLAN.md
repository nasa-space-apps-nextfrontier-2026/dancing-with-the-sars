# CIVISAR: Project Plan

NASA Space Apps Challenge 2026, challenge **"Dancing with the SARs"** (NASA NISAR).

This document records what we are building and why. It is a product and research plan only. It contains no software architecture and no code. Those come later.

> Status: planning. Facts marked **(unverified)** came from press releases, team repositories or secondary sources and must be checked before we rely on them. Dataset availability over our study areas has **not yet been confirmed** (see section 13).

---

## 1. Summary

CIVISAR is a satellite-powered decision-support map for **war-affected regions**. It uses NASA NISAR radar (SAR) data, plus other NASA and partner-agency data, to answer one question:

> In a war-affected area, what was damaged, who is affected, which services still work, how serious is it, and where can emergency teams and displaced people go?

It is aimed at emergency services, humanitarian coordinators and analysts. It is not aimed at the public, and it is never a targeting tool.

## 2. Scope decisions

| Decision | Detail |
|---|---|
| War only | No floods, earthquakes, landslides or other natural disasters. Rainfall data is used only to rule out rain as the cause of a radar change. |
| No rebuilding | Reconstruction plans, recovery action cards and rebuild tracking are out of scope. They are not part of the challenge use cases. |
| No live vehicle tracking | Not technically possible with this data (NISAR and Sentinel-1 give snapshots every 6 to 12 days). It would also be dangerous in a war because it amounts to tracking convoys, evacuations and aid. |
| No Chinese sources | Space Apps rules bar participation through, or collaboration with, China or Chinese-owned entities. Avoid Chinese-owned datasets, APIs and companies. |
| NASA data first | At least some NASA or partner-agency (ESA, ISRO) open data is needed to qualify for Global Judging. Everything used is cited. |
| One combined map | One map with switchable layer groups and one click panel, instead of a separate map per problem. |

## 3. What already exists (and why damage detection is not our pitch)

Existing tools already map damaged buildings and building types: UNOSAT, Conflict Ecology (automated InSAR damage portal), UNDP RAPIDA, Copernicus EMS, Microsoft HASTE, NASA ARIA, and open Sentinel-1 methods (PWTT and others). WorldPop gives population, OSM gives roads, and night-light maps show blackouts.

Judges will see damage detection as a solved problem. CIVISAR therefore **uses damage as an input** and goes further, to human impact and emergency action:

- How serious the damage is for people, ranked per neighbourhood.
- Who has lost access to a working hospital, water or power.
- Routes responders can navigate, with population and service context for the destination.
- Estimated displaced people, and candidate shelter and urgent-work sites with calculated capacity and needs.

We still reproduce basic damage mapping, because the challenge requires NISAR use, and we check it against UNOSAT and UNDP reference data.

## 4. Study areas

| Priority | Area | Why | Caveat |
|---|---|---|---|
| Main | **South Lebanon** | Documented building damage from Sentinel-1 work and UNDP/CNRS-L assessments gives reference data. Public NISAR data starts 17 June 2026, so it mainly shows the period after fighting paused. | Confirm NISAR scenes over south Lebanon in ASF Vertex first. |
| Backup | **Gaza** | Richest reference data (UNOSAT, UN-Habitat, FAO, WHO). | Highest risk of harm. Show only in restricted, delayed mode. |
| Extra | **Kyiv** | A same-track NISAR stack exists for September to October 2026 **(unverified)**. Suits the power, water and hospital chain. | |
| Not planned | Sudan (El Fasher), Iran | Strong reference work, but NISAR coverage unconfirmed. | |

If NISAR scenes do not cover south Lebanon, switch the main case to Gaza.

## 5. Features

### 5.1 Damage and severity
- Candidate damaged areas from NISAR (change strength, coherence loss, cluster size, persistence across passes). Sentinel-1 and OPERA products fill gaps.
- Map severity to UNOSAT classes: destroyed, severely damaged, moderately damaged, possibly damaged.
- Validate against UNOSAT, UNDP and Conflict Ecology data for the same area.
- Radar shows candidates, not confirmed damage. Wording must reflect that.

### 5.2 Affected buildings and facilities
- Classify buildings by type (OSM, healthsites.io): hospitals, clinics, schools, homes, places of worship, water plants and pumps, power substations.
- Overlay reports of attacks on facilities (WHO, Insecurity Insight).
- Each facility gets a status of damaged, working or unknown, with source and date.
- **Never infer "working" from radar alone.** An independent test of a damage model on health facilities found only 42.9% sensitivity. "No detected damage" is not "open".

### 5.3 People affected
- Population per affected area from WorldPop (about 100 m) and NASA SEDAC GPWv4 (about 1 km), with children, elderly and women where available.
- Always shown as a range and an estimate, never an exact count.
- Population living in destroyed or severely damaged buildings gives an estimated displaced figure. Use the UNOSAT housing-unit approach: destroyed and severely damaged count 100%, moderately damaged 50%, possibly damaged 20%.

### 5.4 How serious is it (severity ranking)
Per neighbourhood, combine five parts and **show them separately next to a total rank** so responders can see why an area ranks high:
1. Damage level
2. Population living there
3. Critical facilities hit
4. Power or water lost
5. Roads cut

This is close to UN-Habitat's Gaza neighbourhood scoring. Our difference is that the score comes from NISAR, updates with each 12-day pass, and feeds routing and shelter planning.

### 5.5 Services: power, water, coverage
- Power: night-light loss from NASA Black Marble. **Use NOAA-20/21 (VJ146A1/A2), not Suomi NPP**, which stopped delivering data on 2 November 2026 **(unverified)**. Light loss can overstate real electricity loss.
- Water: locate plants and pumps (OSM) and check which are damaged. Show the chain substation, water pump, hospital.
- Network coverage: shown only where data exists.
- Fires after strikes: NASA FIRMS.

### 5.6 Roads, routes and navigation
- Each road is labelled **open, closed or unknown**, from official and humanitarian reports plus radar-detected possible damage on roads and bridges.
- A responder picks an area, sees routes to the nearest working hospital or shelter that avoid confirmed closures, picks one and starts navigation (in-app or in the phone's map app).
- Alongside the route: population at the destination, power status, water points, coverage and facility status.
- Routes are labelled **"no reported closure", never "safe"**, and are visible only to logged-in responders.
- Show which neighbourhoods are cut off from health care.

### 5.7 Population movement
Individuals cannot and must not be tracked. Feasible aggregate signals:

| Signal | Data | Shows |
|---|---|---|
| Lights dropping or appearing | Black Marble | Where activity fell or rose (proxy only) |
| New tent or camp areas | NISAR or Sentinel-1 change on open land | Camp growth |
| Reported displacement | IOM DTM, UNHCR | Official aggregate numbers |
| Estimated displaced | Section 5.3 | People who probably lost their homes |

Output is aggregated and delayed, and never shows exact camp locations publicly.

### 5.8 Shelter and urgent-site finder
- **Demand:** displaced people from section 5.3.
- **Supply:** candidate sites from filters: open land (HLS, MODIS land cover), flat ground (NASADEM slope), no NISAR change, not wet (OPERA DSWx), near a road (OSM), near working water and health care, away from damage clusters, and large undamaged buildings (schools, halls).
- **Capacity (Sphere standards):** at least 45 m² of site area per person for temporary camps. At least 3.5 m² of covered space per person in warm climates and 4.5 to 5.5 m² in cold climates. At least 15 litres of water per person per day. 40 to 60 litres per inpatient per day at health centres. One tap stand per 250 people.
- Example output: "Site X: 12 ha, holds about 2,600 people, 1.2 km from the main road, nearest working clinic 2 km. Needs about 39,000 L of water a day."
- Sites are **candidates for checking only**. The tool cannot know military danger, front lines or explosive ordnance. They go only to authorised coordinators, and a protection and explosive-ordnance check is required before any site is used.

### 5.9 Explosive hazard warning
UNMAS and mine-action data, aggregated to areas, shown as a warning on shelter sites and return areas. It is the main hidden barrier to people returning after a war.

### 5.10 Return readiness (stretch view)
Per neighbourhood: housing, explosive risk, water, power, health access, roads. Each is ✓, ✗ or unknown with its source and date. The output is "what still blocks return here", never "safe". Optional, and shown only if time allows.

## 6. The combined map

One base map with switchable layer groups:

- 🔴 Damage (severity from NISAR)
- 👥 People (density, affected, displaced)
- 🏥 Facilities (type and status)
- ⚡💧 Services (power, water, coverage)
- 🛣 Roads and routes
- ⛺ Shelter and urgent sites
- 📍 Movement (aggregated)

Clicking an area opens one panel with damage level, population affected, facilities hit, power and water status, roads and the nearest shelter options. NASA GIBS and Worldview provide ready-made layers (night lights, fires, true colour) for a fast, strong visual.

## 7. AI agents

All numbers come from real data and GIS calculations. The AI never invents numbers.

| Agent | Job |
|---|---|
| Damage | NISAR change analysis and severity levels |
| Impact | Population, affected and displaced estimates, facilities hit |
| Services | Power from night lights, water, coverage |
| Route | Routes, and recalculation when new closures are confirmed |
| Shelter | Finds sites, calculates capacity and needs |
| Movement | Night-light change, camp growth, DTM |
| Corroboration | Compares radar changes with incident reports, tracks whether sources are independent |
| Orchestrator | Connects the agents. A new strike updates routes, then shelters, then the brief. A derived claim never carries a higher evidence level than its weakest input. |
| Report | Writes a plain-language emergency brief with sources |
| Safety | Blocks anything that breaks the rules in section 9 |

## 8. Evidence labels

Every claim carries a label, a source and a date:

- **Observed**: seen directly in data.
- **Reported**: stated by an external source.
- **Corroborated**: radar change plus an independent report.
- **Unknown**: no evidence.

A radar change alone is only a candidate. A report alone is only reported.

## 9. Safety and do-no-harm rules

War damage tools can be misused for targeting. These are product requirements, not footnotes:

1. Civilian objects only. No military sites, no front-line movement.
2. No public list of what is still standing, especially power, water and health sites.
3. New strike detections are released with a delay of days, not hours, and aggregated to neighbourhood level.
4. Shelters, displacement sites and aid routes are never shown publicly.
5. Emergency routes and shelter candidates go only to logged-in, authorised users.
6. No live vehicle or convoy data.
7. Never label anything "safe".
8. The safety agent reviews every output before release. In the demo, deliberately try to extract shelter locations and show that it fails.

## 10. Datasets and sources

### 10.1 NASA and partner-agency (core, cite all)

| Need | Dataset | Notes |
|---|---|---|
| Damage detection | NISAR L2 GCOV / GSLC via ASF | Required. 12-day repeat. Public provisional data starts with acquisitions on or after 17 June 2026. |
| Backup and extra dates | OPERA RTC-S1, DIST-S1 (from ESA Sentinel-1) | Partner-agency data. |
| Power cuts | Black Marble VJ146A1/A2 (NOAA-20) | Daily, about 500 m. |
| Fires | FIRMS | Near real time. |
| Population | SEDAC GPWv4 and WorldPop | GPWv4 about 1 km. Age and sex version only for 2010. WorldPop about 100 m. |
| Roads | OSM (main), SEDAC gROADS (backup) | gROADS covers only 1980 to 2010. Cross-check use only. |
| Land, slope | NASADEM, MODIS land cover, HLS | For the shelter finder. |
| Water or wet ground | OPERA DSWx | Excludes unsuitable shelter sites. |
| Rain check | GPM IMERG | Rules out rain as a cause of radar change. |
| Map layers | NASA GIBS / Worldview | Ready-made layers for the map. |

### 10.2 Supporting (non-NASA) data
UNOSAT damage assessments (reference, on HDX), UNDP/CNRS-L Lebanon assessments, WHO attacks-on-health-care data, Insecurity Insight (HDX), UNMAS explosive-ordnance assessments, IOM DTM and UNHCR displacement data, OSM buildings, hospitals and schools, healthsites.io, WHO HeRAMS (facility functionality), OCHA HDX, Logistics Cluster access maps, Pacific Institute Water Conflict Chronology.

### 10.3 NASA sites reviewed
- Earthdata Search: main source.
- Worldview / GIBS: map layers.
- data.nasa.gov: search and citations only. Mostly points back to Earthdata.
- api.nasa.gov: mostly not useful (space APIs). EONET is natural events only.
- Exoplanet Archive and Open Innovation: not relevant.

## 11. Known data limits

- **NISAR latency:** standard products arrive 36 to 72 hours after acquisition. CIVISAR is a day 2 to 3 and later tool, not a first-hours alert.
- **Urgent Response products** (about 4 to 6 hours) exist only for some events and are deleted after 30 days.
- **NISAR anomaly:** no acquisitions from 28 July to 9 August 2026 **(unverified)**.
- Radar reliability drops over vegetation. Damage estimates are minimums.
- OSM road completeness varies and changes access-loss results.

## 12. What to build (48-hour scope)

1. NISAR damage severity map for one area (required).
2. Affected population and estimated displaced.
3. Facility types hit, such as hospitals and schools.
4. Emergency route to a working hospital, with the info panel.
5. Shelter finder showing two or three candidate sites with capacity.
6. Night-light power layer via Worldview/GIBS (easy visual win).

Smaller parts of the demo: movement signals, the full agent system, explosive hazard warning and return-readiness view.

## 13. Open items and next steps

1. **Confirm NISAR coverage** over south Lebanon, Gaza and Kyiv in ASF (scene counts and dates). Not yet done.
2. **Check the NASA Space Apps resources page**, released 13 November 2026. Look for named scenes or areas, a ready-made change-detection notebook, and a NASA source we can cite.
3. Verify the items marked **(unverified)**.
4. Check access to each supporting dataset (HDX, WHO, UNMAS, IOM) and what coverage exists for the chosen area.
5. Decide the demo form (notebook, web map, or both) and then write the architecture.
6. Pick the evaluation method: compare severity classes against UNOSAT or UNDP data for the same area.
7. Prepare the safety-agent demonstration.
