# CIVISAR: Dataset Catalogue

The datasets we use for the **south Lebanon demo** and what each one does. See [PROJECT_PLAN.md](PROJECT_PLAN.md) for how they fit together.

The list was cut down on 13 November 2026 to **14 sources**: only data that feeds a map layer or an agent result. Sources were collected from:
- the **Dancing with the SARs** Resources tab (our challenge),
- the Resources tabs of other 2026 Space Apps challenges,
- the team PDF *NASA Open Data Links – Earth Impact Intelligence*,
- earlier planning research.

Rules: at least one dataset from the challenge Resources tab is required (ours is NISAR). Nothing Chinese-owned. Every dataset used is cited with the record in section 7.

Demo area search box: south Lebanon, 35.0–36.0 E, 33.0–33.6 N.

**Resources tab marks** (tab: https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=resources):

| Mark | Meaning |
|---|---|
| 🟢 **Tab** | Named and linked directly on our challenge's Resources tab |
| 🔵 **Tab tool** | Found and downloaded through a tool linked on the Resources tab (NASA Earthdata Search or ASF Vertex) and their APIs |
| ⚪ **Other** | From another source (other challenge pages, team PDF, humanitarian data) |

Summary: **6 of our 14 datasets come from the Resources tab or its tools** (1 🟢, 5 🔵). All 4 APIs we use for NASA data (section 5) sit behind tools on that tab.

---

## 1. Required dataset (from our challenge's Resources tab)

### 🟢 NISAR via ASF (Vertex / ASF Search API)

NISAR is the challenge's own mission. The tab links ASF Vertex, NASA Earthdata Search and the NISAR Data User Guide, which are the three ways to find and get it.

| Product | CMR concept ID | Newest over Lebanon | Our use |
|---|---|---|---|
| **NISAR_L2_GCOV_V1** (validated) | C3622241360-ASF | 3 Nov 2026 | **Main damage signal.** Backscatter change between dates. HH vs HV comparison helps separate collapsed buildings from other changes. |
| NISAR_L2_GCOV_PROVISIONAL_V1 | C2854338529-ASF | 19 Oct 2026 | Earlier dates for the time series |
| **NISAR_L2_GSLC_V1** / NISAR_L2_GSLC_PROVISIONAL_V1 | C3622244601-ASF / C2854332392-ASF | 3 Nov 2026 | Coherence loss between dates, the strongest damage signal for built-up areas |

**Coverage (ASF Search API, 13 Nov 2026):** 336 NISAR granules over south Lebanon on three tracks. GCOV passes: track 151 descending 11 (24 Jun to 3 Nov 2026, main time series), track 172 ascending 10, track 100 ascending 8.

## 2. Other NASA data

| # | Mark | Dataset | CMR concept ID / access | Newest over Lebanon | Used for |
|---|---|---|---|---|---|
| 2 | 🔵 Tab tool (ASF Vertex, Earthdata Search) | **OPERA_L2_RTC-S1_V1** (Sentinel-1, processed by NASA) | C2777436413-ASF | 10 Nov 2026 | Extra radar dates between NISAR passes |
| 3 | 🔵 Tab tool (Earthdata Search) | **Black Marble NRT** VJ146A2_NRT (NOAA-20), VJ246A2_NRT (NOAA-21) | C4193331158-LANCEMODIS, C4249684820-LANCEMODIS | 12 Nov 2026 | Power lost or working, daily |
| 4 | 🔵 Tab tool (Earthdata Search) | **FIRMS VIIRS active fire** VJ114IMGTDL_NRT, VJ214IMGTDL_NRT (375 m) | C3264430167-LANCEMODIS, C4377939055-LANCEMODIS; live feed also via FIRMS API | 13 Nov 2026 | Live fire alerts |
| 5 | 🔵 Tab tool (Earthdata Search) | **NASADEM_HGT** | C2763264762-LPCLOUD | static | Slope check for open-land shelter sites |
| 6 | ⚪ Other (team PDF) | **GIBS map layers** | https://www.earthdata.nasa.gov/data/tools/gibs | daily | Ready map backgrounds (display only, not analysis) |

Black Marble: use NOAA-20/21, not Suomi NPP (VNP46).

GIBS layers we show: `VIIRS_NOAA20_GapFilled_BRDF_Corrected_DayNightBand_Radiance`, `VIIRS_NOAA21_GapFilled_BRDF_Corrected_DayNightBand_Radiance` (night lights), `VIIRS_NOAA20_Thermal_Anomalies_375m_All`, `VIIRS_NOAA21_Thermal_Anomalies_375m_All` (fires), `HLS_S30_Nadir_BRDF_Adjusted_Reflectance` (true colour), `Reference_Features`, `Reference_Labels`.

## 3. Non-NASA data

All ⚪ Other: these come from humanitarian and open-data sources, not the Resources tab.

| # | Dataset | Access | How often | Used for |
|---|---|---|---|---|
| 7 | **OpenStreetMap / HOTOSM** | Overpass; HDX `hotosm_lbn_buildings`, `hotosm_lbn_roads` | Live edits; exports monthly | Buildings, roads, hospitals, schools, water and power sites. `building:levels` gives floor area for shelter capacity. |
| 8 | **WorldPop** | https://www.worldpop.org/ | Yearly | People counts (about 100 m, with age and sex) |
| 9 | **UNOSAT damage assessments** | HDX | Per event | Validation of our damage classes only |
| 10 | **UNDP / CNRS-L Lebanon assessments** | UNDP, CNRS-L | Per event | Validation for south Lebanon only |
| 11 | **ACLED** | HDX `lebanon-acled-conflict-data`; API (free account) | Weekly | Strike context next to radar changes; watch list |
| 12 | **IODA** (Georgia Tech) | Public API, tested (Lebanon code `LB`) | Real time | Internet outage layer |
| 13 | **IOM DTM + Meta Movement Distribution Maps** | DTM API, HDX `lbn-iom-dtm-from-api`; HDX `movement-distribution` (CC BY) | Weekly; every 2 weeks | Displacement numbers and movement trend, by area only |
| 14 | **Insecurity Insight** | HDX `aid-security-risk-in-lebanon` | Weekly to monthly | Reported attacks on health, water and schools ("reported" label) |

## 4. Which layer and agent uses each dataset

| Mark | Dataset | API | Map layer | Agent |
|---|---|---|---|---|
| 🟢 | NISAR GCOV, GSLC | ASF Search API, earthaccess | NISAR change, damage classes, time slider | Damage |
| 🔵 | OPERA RTC-S1 | ASF Search API, earthaccess | Sentinel-1 change | Damage, Alert |
| 🔵 | Black Marble NRT | CMR, earthaccess | Night lights before/after, power lost | Services, Alert, Movement |
| 🔵 | FIRMS | CMR; FIRMS API for live points | Fires | Alert, Services |
| 🔵 | NASADEM | CMR, earthaccess | (used inside shelter scoring) | Shelter |
| ⚪ | GIBS | GIBS WMTS | Base maps | none (display) |
| ⚪ | OSM / HOTOSM | Overpass, HDX | Buildings, facilities, roads | Facility, Route, Shelter |
| ⚪ | WorldPop | WorldPop REST | People density | People |
| ⚪ | UNOSAT, UNDP | HDX, download | Validation overlay (analyst view) | Damage (check only) |
| ⚪ | ACLED | ACLED API, HDX | Conflict events | Corroboration, Alert |
| ⚪ | IODA | IODA API | Internet outages | Services, Alert |
| ⚪ | IOM DTM, Meta | DTM API, HDX | Movement (aggregated) | People, Movement |
| ⚪ | Insecurity Insight | HDX | Reported attacks | Facility, Corroboration |

## 5. APIs and access plan

How we get each dataset. Marks as above.

### 5.1 APIs from the Resources tab tools

| Mark | API | Behind which tab link | What we use it for | Key / login |
|---|---|---|---|---|
| 🔵 | **ASF Search API** (`https://api.daac.asf.alaska.edu/services/search/param`), Python `asf_search` | ASF Data Search Vertex | Find NISAR GCOV/GSLC and OPERA RTC-S1 scenes by area, date, track and direction. Already used: 336 NISAR granules over south Lebanon. | None to search |
| 🔵 | **CMR Search API** (`https://cmr.earthdata.nasa.gov/search/`) | NASA Earthdata Search | Find every NASA dataset by its concept ID and list new granules (Black Marble, FIRMS NRT, NASADEM). Already used for all IDs in this file. | None to search |
| 🔵 | **Earthdata Login** (`https://urs.earthdata.nasa.gov/`), bearer token | NASA Earthdata Search, ASF Vertex | Needed to download any NASA file | Free account (each team member makes their own) |
| 🔵 | **earthaccess** (Python) | NISAR Data User Guide (download section) | Download NISAR and other NASA files, or read them straight from NASA cloud (S3) | Uses Earthdata Login |

### 5.2 Other APIs

| Mark | API | What we use it for | Key / login |
|---|---|---|---|
| ⚪ | FIRMS API (`https://firms.modaps.eosdis.nasa.gov/api/`) | Live fire points, faster than CMR files | Free map key |
| ⚪ | GIBS WMTS (`https://gibs.earthdata.nasa.gov/`) | Map background tiles | None |
| ⚪ | Overpass API (OSM) | Buildings, roads, facilities | None |
| ⚪ | IODA API (`https://api.ioda.inetintel.cc.gatech.edu/v2/`) | Internet outages, tested with `LB` | None |
| ⚪ | ACLED API | Conflict events | Free account |
| ⚪ | IOM DTM API | Displacement numbers | Free key |
| ⚪ | HDX CKAN API (`https://data.humdata.org/api/`) | HOTOSM exports, Meta movement, UNOSAT, Insecurity Insight, ACLED counts | None |
| ⚪ | WorldPop REST API (`https://www.worldpop.org/rest/data`) | Population rasters | None |

### 5.3 Steps for each NISAR pass

1. **Search:** ASF Search API for new NISAR GCOV and GSLC on track 151 over the demo box.
2. **Download:** earthaccess with the Earthdata Login token.
3. **Process:** change detection against the previous pass on the same track (backscatter change from GCOV, coherence from GSLC).
4. **Store:** results go into the area tables (plan section 8.1), each with its dataset record (section 7).
5. **Daily, between passes:** CMR for new Black Marble files, the FIRMS API for fires, IODA for outages. The ASF Search API also checks for new OPERA RTC-S1 scenes.

## 6. Dropped

Checked and dropped on 13 Nov 2026 so the build stays small:

- **Radar we don't need:** SAOCOM (🟢 on the tab, but needs registration and coverage is not confirmed), RCM and RADARSAT-1 (🟢 on the tab, but no open data over Lebanon), NISAR GUNW and UR products (none over Lebanon), OPERA DIST-ALERT-S1 (not current over Lebanon).
- **Learning material from the tab (🟢, not data):** Intro to Remote Sensing, Intro to SAR, NASA ARSET, NISAR StoryMaps, NISAR Applications White Papers, UAVSAR Postcards, CSA SAR Python tutorial. We use them to learn and for presentation ideas.
- **Duplicates or not needed:** GPWv4 (WorldPop instead), gROADS (OSM instead), MCD12Q1, HLS downloads, OPERA DIST-ALERT-HLS, DSWx, GPM IMERG, SMAP, NASA POWER, AppEEARS, Giovanni, NASA SVS night-lights story.
- **From other challenge pages:** Sentinel-2, ERA5, GEDI, ECOSTRESS, FAO GAEZ, KNMI, NOAA CDO, and the US-only datasets.
- **Hard to access or extra:** WHO HeRAMS, WHO attacks database, UNMAS, Logistics Cluster, Pacific Institute, HDX HAPI, UNHCR, healthsites.io (OSM covers it).
- **Never used:** EONET (natural events only), anything Chinese-owned, live vehicle or phone-location data.

## 7. Record to keep for every dataset used

One record per dataset, so the AI agents and the citations page can read it:

| Field | Example |
|---|---|
| Dataset name | NISAR L2 GCOV |
| Product level | L2 |
| Provider | NASA/ISRO via ASF |
| CMR concept ID | C3622241360-ASF |
| Resources tab mark | 🟢 Tab / 🔵 Tab tool / ⚪ Other |
| API used | ASF Search API + earthaccess |
| Acquisition date(s) | (per scene) |
| Processing version | (from granule metadata) |
| Spatial coverage | Track, frame, bounding box |
| Resolution | |
| Terms of use / licence | |
| Source URL | |
| Date accessed | |
| Known limits | e.g. provisional before 21 Oct 2026 |
