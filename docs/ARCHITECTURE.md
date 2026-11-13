# CIVISAR: Architecture and Build Plan

What we will build in the 48-hour hackathon, how, and who does what. Features are in [PROJECT_PLAN.md](PROJECT_PLAN.md), screens in [UI_DESIGN.md](UI_DESIGN.md), data in [DATASETS.md](DATASETS.md) and [DATA_AND_API_PLAN.md](DATA_AND_API_PLAN.md).

Facts marked **(check)** must be confirmed before or at the start of the hackathon.

---

## 1. Ground rules

| Rule | Meaning |
|---|---|
| **48 hours** | Every part must be buildable by our team in one weekend. Anything that isn't goes on the stretch list (section 9). |
| **Free only** | Open-source software, free accounts and free API tiers. No paid services. |
| **One unsupervised model, no supervised training** | Damage is found by an **anomaly model** trained on our own radar data from quiet areas (section 4). No supervised damage classifier, because no damage labels exist for our area and period (section 4.1). |
| **No big downloads we don't need** | Radar files are large (measured: GCOV 0.85 GB, GUNW 2.3 GB, GSLC 6.4 GB each). We download in tiers and start at hour 0 (section 3). |
| **Radar pre-computed, alerts live** | Radar processing runs once, early. Fires, night lights and internet outages are fetched live. Both use the same code. |
| **One demo area** | South Lebanon, NISAR **track 151 descending, frame 72**. |
| **Safety rules** | PROJECT_PLAN.md section 10 applies everywhere: no "safe", area level only, routes and shelters for logged-in roles only. |
| **No Chinese-owned sources** | Space Apps rule |

## 2. What the demo shows (MVP)

These seven things must work on demo day:

1. **NISAR damage map** for south Lebanon: before (Jan 2026) vs after (Jun 2026), with a time slider over the later passes, and candidate damage classes per neighbourhood.
2. **People and facilities:** residents (pre-displacement estimate, as ranges) and facilities hit, per area.
3. **Alerts:** fires (live), possible power loss (daily night lights), internet disruption (live).
4. **Area summary** with "what to bring", printable from the browser.
5. **Route options** (2–3, in or out) for a logged-in officer.
6. **Shelter candidates** (buildings first, then open land) for a logged-in coordinator.
7. **Sources page** and **sign-in with demo roles**, including the safety demo: an analyst asking for shelters is blocked.

## 3. Data: what we download, in order

### 3.1 Radar (biggest time risk: start at hour 0)

| Tier | Files (track 151D frame 72) | Size | Gives us |
|---|---|---|---|
| **A (must)** | NISAR **GCOV**: 6 dates before (27 Oct 2025 → 19 Jan 2026) + 3 after (24 Jun → 18 Jul 2026) | about **7.7 GB** | Backscatter before/after: the main damage map |
| **B (must)** | NISAR **GCOV**: the 8 later dates (11 Aug → 3 Nov 2026) | about **6.8 GB** | Time slider |
| C (should) | NISAR **GSLC** 19 Jan + 24 Jun 2026, and **GUNW** 7 Jan 2026 | about **15 GB** | Coherence drop across the escalation, the strongest damage signal |

- Download with `earthaccess` (free Earthdata Login) on the machine with the fastest internet, as soon as the hackathon starts. Tiers A and B first.
- **Crop each file to the demo box right after download** and share only the crops (a few hundred MB) with the team.
- If the Space Apps rules allow preparing data before the weekend, download tier A and B in advance **(check the rules)**.

### 3.2 Everything else (small, fast)

| Data | Access | Size |
|---|---|---|
| HOTOSM buildings and roads, Lebanon | HDX download | about a few hundred MB **(check)** |
| WorldPop R2025A, Lebanon, 2026, 100 m | WorldPop website | small |
| OCHA admin boundaries (8 governorates, 26 districts, 1,627 cadasters) | HDX | small |
| GHSL building height (one tile) | JRC website | small |
| NASADEM (two or three tiles) | Earthdata | small |
| Black Marble VJ146A2 / VJ246A2 (+ NRT) | Earthdata, daily files | small per day |
| FIRMS fires | FIRMS API (free map key) | tiny |
| IODA outages | IODA API (no key) | tiny |
| ACLED, Insecurity Insight | ACLED API (free account **(check terms)**), HDX | small |

Nothing else is downloaded: no Sentinel-2, no Sentinel-1 SLC, no models.

## 4. Damage method: an anomaly model trained on our NISAR data

### 4.1 Why not a normal (supervised) damage classifier

A supervised model learns from examples marked "damaged" and "not damaged". It needs many of them, at the same places and dates as our radar images. We checked every source on 13 Nov 2026:

| Possible label source | Result |
|---|---|
| UNOSAT damage assessments for Lebanon (HDX) | **None exist** |
| UNOSAT Gaza assessments | Newest is 11 Oct 2025, but NISAR's first pass over Gaza was 27 Oct 2025. The damage happened before NISAR could see it, so there is no before/after pair. |
| UNOSAT Caracas earthquake (24 Jun 2026, NISAR passes right around it) | The shapefile is 17 KB, far too small to hold building-by-building damage for a city |
| UNDP / CNRS-L or World Bank assessments for 2026 | None found **(check again at hour 0)** |
| Strike reports (ACLED, Insecurity Insight) as labels | A reported strike doesn't mean a building collapsed, locations are approximate, and we need these reports to **test** the model. Training on them too would be circular. |
| Making our own labels from optical images | Needs Sentinel-2 downloads and many hours of hand labelling, and 10 m images only show heavy destruction. Not realistic in 48 hours. |

Without labels, a supervised model has nothing to learn from, and we couldn't show judges that it works. So we train a model that **doesn't need labels**.

### 4.2 The idea

Between January and June, every built-up area changes a little in the radar for ordinary reasons: winter vs summer, wet vs dry ground, vegetation, and the switch from BETA to PROVISIONAL processing. A collapsed or heavily damaged area changes in a different, stronger way.

So we **train a model on quiet areas** (no reported strikes) to learn what normal change looks like, then ask it how unusual every other area is. Unusual change with a collapse-like signature becomes candidate damage.

This also fixes two problems for free: the BETA → PROVISIONAL offset and the season change are part of "normal" because quiet areas have them too.

### 4.3 Steps

1. **Cells:** H3 resolution 9 cells (about 0.1 km²) that are built up (enough OSM building area inside). Mask water, radar shadow and steep slopes; masked cells are "Unknown".
2. **Features per cell** (medians over the built-up pixels inside, so single noisy pixels don't matter):

   | Feature | Meaning |
   |---|---|
   | HH change | After minus before, in dB, using the average of 6 before dates and 3 after dates (averaging cuts radar noise) |
   | HV change | Same for HV |
   | HH−HV change | Change in the polarization difference. Collapse often lowers HH (lost wall–ground corners) and raises HV (rubble). |
   | Strong-drop share | Share of pixels in the cell whose HH fell by more than 3 dB (catches partial collapse inside a cell) |
   | Coherence drop | Only if tier C arrived: 12-day coherence before minus coherence across the gap |
   | Incidence angle, building density | Context, so "normal" is learned for each kind of place, not one average |

3. **Quiet cells for training:** built-up cells with no ACLED or Insecurity Insight event within 2 km between 19 Jan and 24 Jun 2026. If fewer than about 500, widen to the rest of the frame. Some quiet cells may still have unreported damage; the model is set to tolerate a small share of those.
4. **Model:** **Isolation Forest** (scikit-learn), trained on the quiet cells. It needs no labels, makes no assumption about the shape of the data, and trains in seconds on a laptop CPU. A robust Mahalanobis distance (MinCovDet, also scikit-learn) is computed alongside as a cross-check and because it's easy to explain ("this many standard units from normal").
5. **Damage-like or not:** an unusual cell becomes **candidate damage** only if its change points the collapse way (HH down, or coherence down). Unusual cells pointing the other way are labelled **"other change"** (for example new structures or tents), not damage.
6. **Classes from known false-alarm rates:** thresholds come from the quiet cells' own scores, so we know the false-alarm rate of each level:

   | Score above this share of quiet cells | Class shown | Confidence |
   |---|---|---|
   | 99.9% | Destroyed / severely damaged (candidate) | Higher |
   | 99% | Moderately damaged (candidate) | Medium |
   | 95% | Possibly damaged (candidate) | Low, unless a second source agrees |

7. **Why each cell was flagged:** store each feature's distance from normal. The Inspector shows "HH dropped strongly, coherence dropped", not just a score.
8. **Time slider:** refit the same model for each later pass against the June baseline (seconds per pass), so new changes after June show up with the right season as "normal".
9. **Display:** compute at resolution 9, publish at resolution 8 (about 0.7 km²), as the safety rules require. Building-level results are shown only as "candidate".
10. **Fallback:** if the model behaves badly, use simple z-score thresholds on the same features (same output format, an hour of work).

### 4.4 How we show it works (on the Sources page)

| Test | Pass if |
|---|---|
| **Hold-out quiet areas:** train on 80% of quiet cells (split by area blocks), score the other 20% | About 1% flagged at the 99% level, as designed |
| **Strike enrichment:** share of flagged cells within 1 km of reported strikes vs far from them | Much higher near strikes. Also compared within the same district, so terrain differences don't explain it. |
| **Look at the top cells:** open the 20 highest-scoring cells on the radar images | Most show a clear, compact change, not stripes or edges (radio interference, file edges) |
| Sentinel-1 agreement (stretch) | Flagged cells also changed in Sentinel-1 |

Known limits, stated in the app: radar misses some damage (intact roofs), so counts are minimums; "quiet" areas may hide unreported damage; scores are candidates, never confirmed damage.

Output: a coloured change image per pass (for the map) and one row per cell (class, score, confidence, top features, dates).

## 5. Other data processing

| What | How | When |
|---|---|---|
| Area units | H3 hexagons: resolution 9 (about 0.1 km²) for calculating, resolution 8 (about 0.7 km²) for display; cadasters for summaries | Once |
| Residents | WorldPop 2026 spread over residential buildings by floor area. Shown as a range and labelled "pre-displacement estimate". | Once |
| Affected and displaced | Residents × damage class shares (destroyed and severe 100%, moderate 50%, possible 20%) | After damage |
| Facilities | OSM hospitals, clinics, schools, water and power sites. "Damaged" from the damage map; "working" only if reported; otherwise "No detected damage. Not confirmed open." | After damage |
| Road graph | OSMnx from HOTOSM roads. Segments near damage = "unknown status"; officer-reported closures = "closed". | Once, then on each closure |
| Routes | 2–3 different shortest paths avoiding closures, with the seven facts (PROJECT_PLAN.md 6.5). Computed on our server only. | On request |
| Shelters | Large public buildings with no detected damage; floor area = footprint × levels (OSM, else GHSL height ÷ 3 m, else a default); open land = OSM land use, flat (NASADEM), near a road | After damage |
| Night lights | Per cell, clear nights only (the archive repeats old values on cloudy nights). Below 50% of the 60-night baseline on 2 clear nights → "Possible power loss". | Daily |
| Fires | FIRMS NOAA-20/21, low-confidence and permanent hot spots removed, grouped within 1 km and 12 h → "Fire detected" (never a cause) | Every 30 min |
| Internet | IODA outage events for South Lebanon and An Nabatiyah governorates | Every 30 min |
| Alerts | One alert per event with area, time, source and label, plus residents within 1 and 3 km and facilities nearby. Two independent sources agreeing → "Corroborated". | After each live fetch |

All "agents" in the plan are these steps written as Python functions. None of them use an LLM, so no number is ever made up.

## 6. Backend

| Part | Choice |
|---|---|
| API | **FastAPI** (Python) |
| Database | **PostgreSQL + PostGIS** in one Docker container: areas, values, facilities, roads, alerts, closures, users |
| Map layers | Pre-made files, served by the API: radar change images as map tiles (made with GDAL), vector layers as **PMTiles** (made with tippecanoe), small changing layers (alerts, routes, shelters) as GeoJSON |
| Live jobs | One Python worker on a timer: fires, IODA, night lights. Each keeps its last good result and shows "Cached" if the source fails. |
| Sign-in | Simple token login with four demo accounts: analyst, officer, coordinator, admin. Logged out: the public-safe map only (UI_DESIGN.md section 6). |
| Access checks | In every API endpoint and on every layer file: routes need officer, shelters need coordinator. Radar results are held for 72 hours after a pass. |
| Where it runs | One team laptop or the GPU machine, with Docker Compose. Public link through a free **Cloudflare Tunnel**. Backup: second laptop and a recorded video. |

Every stored value carries: area ID, low, high, evidence label, source, date and safety tag. The Sources page and "trace a value" read these.

Main endpoints: login, status (data freshness), layers, area summary, alerts, facilities, routes, shelters, report closure, sources, trace.

## 7. Frontend

| Part | Choice |
|---|---|
| App | **React + Vite** |
| Map | **MapLibre GL JS** (free, open source) |
| Base map | NASA **GIBS** imagery and reference labels (free, no key), plus our own OSM roads and buildings |
| Design | Tokens, symbols and wording from UI_DESIGN.md |
| Phone | Same app, responsive layout for alerts, area summary and routes |
| Print | Browser print of the area summary (no PDF service) |

Screens, in build order:

1. **Sign-in** and the **logged-out view** (decided in UI_DESIGN.md section 6: login required; logged out shows only the public-safe map with data layers and area-level results)
2. **Main map:** layer list, time slider (Before / After / Change), alert feed, area pop-up
3. **Area summary** with "what to bring" and print
4. **Alert detail** (1 km and 3 km rings, facilities, routes button)
5. **Routes** (A/B/C options and the seven facts)
6. **Shelters** (space-per-person setting, ranked list, warnings)
7. **Sources** (datasets, dates, validation numbers)

The frontend starts on **mock JSON** from hour 2, using the agreed shapes (section 8.2), and switches to the real API around hour 24.

## 8. Team plan

### 8.1 Roles

| Team | Skills | Owns |
|---|---|---|
| **Radar** | ML / remote sensing | Sections 3.1 and 4: download, crop, features, anomaly model, change images, tests |
| **Data** | Python / data | Sections 3.2 and 5: buildings, residents, facilities, roads, shelters, live jobs, alerts |
| **Backend** | Backend / DevOps | Section 6: database, API, sign-in, access checks, layer files, Docker, tunnel |
| **Frontend** | Web frontend | Section 7: all screens |
| **Demo** (one person, part time) | Anyone | Story, demo script, video, Space Apps submission page |

### 8.2 Agree at hour 2 (so everyone can work in parallel)

1. **Area IDs:** H3 resolution 9 and 8, and cadaster codes from the OCHA boundaries.
2. **Value row:** `area_id, metric, low, high, unit, label, source, date, safety_tag`.
3. **File names and formats:** change images per pass, PMTiles layers, GeoJSON for alerts, routes and shelters.
4. **API JSON shapes** for area summary, alert, route option and shelter, with one mock example each.

### 8.3 Before the hackathon (accounts and checks only)

- Everyone: free **Earthdata Login** account.
- One person each: **FIRMS map key**, **ACLED account**, **IOM DTM key**, **Cloudflare** account.
- Read the **Space Apps rules** on what may be prepared before the weekend.
- Test the internet speed on the download machine. At 20 Mbit/s, tiers A + B (14.5 GB) take about 1.6 hours.
- Install Docker, Python and Node on the machines.

### 8.4 Timeline

| Hours | Radar | Data | Backend | Frontend |
|---|---|---|---|---|
| 0–2 | Start tier A+B downloads | Download small data | Repo, Docker, database | App skeleton, map with GIBS |
| 2 | **Agree IDs, rows, files and JSON shapes (8.2)** | | | |
| 2–8 | Crop, mask, version offset | H3 grid, buildings, residents, facilities | Tables, sign-in, roles | Main map with mock layers |
| 8–16 | Features per cell, quiet cells, anomaly model, classes (tier C download in background) | Road graph, live jobs (fires, IODA, lights) | Endpoints with mock data, layer files | Time slider, alert feed, area pop-up |
| 16–24 | Change images, time slider passes | Shelters, alerts, join with damage | Real data loaded, access checks | Area summary, alert detail |
| **24** | **Everything on real data. Check what works.** | | | |
| 24–32 | Add coherence (if tier C arrived), refit; the four tests in 4.4 | Routes with seven facts, closures | Routes, shelters, closures endpoints; tunnel | Routes, shelters, sources screens |
| 32–38 | Fix classes, Sources text | Fix data errors | Safety demo test, freshness strip | Phone layout, print, polish |
| **38** | **Feature freeze. Only fixes from here.** | | | |
| 38–44 | Help test | Help test | Backup laptop set up | Fixes |
| 40–44 | Demo person records the video | | | |
| 44–48 | Submission page, final checks, rest | | | |

## 9. If time is short, cut in this order

1. Gemini assistant (stretch only, below)
2. Coherence (tier C): keep the backscatter-only damage map
3. Phone layout and print styling
4. Shelter open-land search (keep buildings)
5. Time slider passes after July (keep before/after)

Never cut: the NISAR damage map, sign-in with roles, the safety rules.

### Stretch goals (only after hour 38 if everything above works)

- **Question box using the Gemini API free tier** (free key, nothing to install). Only the question is sent; our code builds the answer from our data. Restricted data never goes to the API.
- Sentinel-1 (OPERA RTC-S1) cross-check
- Movement trend (IOM DTM, Meta)
- Second radar view (track 172 ascending)
- Offline saved summaries
