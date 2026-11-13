# CIVISAR: Dataset Catalogue

The datasets we use for the **south Lebanon demo** and what each one does. See [PROJECT_PLAN.md](PROJECT_PLAN.md) for how they fit together.

The list was cut down on 13 November 2026 to **14 sources**: only data that feeds a map layer or an agent result. Sources were collected from:
- the **Dancing with the SARs** Resources tab (our challenge),
- the Resources tabs of other 2026 Space Apps challenges,
- the team PDF *NASA Open Data Links – Earth Impact Intelligence*,
- earlier planning research.

Rules: at least one dataset from the challenge Resources tab is required (ours is NISAR). Nothing Chinese-owned. Every dataset used is cited with the record in section 6.

Demo area search box: south Lebanon, 35.0–36.0 E, 33.0–33.6 N.

---

## 1. Required dataset (from our challenge's Resources tab)

### NISAR via ASF (Vertex / ASF Search API)

| Product | CMR concept ID | Newest over Lebanon | Our use |
|---|---|---|---|
| **NISAR_L2_GCOV_V1** (validated) | C3622241360-ASF | 3 Nov 2026 | **Main damage signal.** Backscatter change between dates. HH vs HV comparison helps separate collapsed buildings from other changes. |
| NISAR_L2_GCOV_PROVISIONAL_V1 | C2854338529-ASF | 19 Oct 2026 | Earlier dates for the time series |
| **NISAR_L2_GSLC_V1** / NISAR_L2_GSLC_PROVISIONAL_V1 | C3622244601-ASF / C2854332392-ASF | 3 Nov 2026 | Coherence loss between dates, the strongest damage signal for built-up areas |

**Coverage (ASF Search API, 13 Nov 2026):** 336 NISAR granules over south Lebanon on three tracks. GCOV passes: track 151 descending 11 (24 Jun to 3 Nov 2026, main time series), track 172 ascending 10, track 100 ascending 8.

Guides from the Resources tab:
- NISAR Data User Guide: https://nisar-docs.asf.alaska.edu/
- ASF Vertex: https://search.asf.alaska.edu/
- ASF Search API: https://docs.asf.alaska.edu/api/overview/
- Earthdata Login (needed for downloads): https://urs.earthdata.nasa.gov/

## 2. Other NASA data

| # | Dataset | CMR concept ID / access | Newest over Lebanon | Used for |
|---|---|---|---|---|
| 2 | **OPERA_L2_RTC-S1_V1** (Sentinel-1, processed by NASA) | C2777436413-ASF | 10 Nov 2026 | Extra radar dates between NISAR passes |
| 3 | **Black Marble NRT** VJ146A2_NRT (NOAA-20), VJ246A2_NRT (NOAA-21) | C4193331158-LANCEMODIS, C4249684820-LANCEMODIS | 12 Nov 2026 | Power lost or working, daily |
| 4 | **FIRMS VIIRS active fire** VJ114IMGTDL_NRT, VJ214IMGTDL_NRT (375 m) | C3264430167-LANCEMODIS, C4377939055-LANCEMODIS; FIRMS API (free map key) | 13 Nov 2026 | Live fire alerts |
| 5 | **NASADEM_HGT** | C2763264762-LPCLOUD | static | Slope check for open-land shelter sites |
| 6 | **GIBS map layers** | https://www.earthdata.nasa.gov/data/tools/gibs | daily | Ready map backgrounds (display only, not analysis) |

Black Marble: use NOAA-20/21, not Suomi NPP (VNP46).

GIBS layers we show: `VIIRS_NOAA20_GapFilled_BRDF_Corrected_DayNightBand_Radiance`, `VIIRS_NOAA21_GapFilled_BRDF_Corrected_DayNightBand_Radiance` (night lights), `VIIRS_NOAA20_Thermal_Anomalies_375m_All`, `VIIRS_NOAA21_Thermal_Anomalies_375m_All` (fires), `HLS_S30_Nadir_BRDF_Adjusted_Reflectance` (true colour), `Reference_Features`, `Reference_Labels`.

## 3. Non-NASA data

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

| Dataset | Map layer | Agent |
|---|---|---|
| NISAR GCOV, GSLC | NISAR change, damage classes, time slider | Damage |
| OPERA RTC-S1 | Sentinel-1 change | Damage, Alert |
| Black Marble NRT | Night lights before/after, power lost | Services, Alert, Movement |
| FIRMS | Fires | Alert, Services |
| NASADEM | (used inside shelter scoring) | Shelter |
| GIBS | Base maps | none (display) |
| OSM / HOTOSM | Buildings, facilities, roads | Facility, Route, Shelter |
| WorldPop | People density | People |
| UNOSAT, UNDP | Validation overlay (analyst view) | Damage (check only) |
| ACLED | Conflict events | Corroboration, Alert |
| IODA | Internet outages | Services, Alert |
| IOM DTM, Meta | Movement (aggregated) | People, Movement |
| Insecurity Insight | Reported attacks | Facility, Corroboration |

## 5. Dropped

Checked and dropped on 13 Nov 2026 so the build stays small:

- **Radar we don't need:** SAOCOM (registration, coverage not confirmed), RCM and RADARSAT-1 (no open data over Lebanon), NISAR GUNW and UR products (none over Lebanon), OPERA DIST-ALERT-S1 (not current over Lebanon).
- **Duplicates or not needed:** GPWv4 (WorldPop instead), gROADS (OSM instead), MCD12Q1, HLS downloads, OPERA DIST-ALERT-HLS, DSWx, GPM IMERG, SMAP, NASA POWER, AppEEARS, Giovanni, NASA SVS night-lights story.
- **From other challenge pages:** Sentinel-2, ERA5, GEDI, ECOSTRESS, FAO GAEZ, KNMI, NOAA CDO, and the US-only datasets.
- **Hard to access or extra:** WHO HeRAMS, WHO attacks database, UNMAS, Logistics Cluster, Pacific Institute, HDX HAPI, UNHCR, healthsites.io (OSM covers it).
- **Never used:** EONET (natural events only), anything Chinese-owned, live vehicle or phone-location data.

## 6. Record to keep for every dataset used

One record per dataset, so the AI agents and the citations page can read it:

| Field | Example |
|---|---|
| Dataset name | NISAR L2 GCOV |
| Product level | L2 |
| Provider | NASA/ISRO via ASF |
| CMR concept ID | C3622241360-ASF |
| Acquisition date(s) | (per scene) |
| Processing version | (from granule metadata) |
| Spatial coverage | Track, frame, bounding box |
| Resolution | |
| Terms of use / licence | |
| Source URL | |
| Date accessed | |
| Known limits | e.g. provisional before 21 Oct 2026 |
