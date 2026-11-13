# CIVISAR: Architecture and Build Plan

What we will build in the 48-hour hackathon, how, and who does what. Features are in [PROJECT_PLAN.md](PROJECT_PLAN.md), screens in [UI_DESIGN.md](UI_DESIGN.md), data in [DATASETS.md](DATASETS.md) and [DATA_AND_API_PLAN.md](DATA_AND_API_PLAN.md).

The build is split into **four main parts**. Each part has one team, clear inputs, clear outputs and a "done when" list:

| Part | Team (skills) | Builds | Hands over to |
|---|---|---|---|
| **1. Radar and damage model** | ML / remote sensing | NISAR downloads, the anomaly model, damage classes, change images | Part 2 (damage per cell), Part 3 (change images) |
| **2. Data and alerts** | Python / data | Residents, facilities, roads, routes, shelters, night lights, fires, internet, alerts | Part 3 (tables, GeoJSON, route and shelter functions) |
| **3. Backend and safety** | Backend / DevOps | Database, API, sign-in and roles, layer files, hosting | Part 4 (API and layers) |
| **4. Frontend and demo** | Web frontend (+ one person for the demo) | All screens, the demo story, video and submission | Judges |

```
Part 1 Radar ──damage per cell──► Part 2 Data ──tables, alerts, routes, shelters──► Part 3 Backend ──API + layers──► Part 4 Frontend
      └────────────────────change images (map tiles)────────────────────────────────────►┘
```

Facts marked **(check)** must be confirmed before or at the start of the hackathon.

---

## Shared by all parts

### Ground rules

| Rule | Meaning |
|---|---|
| **48 hours** | Every part must be buildable in one weekend. Anything else goes on the stretch list. |
| **Free only** | Open-source software, free accounts and free API tiers. No paid services. |
| **One unsupervised model, no supervised training** | Damage comes from an anomaly model trained on our own radar data (Part 1). No damage labels exist for our area and period (Part 1.2). |
| **No big downloads we don't need** | Radar files are large (measured: GCOV 0.85 GB, GUNW 2.3 GB, GSLC 6.4 GB each). Download in tiers from hour 0. |
| **Radar pre-computed, alerts live** | Radar runs once, early. Fires, night lights and internet outages are fetched live. |
| **One demo area** | South Lebanon, NISAR **track 151 descending, frame 72** |
| **Safety rules** | PROJECT_PLAN.md section 10: never "safe", area level only, routes and shelters for logged-in roles only |
| **No Chinese-owned sources** | Space Apps rule |

### What the demo must show (MVP)

1. **NISAR damage map:** before (Jan 2026) vs after (Jun 2026), time slider over later passes, candidate damage classes per neighbourhood. *(Parts 1, 3, 4)*
2. **People and facilities:** residents (pre-displacement estimate, ranges) and facilities hit, per area. *(Parts 2, 3, 4)*
3. **Alerts:** fires (live), possible power loss (daily), internet disruption (live). *(Parts 2, 3, 4)*
4. **Area summary** with "what to bring", printable. *(Parts 2, 3, 4)*
5. **Route options** (2–3, in or out) for a logged-in officer. *(Parts 2, 3, 4)*
6. **Shelter candidates** for a logged-in coordinator. *(Parts 2, 3, 4)*
7. **Sign-in with demo roles, logged-out public-safe view, Sources page**, and the safety demo: an analyst asking for shelters is blocked. *(Parts 3, 4)*

### Agree at hour 2 (so the four parts can work in parallel)

1. **Area IDs:** H3 resolution 9 (about 0.1 km², for calculating) and resolution 8 (about 0.7 km², for display), plus cadaster codes from the OCHA boundaries (8 governorates, 26 districts, 1,627 cadasters).
2. **Value row:** `area_id, metric, low, high, unit, label, source, date, safety_tag`. Every number in the app is one of these rows.
3. **File names and formats:** change image per pass (GeoTIFF → map tiles), PMTiles for buildings, roads and cells, GeoJSON for alerts, routes and shelters.
4. **API JSON shapes** for area summary, alert, route option and shelter, with one mock example each.

### Before the hackathon (accounts and checks only)

- Everyone: free **Earthdata Login** account.
- One person each: **FIRMS map key**, **ACLED account** **(check its free terms)**, **IOM DTM key**, **Cloudflare** account.
- Read the **Space Apps rules** on what may be prepared before the weekend.
- Test the download machine's internet. At 20 Mbit/s, the must-have radar files (14.5 GB) take about 1.6 hours.
- Install Docker, Python and Node.

---

## Part 1. Radar and damage model

**Team:** ML / remote sensing. **Goal:** find candidate war damage in south Lebanon from NISAR, with a model we can prove works.

### 1.1 Downloads (biggest time risk: start at hour 0)

| Tier | Files (track 151D frame 72) | Size | Gives us |
|---|---|---|---|
| **A (must)** | NISAR **GCOV**: 6 dates before (27 Oct 2025 → 19 Jan 2026) + 3 after (24 Jun → 18 Jul 2026) | about **7.7 GB** | Before/after backscatter: the main damage map |
| **B (must)** | NISAR **GCOV**: the 8 later dates (11 Aug → 3 Nov 2026) | about **6.8 GB** | Time slider |
| C (should) | NISAR **GSLC** 19 Jan + 24 Jun 2026, and **GUNW** 7 Jan 2026 | about **15 GB** | Coherence drop, the strongest damage signal |

- `earthaccess` (free Earthdata Login) on the machine with the fastest internet. A and B first, C in the background.
- **Crop each file to the demo box right after download.** Share only the crops (a few hundred MB).
- If the rules allow, download A and B before the weekend **(check)**.

### 1.2 Why not a normal (supervised) damage classifier

A supervised model needs many examples marked "damaged" / "not damaged", at the same places and dates as our radar. We checked every source on 13 Nov 2026:

| Possible label source | Result |
|---|---|
| UNOSAT damage assessments for Lebanon (HDX) | **None exist** |
| UNOSAT Gaza assessments | Newest is 11 Oct 2025; NISAR's first Gaza pass was 27 Oct 2025, so the damage predates NISAR |
| UNOSAT Caracas earthquake (24 Jun 2026) | Shapefile is 17 KB, far too small for building-by-building damage |
| UNDP / CNRS-L or World Bank assessments for 2026 | None found **(check again at hour 0)** |
| Strike reports (ACLED, Insecurity Insight) | A strike isn't a collapse, locations are approximate, and we need these reports to **test** the model |
| Hand labels from optical images | Needs Sentinel-2 downloads and hours of labelling; 10 m images only show heavy destruction |

So we train a model that **doesn't need labels**.

### 1.3 The anomaly model

**Idea:** between January and June every built-up area changes a little in the radar for ordinary reasons (season, wet ground, vegetation, and the BETA → PROVISIONAL software change). A collapsed area changes differently and more strongly. We **train on quiet areas** (no reported strikes) to learn normal change, then score how unusual every other area is. The season and software differences are part of "normal", so they're corrected automatically.

**Steps:**

1. **Cells:** built-up H3 resolution 9 cells. Mask water, radar shadow and steep slopes ("Unknown").
2. **Features per cell** (medians over built-up pixels):

   | Feature | Meaning |
   |---|---|
   | HH change | After minus before in dB (average of 6 before and 3 after dates cuts radar noise) |
   | HV change | Same for HV |
   | HH−HV change | Collapse often lowers HH (lost wall–ground corners) and raises HV (rubble) |
   | Strong-drop share | Share of pixels whose HH fell by more than 3 dB (partial collapse) |
   | Coherence drop | Only if tier C arrived: 12-day coherence before minus coherence across the gap |
   | Incidence angle, building density | Context, so "normal" is learned per kind of place |

3. **Quiet cells:** no ACLED or Insecurity Insight event within 2 km between 19 Jan and 24 Jun 2026. If fewer than about 500, widen to the rest of the frame.
4. **Model:** **Isolation Forest** (scikit-learn, laptop CPU, seconds). Robust Mahalanobis distance (MinCovDet) alongside as a cross-check that's easy to explain.
5. **Damage-like or not:** unusual + collapse direction (HH down or coherence down) = **candidate damage**. Unusual the other way = **"other change"** (new structures, tents).
6. **Classes with known false-alarm rates** (thresholds from the quiet cells' own scores):

   | Score above this share of quiet cells | Class | Confidence |
   |---|---|---|
   | 99.9% | Destroyed / severely damaged (candidate) | Higher |
   | 99% | Moderately damaged (candidate) | Medium |
   | 95% | Possibly damaged (candidate) | Low, unless a second source agrees |

7. **Why flagged:** store each feature's distance from normal ("HH dropped strongly").
8. **Time slider:** refit per later pass against the June baseline (seconds each).
9. **Display level:** compute at resolution 9, publish at resolution 8 (safety rule). Buildings shown only as "candidate".
10. **Fallback:** simple z-score thresholds on the same features (same output, about an hour).

### 1.4 How we prove it works (shown on the Sources page)

| Test | Pass if |
|---|---|
| Hold-out quiet areas (train on 80%, split by area blocks; score 20%) | About 1% flagged at the 99% level |
| Strike enrichment: flagged share near reported strikes vs far, also within the same district | Much higher near strikes |
| Look at the 20 top cells on the radar images | Clear, compact changes, not stripes or file edges |
| Sentinel-1 agreement (stretch) | Flagged cells also changed in Sentinel-1 |

Limits stated in the app: radar misses some damage (intact roofs), so counts are minimums; quiet areas may hide unreported damage; results are candidates, never confirmed.

### 1.5 Delivers

| Output | To | By hour |
|---|---|---|
| Damage table: one row per resolution 9 cell (class, score, confidence, top features, dates) | Part 2 | 16 (first version), 32 (final) |
| Change image per pass (GeoTIFF) | Part 3 | 24 |
| Test results for the Sources page | Part 3 / 4 | 32 |

### 1.6 Done when

- [ ] Tiers A and B downloaded and cropped
- [ ] Damage table and change images for before/after and every later pass
- [ ] Hold-out and strike tests run, numbers written down
- [ ] Top 20 cells checked by eye

---

## Part 2. Data and alerts

**Team:** Python / data. **Goal:** turn the damage into people, facilities, routes, shelters and live alerts.

### 2.1 Downloads (small, fast)

| Data | Access | Size |
|---|---|---|
| HOTOSM buildings and roads, Lebanon | HDX | a few hundred MB **(check)** |
| WorldPop R2025A, Lebanon, 2026, 100 m | WorldPop website | small |
| OCHA admin boundaries | HDX | small |
| GHSL building height (one tile) | JRC website | small |
| NASADEM (two or three tiles) | Earthdata | small |
| Black Marble VJ146A2 / VJ246A2 (+ NRT) | Earthdata, daily | small per day |
| FIRMS, IODA, ACLED, Insecurity Insight | APIs / HDX | tiny |

### 2.2 What it builds

| What | How | When |
|---|---|---|
| Area grid | H3 resolution 9 and 8 over the demo box; cadasters | Once |
| Residents | WorldPop 2026 spread over residential buildings by floor area. Range, labelled "pre-displacement estimate". | Once |
| Affected and displaced | Residents × damage shares (destroyed and severe 100%, moderate 50%, possible 20%) | After each damage update |
| Facilities | OSM hospitals, clinics, schools, water and power sites. "Damaged" from Part 1; "working" only if reported; else "No detected damage. Not confirmed open." | After damage |
| Road graph | OSMnx from HOTOSM roads. Near damage = "unknown status"; officer-reported = "closed". | Once, then per closure |
| Routes | Function: 2–3 different shortest paths avoiding closures, with the seven facts (PROJECT_PLAN.md 6.5). Runs on our server only. | On request |
| Shelters | Large public buildings with no detected damage; floor area = footprint × levels (OSM, else GHSL height ÷ 3 m, else a default); open land = OSM land use, flat (NASADEM), near a road | After damage |
| Night lights | Per cell, clear nights only. Below 50% of the 60-night baseline on 2 clear nights → "Possible power loss". | Daily |
| Fires | FIRMS NOAA-20/21, low confidence and permanent hot spots removed, grouped within 1 km and 12 h → "Fire detected" (never a cause) | Every 30 min |
| Internet | IODA outages for South Lebanon and An Nabatiyah governorates | Every 30 min |
| Alerts | One per event (area, time, source, label) with residents within 1 and 3 km and facilities nearby. Two independent sources → "Corroborated". | After each live fetch |

All the plan's "agents" (Damage, Facility, Services, People, Shelter, Route, Alert) are these Python functions. None use an LLM, so no number is made up. Every live job keeps its last good result and marks it "Cached" if a source fails.

### 2.3 Delivers

| Output | To | By hour |
|---|---|---|
| Area grid, residents, facilities (value rows + PMTiles source files) | Part 3 | 12 |
| Live jobs (fires, IODA, lights) as Python functions | Part 3 | 16 |
| Alerts, shelters, affected and displaced (joined with Part 1) | Part 3 | 24 |
| Route function and closure handling | Part 3 | 32 |

### 2.4 Done when

- [ ] Every area has residents, affected, displaced and facility counts as value rows
- [ ] Live jobs run on a timer and fall back to "Cached"
- [ ] Routes return 2–3 options with the seven facts
- [ ] Shelters ranked, with capacity at 3.5 m² per person by default

---

## Part 3. Backend and safety

**Team:** Backend / DevOps. **Goal:** one API that serves everything, with the safety rules enforced on the server.

### 3.1 Stack

| Part | Choice |
|---|---|
| API | **FastAPI** (Python) |
| Database | **PostgreSQL + PostGIS** in Docker: areas, values, facilities, roads, alerts, closures, users |
| Map layers | Pre-made files served by the API: change images as map tiles (GDAL), vector layers as **PMTiles** (tippecanoe), small changing layers as GeoJSON |
| Live jobs | One Python worker on a timer, running Part 2's functions |
| Where it runs | A team laptop or the GPU machine, Docker Compose. Public link: free **Cloudflare Tunnel**. Backup: second laptop + recorded video. |

### 3.2 Endpoints

Login, status (data freshness), layers, area summary, alerts, facilities, routes, shelters, report closure, sources, trace a value.

### 3.3 Safety on the server

| Role | Sees |
|---|---|
| Logged out | Public-safe map: data layers and area-level results only (UI_DESIGN.md section 6) |
| Analyst | Damage, people, services, alerts, validation |
| Officer | + routes, closure reports |
| Coordinator | + shelter candidates |
| Admin | + users and audit log |

- Checks in **every endpoint and on every layer file**, not just in the screens.
- Radar results held for 72 hours after a pass.
- API keys (FIRMS, ACLED, DTM, Earthdata) only on the server.
- Every value keeps its label, source, date and safety tag, so the Sources page can trace it.

### 3.4 Delivers

| Output | To | By hour |
|---|---|---|
| Running API with mock data, sign-in and roles | Part 4 | 12 |
| Real data loaded, layer files served | Part 4 | 24 |
| Routes, shelters, closures endpoints; public link | Part 4 | 32 |

### 3.5 Done when

- [ ] All endpoints return real data
- [ ] An analyst asking for shelters gets "not allowed", from the API itself
- [ ] Logged-out users see only the public-safe map
- [ ] Public link works; backup laptop ready

---

## Part 4. Frontend and demo

**Team:** web frontend, plus one person (part time) for the demo. **Goal:** the screens judges use, and the story they hear.

### 4.1 Stack

| Part | Choice |
|---|---|
| App | **React + Vite** |
| Map | **MapLibre GL JS** (free) |
| Base map | NASA **GIBS** imagery and labels (free, no key), plus our OSM roads and buildings |
| Design | Tokens, symbols and wording from UI_DESIGN.md |
| Phone | Responsive layout for alerts, area summary and routes |
| Print | Browser print of the area summary |

### 4.2 Screens, in build order

1. **Sign-in** and **logged-out view**
2. **Main map:** layer list, time slider (Before / After / Change), alert feed, area pop-up
3. **Area summary** with "what to bring" and print
4. **Alert detail** (1 km and 3 km rings, facilities, routes button)
5. **Routes** (A/B/C options, the seven facts)
6. **Shelters** (space-per-person setting, ranked list, warnings)
7. **Sources** (datasets, dates, Part 1's test results)

Start on **mock JSON** at hour 2 (shapes agreed at hour 2); switch to the real API around hour 24.

### 4.3 Demo and submission (one person)

- Demo script: fire alert → alert detail → area summary → routes → shelters (coordinator) → analyst blocked from shelters → Sources page with the model's test numbers.
- Record the video at hours 40–44; submission page at 44–48.

### 4.4 Done when

- [ ] All seven screens work on real data
- [ ] Safety demo works for each role
- [ ] Video recorded, submission page filled in

---

## Putting it together

### Timeline

| Hours | Part 1 Radar | Part 2 Data | Part 3 Backend | Part 4 Frontend |
|---|---|---|---|---|
| 0–2 | Start tier A+B downloads | Download small data | Repo, Docker, database | App skeleton, GIBS map |
| **2** | **All parts agree IDs, rows, files and JSON shapes** | | | |
| 2–8 | Crop, mask | Grid, buildings, residents, facilities | Tables, sign-in, roles | Main map on mock layers |
| 8–16 | Features, quiet cells, anomaly model, classes | Road graph, live jobs | Endpoints on mock data, layer files | Time slider, alert feed, area pop-up |
| 16–24 | Change images, slider passes | Shelters, alerts, join with damage | Real data loaded, access checks | Area summary, alert detail |
| **24** | **Everything on real data. Check what works.** | | | |
| 24–32 | Coherence (if tier C), refit, tests | Routes, closures | Routes, shelters, closures endpoints; tunnel | Routes, shelters, sources screens |
| 32–38 | Fix classes, Sources text | Fix data errors | Safety tests, freshness strip | Phone layout, print, polish |
| **38** | **Feature freeze. Only fixes from here.** | | | |
| 38–44 | Help test | Help test | Backup laptop | Fixes; video at 40–44 |
| 44–48 | Submission page, final checks | | | |

### If time is short, cut in this order

1. Gemini question box (stretch only)
2. Coherence (tier C): keep the backscatter-only damage map
3. Phone layout and print styling
4. Open-land shelters (keep buildings)
5. Time slider passes after July (keep before/after)

Never cut: the NISAR damage map, sign-in with roles, the safety rules.

### Stretch goals (only after hour 38)

- **Question box with the Gemini API free tier** (free key, nothing to install). Only the question is sent; our code builds the answer. Restricted data never goes to the API.
- Sentinel-1 (OPERA RTC-S1) cross-check
- Movement trend (IOM DTM, Meta)
- Second radar view (track 172 ascending)
- Offline saved summaries
