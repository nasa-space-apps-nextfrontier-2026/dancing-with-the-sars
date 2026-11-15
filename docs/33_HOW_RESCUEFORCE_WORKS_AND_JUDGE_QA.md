# 33 · How RescueForce works: data, live status, methods and judge Q&A

Status: 15 Nov 2026 (Thanoban). One place to prepare the presentation. Every number below comes from the code or a file in this repo; the file is named so anyone can check it. Where something is a plan or a demo drawing, it says so.

**One line:** RescueForce turns free satellite data (radar, night lights, fires) plus open maps (buildings, population, facilities) into a ranked list of places that may need help, with the reasons, the uncertainty and suggested next checks. **It suggests; a person decides.**

---

## 1. Product in one minute

- **Landing page** (`/`): the story (3D Earth → dive to the affected area → what responders see) and the "Try RescueForce" button.
- **Dashboard** (`/map`): 3D, 2D and split map. Incident ranking, insights, decision assistant, rebuild budget, building and shelter details, a satellite-pass timeline and a Sources panel.
- **No sign-in** (team decision, 15 Nov 2026, PR #47): the public demo shows **labelled sample data**. Real released data needs a separate public-release step on the backend (doc 31).
- Rules everywhere: evidence labels **Observed / Reported / Corroborated / Unknown**; numbers as **ranges**; damage and routes are **candidates / not verified**; never the word "safe"; no vehicle or phone tracking; a missing input is **Unknown, never 0**.

---

## 2. Data: what each source is, how we get it, and is it live?

"Dataset" = files we download and process. "API / feed" = a service we query. "Live" = updated automatically on a schedule.

| Data | Provider | Dataset or API | How we get it | What we use it for | How fresh (honest) |
| --- | --- | --- | --- | --- | --- |
| **NISAR L2 GCOV** (L-band radar) | NASA–ISRO | Dataset, found with an API | ASF Search API finds granules (336 over south Lebanon); Earthdata Login downloads; Colab crops to the demo box | Radar change → damage candidates | Each pass repeats about every **12 days**; products arrive **days** after the pass. **Not live**; near-real-time is a scheduled job, not built yet |
| **OPERA RTC-S1** (Sentinel-1 C-band) | ESA / NASA JPL | Dataset via ASF | Same as NISAR | **Second sensor**: does a second radar agree? | Sentinel-1 about every 6–12 days; same latency idea |
| **FIRMS VIIRS 375 m** active fire | NASA | Public CSV **feed** (no key) | `worker/services/firms_feed.py`; scheduler fetches **every 30 minutes** | Fire points with a 375 m uncertainty ring | **Live** (near real time: hours after the satellite overpass). Real run 14 Nov: 2 detections in 7 days |
| **Black Marble** VJ146A2 / VJ246A2 (+ near real time) | NASA (NOAA-20, NOAA-21) | Dataset via NASA CMR search + LAADS/LANCE download | `worker/services/blackmarble_history.py`, scheduler **daily** | Night lights → **possible power loss** | **Daily**, near real time keeps ~7 days; archive lags 1–2 weeks. Real history: 230 nights, 7,546 cells |
| **WorldPop 2020** (constrained + unconstrained) | University of Southampton | Static dataset | `worker/loaders/population.py` sums the rasters per H3 cell | People per area, as a **range** (low = smaller of the two, high = larger) | **Not live.** A 2020 pre-war estimate; displacement is not in it |
| **OpenStreetMap** buildings, roads, facilities | OSM community | Dataset (extract) | Loaders in `worker/loaders/`, `pipelines/buildings/` | Footprints (268,536 in the demo box), building use, hospitals/schools/water/fuel | Snapshot; **not live** |
| **GHSL GHS-OBAT** building heights | EU JRC | Static dataset | `pipelines/buildings/heights.py` | Height and floors when OSM has no levels | About **2018** (pre-war stock) |
| **Esri World Imagery** | Esri | Map tiles | Loaded by the map | Satellite background | Capture dates vary by tile; **not the incident date** (credit line says so) |
| **Cesium ion** World Terrain, OSM Buildings | Cesium | Tiles (free token) | Loaded by the map | 3D terrain and buildings | Map context only |
| **World Bank** damage assessments | World Bank | Public reports | Read by hand into `worker/agents/budget_assumptions.json` | Cost per m² for the budget | 2025 reports |

### What is real and what is sample in the demo?

| Part | Public demo (website) | Backend real-data mode (doc 31) |
| --- | --- | --- |
| Damage candidates | Sample (`civisar-3d-sample.json`) | **Real** M1 radar results for the demo box: 13,669 areas, 52,786 cell results |
| Fires | Sample points | **Real** FIRMS feed every 30 min |
| Power loss | Sample cells | **Real** Black Marble rule when the night history is on the machine |
| Population, buildings, facilities | Sample values | **Real** WorldPop, OSM, GHSL tables |
| Ranking, insights, assistant, budget | Sample text | **Real** agents run on the real tables (`worker/agents/`) |
| Routes, shelters | **Demo drawings only** (see section 7–8) | Not built yet |

**Short answer for judges:** fires and night lights are live feeds; radar damage is real but arrives per satellite pass (days, not minutes); population and buildings are fixed pre-war datasets. The public website shows labelled sample data so nobody mistakes it for a live operational picture.

### Can it become a live detection system?

Yes, step by step, and the plumbing exists (`worker/scheduler.py`):
1. **Already scheduled:** fires every 30 min, night lights daily (`python -m worker.scheduler`).
2. **Next:** a job that checks ASF every day for new NISAR / Sentinel-1 passes over the area, runs the processing and the model, and publishes new candidates (the code for each step exists in `pipelines/radar/nisar/`; it runs by hand on Colab today).
3. **Limits we cannot remove:** radar only sees an area when the satellite passes (days apart); processing takes compute; building changes show about **72 hours** after a pass in the UI. So "live" means **near real time per satellite pass**, not CCTV.

---

## 3. How we detect damage (radar)

Files: `pipelines/radar/nisar/` (features, `model.py`, `evaluate.py`, `s1_check.py`).

1. Take NISAR radar images **before and after** for the same track and frame; crop to the demo box; correct for terrain.
2. For every H3 cell (about 0.1 km²) compute change features: drop in HH and HV backscatter, polarisation change, share of strongly dropping pixels, built-up density (and coherence drop when available).
3. **Isolation Forest** (unsupervised anomaly model), trained only on quiet built-up cells. It learns what "normal change" looks like and scores how unusual each cell is.
4. Thresholds are quantiles of the quiet scores: **possible** (95th), **moderate** (99th), **severe** (99.9th). These are *anomaly classes*, not probabilities and not proof of collapse.
5. **Second sensor:** check the same cells in Sentinel-1 (OPERA RTC). Agreement → **Corroborated**; one radar only → **Observed**.
6. A cell with no detection is stored as "nothing detected", **never** "no damage".

Why radar: it sees through cloud and smoke, day and night. Limits: it misses some damage and flags some change that is not damage; classes are per cell and apply to every building in the cell.

---

## 4. How we detect possible power loss (night lights), and the "night" question

Files: `worker/services/nightlights.py`, `power_loss.py`, `blackmarble_history.py`.

**Night lights are measured only at night, by design.** The VIIRS Day/Night Band on NOAA-20 and NOAA-21 photographs the lights after dark (around 1:30 am local; the two satellites pass about 50 minutes apart). Black Marble cleans each night (moonlight, clouds, snow, quality flags). So:
- **We judge each night against the same place's own normal nights.** For every cell: baseline = median brightness of its last **60 clear nights** (at least 30 needed).
- **Possible power loss** = the cell is **below 50 % of its baseline on 2 clear nights**.
- Too little evidence (cloud, moon, too few nights, a very dark area under 0.5 nW/cm²/sr such as sea or fields) → **Unknown**, never a guess.
- **Two satellites:** one satellite alone flags 2.7 % of assessable cell-nights; both satellites agreeing flags only **0.73 %** (measured on 59,868 real cell-dates). Both agree → confidence medium/high (**Corroborated**); one only → low.
- During the **day** nothing new can be measured; the map shows the result of the **latest clear night**, with its date ("last lit night"). A daytime outage is only seen the following night.
- Wording is always "**possible** power loss", never "blackout", and never a claimed cause.

---

## 5. Fires

File: `worker/services/firms_feed.py`, `fires.py`. NASA FIRMS VIIRS 375 m detections from the public CSV feed every 30 minutes. Each point gets a **375 m uncertainty ring** (the sensor's pixel size). Evidence = **Observed**. The flames and smoke on the map are an **illustrative effect** at the real point; size is not a measured fire size. A fire is "fire detected", never a cause.

---

## 6. Building details

Files: `pipelines/buildings/base.py`, `heights.py`, `table.py`.

| Field | How we get it |
| --- | --- |
| Footprint, use | OpenStreetMap building outline and `building=` tag (GHSL use where OSM only says `yes`) |
| Height range | 1) OSM `building:levels` × 3 m ±10 %; else 2) GHSL GHS-OBAT height (2018), range −3 m to +4.5 m (GHSL mean error 2.89 m, tends to underestimate); else 3) a default range for the use. Each row says where it came from; estimated heights are labelled |
| Floors | height ÷ 3 m, as a low–high range |
| Residents | from WorldPop people in the cell, shared over the residential floor area (range). In the public demo it is a **sample formula** |
| Facility flag | OSM tags (hospital, clinic, school, water, power) |
| Damage class, evidence, second sensor | from the radar cell the building sits in (section 3) |

Heights describe the building stock **before** the war, not what stands today.

---

## 7. Routes: available and possibly blocked

**Current demo:** route lines are **sample drawings** (Udula removed calls to the public OSRM demo server; doc 03 forbids sending locations to external routing services). Earlier mockups showed real-road routes from OSRM; that is not in the product now.

**Method (planned, offline):**
1. Road network from the **OpenStreetMap** extract, routed locally (no external service, no location leaves the server).
2. Any road segment within about **35–40 m of a damage-candidate cell** is marked **"possibly blocked (candidate)"** (red dashed). Fire rings (375 m) are flagged on the route too.
3. A route that avoids those segments is shown as **"available, not verified"** (white). Never "safe": radar cannot see debris on a road, craters, checkpoints or fighting.
4. The officer chooses the route; field reports can confirm or close a road.

---

## 8. Shelters: how we find candidate sites

**Current demo:** shelter pins and capacities are **sample** ("Sample shelter N"). Real place names are not labelled as shelters on a public page.

**Method (planned):**
1. **Candidates** = large public buildings from OSM: schools, community halls, mosques and churches, sports halls, other public buildings (tags such as `amenity=school`, `amenity=community_centre`, `building=public`).
2. **Distance and route** from the incident by road (local routing, section 7).
3. **Capacity range** = floor area (footprint × floors range, section 6) ÷ **3.5 m² per person** (Sphere humanitarian standard for covered living space), reduced for corridors and services. Always a range.
4. **Hazard check**: inside or near (300 m) a damage candidate, inside a fire ring, or in a dark (possible power loss) cell → shown as tags.
5. Label: **"candidate shelter, not verified"**. Someone must check the site is open, intact and reachable before use. Shelter details are restricted to coordinators in the backend roles (doc 07).

---

## 9. How we rank incidents (prioritise)

File: `worker/agents/ranking.py`, weights in `ranking_weights.json` (editable; must add up to 100).

Score 0–100 from seven named parts:

| Part | Weight | How it is measured |
| --- | --- | --- |
| People | 30 | WorldPop residents (high end) ÷ 2,000, capped at 1 |
| Facility | 20 | OSM facility inside a damage-candidate cell: hospital, clinic, water, power = 1.0; school = 0.6 |
| Damage | 15 | Worst candidate class (severe 1.0, moderate 0.6, possible 0.3) × 0.75 if only one radar |
| Fire | 15 | Fire detected: 1.0 if two satellites, 0.7 if one |
| Services | 10 | Possible power loss: 1.0 if both satellites, 0.5 if one (water and internet: no data yet) |
| Time | 5 | Hours an alert has been unreviewed ÷ 72, capped at 1 |
| Access | 5 | Unknown today (no road data loaded) |

**Unknown is never zero:** a part without data makes the score a **range**: low = unknown parts count 0, high = unknown parts count in full. Incidents are ordered by the low end (what is known), then the high end, then people. A wide range is flagged "could rank higher". Ranking only orders; it never hides an incident. Every incident shows "why ranked here".

---

## 10. Decision assistant and insights

- **Assistant** (`worker/agents/assistant.py`): rules only, no generative AI. For a ranked incident: a situation line, 2–3 options from fixed playbooks, trade-offs, what we do not know, a checklist, and when to look again. It never dispatches, never changes data, and only prints numbers its inputs contain. Every suggestion is **Unverified** with a reason; the officer can mark it checked or dismiss it.
- **Insights** (`worker/agents/insights.py`): 3–5 template sentences from computed values, each with its evidence label, source and date.

---

## 11. How we calculate the rebuild budget

Files: `worker/agents/budget.py`, `budget_assumptions.json`. Label: **"Planning indication only", never a quote.**

**Cost range = affected floor area × damage share × cost per m²**
- Floor area: footprints × floors (low end uses low floors, high end high floors), residential and non-residential separately.
- Damage share (team rule): destroyed/severe 100 %, moderate 50 %, possible 20 %.
- Cost per m² (USD 2025), anchored to the **World Bank Syria damage assessment (Aug 2025)**: housing about US$600/m² → range **450–900**; non-residential about US$800/m² → **600–1,200** (−25 % to +50 % because Lebanese costs are likely higher; to be checked against the World Bank Lebanon RDNA, March 2025).

**Duration range = start delay + work volume ÷ (crews × m² per crew per month)**
- Start delay 3–9 months (assessment, rubble and unexploded-ordnance clearance), crews 10–40 per neighbourhood, 150–300 m² per crew per month. These three are **assumptions** (no public source) and are editable.

Context: the World Bank Lebanon RDNA (7 Mar 2025) puts total recovery needs at about US$11 billion; it is shown for context, not used in the formula. Limits: radar misses/over-flags damage, heights are estimates, costs come from Syria and are adjusted.

---

## 12. Evidence labels

| Label | Meaning in RescueForce |
| --- | --- |
| **Observed** | Seen by one sensor (one radar, one night-light satellite, a FIRMS detection) |
| **Reported** | From a person or report (field team, municipality, media) |
| **Corroborated** | Two independent sources agree (e.g. NISAR + Sentinel-1, NOAA-20 + NOAA-21) |
| **Unknown** | Not enough evidence; shown as a gap, never as 0 or "no damage" |

---

## 13. Likely judge questions (short answers)

1. **Is this live?** Fires (every 30 min) and night lights (daily) are live feeds. Radar damage updates per satellite pass (days). Population and buildings are fixed datasets. The public demo uses labelled sample data.
2. **Is the data real?** Yes in the backend: real NISAR, Sentinel-1, FIRMS, Black Marble, WorldPop, OSM, GHSL. The public site uses sample data on purpose, because it is not an operational system.
3. **How do you know a building is damaged?** We don't claim to: radar change that is unusual compared with quiet areas becomes a *candidate*; a second radar can corroborate it; a person must verify.
4. **What about night: how do you detect power cuts?** Night lights are only measured at night (~1:30 am). Each cell is compared with its own last 60 clear nights; below 50 % on 2 clear nights = possible power loss; two satellites must agree for high confidence; daytime shows the latest night's result.
5. **Why radar?** It sees through cloud and smoke, day and night.
6. **How accurate is it?** Night-light rule: 0.73 % flagged when both satellites agree (vs 2.7 % single). Radar classes are anomaly quantiles (95/99/99.9 %); field validation is still needed. We show ranges and Unknown instead of false precision.
7. **How do you prioritise?** Seven weighted parts (people 30, facilities 20, damage 15, fire 15, services 10, time 5, access 5); missing data widens the range instead of counting as zero; every rank has its reasons.
8. **How is the budget calculated?** Floor area × damage share × World Bank cost per m², as a range; durations from crews and delays; labelled "planning indication only".
9. **How do you find routes and shelters?** Planned: OSM roads routed locally, roads near damage flagged "possibly blocked"; shelters are OSM schools, halls and places of worship with capacity from floor area (3.5 m²/person). In the demo both are sample drawings, always "not verified".
10. **Is it AI?** The damage model is machine learning (Isolation Forest). The agents (ranking, insights, assistant, budget) are transparent rules and formulas, not a chatbot, so every output can be traced.
11. **Privacy and safety?** No tracking of people or vehicles; no external routing calls with locations; alerts are stored per neighbourhood; real places are not labelled as shelters publicly; nothing is called "safe".
12. **What is the population number?** WorldPop 2020, two models; we show the smaller and larger as a range. It is pre-war, so it does not include displacement.
13. **Costs and keys?** All data is free and open. Keys: Earthdata login (free), Cesium ion token (free). No paid APIs.
14. **What would you build next?** Daily automatic radar job, local road routing, real shelter capacities, field-report input to raise or lower evidence, and validation against ground truth.

---

## 14. Where to look in the repo

| Topic | Files |
| --- | --- |
| Sources list | `docs/progress/SOURCES_AND_TOOLS_USED.md` |
| Radar model | `pipelines/radar/nisar/` |
| Night lights, fires | `worker/services/` |
| Population, facilities | `worker/loaders/` |
| Buildings | `pipelines/buildings/` |
| Agents (ranking, budget, assistant, insights) | `worker/agents/` |
| Backend real-data mode | `docs/31_BACKEND_REAL_DATA.md` |
| UI and frontend | `docs/26_3D_MAP_UI_AND_FRONTEND.md`, `frontend/README.md` |
