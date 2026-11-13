# CIVISAR: NASA Dataset Analysis

What NASA open data can tell us about war impacts, checked live against the portals in the team PDF *NASA Open Data Links – Earth Impact Intelligence* ([PDF](NASA_Open_Data_Links_Earth_Impact_Intelligence.pdf)).

> Checked on **13 November 2026**. Coverage, dates and counts below come from live queries, not from memory or secondary sources. Items marked **(spec)** are product-documentation values (resolution, revisit) that were not re-measured. Items marked **(unverified)** still need checking.

---

## 0. How this was checked

| PDF portal | How it was queried | Result |
|---|---|---|
| NASA Earthdata Search | Its back-end catalogue (CMR API): keyword search per war impact, then granule counts per study area | Main source. All dataset rows below come from here. |
| ASF Vertex + ASF Search API | ASF Search API (same back-end as Vertex) | All NISAR and Sentinel-1 rows |
| NASA Worldview + GIBS | GIBS WMTS capabilities (1,330 layers), plus test map requests over south Lebanon | Ready-made web-map layers, section 4 |
| NASA Open Data Portal (data.nasa.gov) | CKAN API | 36,518 metadata records. Mostly mirrors Earthdata and SEDAC, so nothing beyond what CMR gives. Searching "war damage" returns 0. |
| NASA API Portal (api.nasa.gov) | Direct calls | Earth imagery API returned **503**. The other APIs are for space and planetary science (section 6). |
| NASA EONET | Events API | Floods in Lebanon and Israel only. The "manmade" category's newest event is from 2018. Useful only to rule out floods as a cause of radar change. |
| Earthdata Login | | Needed to download most files (section 7) |
| NASA Exoplanet Archive, NASA Open | | Not relevant |

**Search boxes** (lon/lat):
- South Lebanon (LB): 35.0–36.0 E, 33.0–33.6 N
- Gaza (GZ): 34.2–34.6 E, 31.2–31.6 N
- Kyiv (KV): 30.2–30.8 E, 50.2–50.6 N

"Granules since Oct 2025" means files from **1 Oct 2025 to 13 Nov 2026** whose footprint touches the box.

---

## 1. What war does, and what a satellite can see

| War impact | What a satellite can observe | Best NASA data (detail in section 3) | CIVISAR feature |
|---|---|---|---|
| Buildings destroyed or damaged | Radar backscatter change, coherence loss, optical change | NISAR GCOV/GSLC/GUNW, OPERA RTC-S1, Sentinel-1 SLC, HLS, OPERA DIST-ALERT-HLS | Damage and severity |
| Roads, bridges, ports hit | Same as buildings, at the scale of a road or bridge | NISAR GSLC, Sentinel-1, HLS | Routing (closures, unknown segments) |
| Power cut | Night lights drop | Black Marble VJ146/VJ246 (+NRT) | Services lost: power |
| Fires after strikes | Thermal hotspots, burn scars | VIIRS 375 m and MODIS active fire (FIRMS), MCD64A1/VNP64A1 | Hazards, damage cross-check |
| Farmland, orchards, forest burned or abandoned | Vegetation index drop, land disturbance | HLS VI, OPERA DIST-ALERT-HLS, MODIS/VIIRS NDVI, ECOSTRESS ESI | Food and livelihood loss (new) |
| Water supply hit (reservoirs, canals) | Water extent and level change | OPERA DSWx-HLS/S1, SWOT, VIIRS reservoir product | Services lost: water (context) |
| Toxic smoke (fuel depots, industry) | NO2, SO2, CO, aerosol, smoke | Sentinel-5P TROPOMI via GES DISC, MODIS MAIAC, VIIRS Deep Blue, OMPS SO2 | Hazards: air quality (new) |
| Gas leaks from damaged pipes | Methane plume | EMIT CH4, TROPOMI CH4 | Hazards (context) |
| Sewage and oil reaching the sea | Ocean colour, turbidity, slicks | PACE OCI, VIIRS ocean colour, Sentinel-1 GRD (slicks) | Hazards: coastal (new, mainly Gaza) |
| People displaced, activity lost | Night-light loss, land-use change | Black Marble, NISAR change on open land | Population movement (aggregated) |
| Heat or cold exposure for displaced people | Air and land temperature | NASA POWER, MODIS/VIIRS LST, ECOSTRESS LST, MERRA-2 | Shelter needs (3.5 vs 4.5 m² rule) |
| Ground too wet for an open-land site | Soil moisture, standing water | SMAP, NISAR SME2, DSWx | Shelter finder (open land) |
| False radar alarms from rain or flood | Rainfall, flood events | GPM IMERG, EONET floods | Damage confidence |
| Terrain for routes and sites | Elevation and slope | NASADEM, SRTM, ASTER GDEM | Routing, shelter site slope |
| Who lives there | Population grids | SEDAC GPWv4, GHSL, GRDI | People affected (baseline only, old) |
| Unexploded ordnance, mines | **Not visible from space** | none | Must come from UNMAS (non-NASA) |

---

## 2. Big findings

1. **NISAR before/after across the 2026 escalation.**
   - What exists: NISAR has BETA products from 27 Oct 2025 to 19 Jan 2026 (software 1.0.2), **no acquisitions from 20 Jan to 17 Jun 2026**, then PROVISIONAL (1.0.11) and validated V1 from 22 Oct 2026.
   - Why it matters: Insecurity Insight data (HDX) shows Lebanon explosive-weapon incidents spiked in Mar–May 2026 (110, 109, 91 per month), inside the NISAR gap. So a January 2026 vs June 2026 pair brackets the escalation.
   - Catches:
     - The pair mixes software versions.
     - No ready-made interferogram spans the gap: GUNW pairs are 12 or 24 days apart. We would compute coherence ourselves from two GSLC files on the same track and frame.
2. **NISAR is already a web-map layer.** GIBS layer `NISAR_L2_Geocoded_Polarimetric_Covariance` (about 15.6 m tiles, 29 Oct 2025 – 10 Nov 2026) rendered over south Lebanon for 26 Jun 2026. It is **blank for 9 Jan 2026**, so BETA data is not on GIBS. It works for the demo backdrop, not for analysis.
3. **NISAR emergency products don't cover us.**
   - Urgent Response products (`NISAR_UR_L1/L2`) exist (6,676 granules worldwide), but **none** over Lebanon, Gaza or Kyiv.
   - Pixel offsets (GOFF) and wrapped interferograms (RIFG): none over Lebanon either.
4. **NISAR publishes its future schedule.** The `NISAR_COP` (Coordinated Observation Plan) files run to 22 Nov 2026, about 9 days ahead. CIVISAR can show "next radar pass over this area" and explain when the damage map will be refreshed.
5. **Sentinel-1 fills the gaps between NISAR passes.**
   - Sentinel-1A's last scene over Lebanon was 29 Jun 2026. Sentinel-1C (from Apr 2025) and **Sentinel-1D (from 18 Apr 2026)** are active.
   - OPERA RTC-S1 over Lebanon is current to 10 Nov 2026 (about 3 days old).
6. **Night lights: use NOAA-20 and NOAA-21.**
   - Suomi NPP data (VNP46) ends 2 Nov 2026.
   - The NRT versions keep only about the **last 8 days**. The standard versions lag 8 days (A1) to 16 days (A2). A daily power layer has to join NRT (recent days) with the standard archive (older days).
7. **Sentinel-1 disturbance alerts are not usable.** `OPERA_L3_DIST-ALERT-S1` only has Jan–Feb 2026 over all three areas. The optical **DIST-ALERT-HLS** is current (5 Nov 2026) and good for burned or cleared land.
8. **NASA's population and settlement data is old.** GPWv4 ends at 2020, age/sex at 2010, SEDAC GHSL at 2015, gROADS at 2010, HBASE/GMIS at 2010. Use these only as a cross-check or fallback, never as "people there now".
9. **NASA lidar has building heights at sample points.** GEDI (to Jun 2026) and ICESat-2 (current) measure height at footprints. They could partly fill OSM's missing building levels. **(unverified for buildings in our areas)**

---

## 3. Dataset analysis by impact

Columns:
- **Granules since Oct 2025:** LB / GZ / KV counts.
- **Last over LB:** newest file over south Lebanon.
- **Priority:** **Core** = needed for the 48-hour build. **Support** = adds value if time allows. **Context** = story or validation only. **Skip** = see section 6.

### 3.1 Building, road and bridge damage (radar)

| Dataset (short name) | Res. (spec) | Granules since Oct 2025 LB / GZ / KV | Last over LB | Use for CIVISAR | Priority |
|---|---|---|---|---|---|
| NISAR L2 GCOV (BETA / PROVISIONAL / V1) | ~20 m, HH+HV, 20+5 MHz | 71 / 56 / 53 | 2026-11-03 | Backscatter change, HH vs HV comparison. **Required by the challenge.** | **Core** |
| NISAR L2 GSLC (BETA / PROVISIONAL / V1) | Single-look, finer than GCOV (spec) | 70 / 57 / 53 | 2026-11-03 | Our own coherence across any two dates, including across the Jan–Jun gap. Strongest damage signal for built-up areas. | **Core** |
| NISAR L2 GUNW (BETA / PROVISIONAL) | HH only, 20 MHz | 59 / 36 / 42 | pairs to 2026-10-19 | Ready-made coherence and phase for 12- and 24-day pairs. Time-slider steps after June 2026. | **Core** |
| NISAR L1 RSLC | Radar geometry | 71 / 57 / 54 | 2026-11-03 | Reprocess BETA and PROVISIONAL with one software version if calibration differs | Support |
| NISAR L3 SME2 soil moisture | (spec) | 41 / 39 / 38 | 2026-10-19 | Wet-ground check for open-land shelter sites | Support |
| NISAR_COP observation plan | n/a | n/a | runs to 2026-11-22 | "Next NISAR pass" in the app | Support |
| NISAR_DEM, NISAR_WATERMASK | | static | | Same DEM and water mask NISAR used, so our masks match its processing | Support |
| OPERA RTC-S1 (Sentinel-1, ESA, processed by NASA) | 30 m, C-band | 2,299 / 1,243 / 1,620 | 2026-11-10 | Extra dates between NISAR passes, C-band vs L-band cross-check | **Core** |
| Sentinel-1C / 1D SLC (ESA via ASF) | IW SLC | 169+69 / 184+82 / 203+102 | 2026-11-10 | C-band coherence if needed. 1A stopped over LB on 29 Jun 2026. | Support |
| Sentinel-1A GRD-H (ESA via ASF) | ~10 m | 90 / 111 / 155 | 2026-06-29 | Oil slicks at sea, older dates | Context |
| OPERA DIST-ALERT-S1 | 30 m | 203 / 74 / 214 | **2026-02-28** | Stopped after Feb 2026 | Skip for now |
| OPERA CSLC-S1, DISP-S1; ARIA S1 GUNW | | 0 / 0 / 0 | (CSLC only Oct 2023) | No current coverage | Skip |
| NISAR UR L1/L2, GOFF, RIFG; ALOS-2 PSR2 | | 0 / 0 / 0 | | No coverage over our areas | Skip |

### 3.2 Optical change (buildings, land, vegetation)

| Dataset | Res. | LB / GZ / KV | Last over LB | Use | Priority |
|---|---|---|---|---|---|
| HLS L30 / S30 (Landsat 8/9 + Sentinel-2) | 30 m, every 2–3 days | 480+570 / 192+175 / 248+642 | 2026-11-05 | Before/after swipe images, open-land check, confirm radar changes when cloud-free | **Core** |
| HLS VI (vegetation indices) | 30 m | 571 / 177 / 644 (S30) | 2026-11-05 | Farmland and orchard loss | Support |
| OPERA DIST-ALERT-HLS | 30 m | 1,044 / 363 / 890 | 2026-11-05 | Ready-made land-disturbance alerts: burned orchards, cleared land, new camp areas | **Core** |
| OPERA DIST-ANN-HLS | 30 m, yearly | 6 / 2 / 4 | 2025 | Annual disturbance summary | Context |
| MODIS MOD13Q1 NDVI | 250 m, 16-day | 50 / 25 / 25 | 2026-10-16 | Long vegetation baseline (since 2000) | Support |
| VIIRS VNP13A1 NDVI | 500 m, 16-day | 102 / 51 / 51 | 2026-10-24 | Same | Context |
| EMIT L2A reflectance (ISS) | 60 m, irregular | 32 / 15 / 28 | 2026-08-11 | Debris and material mapping (experimental) | Context |
| GEDI L2B v003 (lidar) | 25 m footprints | 29 / 15 / 81 | 2026-06-09 | Canopy and possibly building height samples | Support (unverified) |

### 3.3 Power and activity (night lights)

| Dataset | Res. | LB / GZ / KV | Last over LB | Use | Priority |
|---|---|---|---|---|---|
| VJ146A2 (NOAA-20 Black Marble, gap-filled, lunar corrected) | ~500 m, daily | 394 / 394 / 393 | 2026-10-28 | Main power-outage layer (archive) | **Core** |
| VJ246A2 (NOAA-21) | ~500 m, daily | 395 / 395 / 396 | 2026-10-31 | Second satellite, more cloud-free nights | **Core** |
| VJ146A2_NRT, VJ246A2_NRT, VJ146A1_NRT, VJ246A1_NRT | ~500 m | 8 each (rolling) | 2026-11-12 | Last ~8 days only. Joins the archive for a current view. | **Core** |
| VJ146A1 (at-sensor, not corrected) | ~500 m | 402 each | 2026-11-05 | Backup | Support |
| VJ146A3 / VNP46A3 monthly | ~500 m | 13 / 14 | 2026-09-01 / 2026-10-01 | Monthly trend charts | Support |
| VNP46A1/A2 (Suomi NPP) | | 375 | **2026-11-02 (end)** | Archive only | Context |
| SEDAC VIIRS+DMSP dLIGHT | | | 1992–2013 | Too old | Skip |

### 3.4 Fires and burned land

| Dataset | Res. | LB / GZ / KV | Last over LB | Use | Priority |
|---|---|---|---|---|---|
| VJ114IMGTDL_NRT, VJ214IMGTDL_NRT (VIIRS 375 m NRT, FIRMS) | 375 m | rolling ~7 days | **2026-11-13 (today)** | Active fires after strikes, live hazard layer | **Core** |
| MCD14DL (MODIS NRT, FIRMS) | 1 km | rolling | 2026-11-13 | Second fire source | Support |
| VJ114IMG / VNP14IMG (standard) | 375 m | 1,170 / 1,126 / 1,556 | 2026-11-07 | Fire archive for the time slider | **Core** |
| MCD64A1 / VNP64A1 burned area | 500 m, monthly | 24 / 12 / 12 | 2026-09-01 | Burn scars on farmland and forest | Support |

FIRMS also has an area API that needs a free MAP_KEY. We didn't test it, because the key requires sign-up.

### 3.5 Air pollution and smoke

Sentinel-5P is an ESA satellite, but NASA GES DISC distributes its data, so it counts as partner-agency data.

| Dataset | Res. | LB / GZ / KV | Last over LB | Use | Priority |
|---|---|---|---|---|---|
| S5P TROPOMI NO2 (v2) | 5.5×3.5 km | 492 / 484 / 750 | 2026-10-29 | Combustion and industrial pollution change | Support |
| S5P TROPOMI SO2 (v2) | 5.5×3.5 km | 500 / 493 / 761 | 2026-11-05 | Fuel depot and industrial fires | Support |
| S5P TROPOMI CO (v2) | 5.5×7 km | 501 / 476 / 748 | 2026-11-06 | Large fire smoke | Context |
| S5P TROPOMI Aerosol Index / TROPOMAER | 5.5×3.5 km | ~500 | 2026-11-06 | Smoke and dust plumes | Context |
| MCD19A2 MAIAC AOD | 1 km, daily | 814 / 407 / 407 | 2026-11-11 | Local haze and smoke at shelter sites | Support |
| AERDB VIIRS NOAA-20 Deep Blue | 6 km | 561 / 550 / 886 | 2026-11-12 | Daily aerosol, near real time | Context |
| OMPS NOAA-20 SO2 | ~17×13 km | 479 / 478 / 651 | 2026-10-21 | SO2 backup | Context |
| MERRA-2 aerosol (M2T1NXAER) | ~50 km | 366 | 2026-10-01 | Regional background, about 6 weeks behind | Context |
| TEMPO (NO2, aerosol) | | | | North America only | Skip |

At these resolutions, air data shows **regional pollution events**, not single strikes.

### 3.6 Water: surface water, reservoirs, flood check

| Dataset | Res. | LB / GZ / KV | Last over LB | Use | Priority |
|---|---|---|---|---|---|
| OPERA DSWx-S1 | 30 m | 2,443 / 769 / 2,248 | 2026-11-11 | Wet or flooded ground, through cloud. Excludes shelter sites. Flags flooding from damaged infrastructure. | **Core** |
| OPERA DSWx-HLS | 30 m | 1,774 / 505 / 1,132 | 2026-11-05 | Same, optical | Support |
| SWOT L2 HR LakeSP / Raster | vector / 100 m | 1,632 / 1,821 / 3,084 | 2026-11-09 | Reservoir level change, e.g. Qaraoun reservoir on the Litani, or Kyiv reservoirs | Support |
| VIIRS reservoir VJ128C2 | 8-day | 50 each | 2026-10-24 | Reservoir area trend | Context |
| GPM IMERG Early / Late daily | 0.1°, half-hourly | 19,596 / 407 | 2026-11-13 / 11-11 | Rule out rain as a cause of radar change (wet soil changes backscatter) | **Core** |
| EONET floods | events | Lebanon floods on 23 Nov 2025 and 28 Aug 2026 | | Flag dates when radar change may be flood, not damage | Support |

### 3.7 Coast and sea (mainly Gaza; also Tyre and Sidon)

| Dataset | Res. | LB / GZ / KV | Last over LB | Use | Priority |
|---|---|---|---|---|---|
| PACE OCI L2 BGC / AOP | 1 km, hyperspectral | 455 / 432 / – | 2026-10-01 | Coastal water quality, sewage and algae plumes | Support (Gaza) |
| VIIRS NOAA-20 ocean colour NRT | 750 m | 577 / 565 / – | 2026-11-12 | Daily turbidity and chlorophyll near the coast | Support (Gaza) |
| Sentinel-1 GRD | ~10 m | see 3.1 | | Oil slicks show as dark patches | Context |

### 3.8 Gas leaks

| Dataset | Res. | LB / GZ / KV | Last over LB | Use | Priority |
|---|---|---|---|---|---|
| EMIT L2B CH4 enhancement v003 | 60 m, irregular | 2 / 1 / 4 | 2026-10-17 | Methane from damaged gas infrastructure (most useful in Ukraine) | Context |
| S5P TROPOMI CH4 | 5.5×7 km | 502 / 477 / 750 | 2026-11-06 | Regional methane | Skip (too coarse) |

### 3.9 Heat, cold and weather (shelter needs, responder conditions)

| Dataset | Res. | Last | Use | Priority |
|---|---|---|---|---|
| NASA POWER API (no key) | 0.5° | 10 Nov 2026 (about 3 days behind) | Daily min/max temperature and rain at each shelter site. Decides 3.5 vs 4.5–5.5 m² per person. | **Core** |
| MODIS MOD11A1 / VIIRS VJ121A1D LST | 1 km, daily | 2026-11-12 / 11-05 | Heat stress maps for camps in summer | Support |
| ECOSTRESS L2T LSTE | 70 m, irregular | 2026-11-08 (626 scenes over LB) | Fine-scale heat at camp sites | Context |
| ECOSTRESS L4T ESI | 70 m | 2026-10-21 (none over Kyiv) | Crop water stress, i.e. damaged irrigation | Context |
| MERRA-2 single-level (M2T1NXSLV) | ~50 km | 2026-10-01 | Weather archive | Context |

### 3.10 Ground and soil for open-land sites

| Dataset | Res. | Last | Use | Priority |
|---|---|---|---|---|
| SMAP SPL3SMP_E / SPL4SMGP | 9 km | 2026-11-11 / 11-10 | Ground wetness, regional | Support |
| NISAR SME2 | see 3.1 | 2026-10-19 | Finer soil moisture | Support |
| NASADEM_HGT / SRTMGL1 / ASTER GDEM | 30 m, static | 2000 | Slope for open-land sites, terrain for routing | **Core** (one of them) |
| MCD12Q1 land cover | 500 m, yearly | 2025 | Open land vs cropland vs urban mask | Support |
| IMERG + LHASA landslide exposure | | static | Landslide risk on mountain routes in Lebanon | Context |

### 3.11 People and settlements (NASA SEDAC, now hosted on Earthdata)

| Dataset | Res. | Latest year | Use | Priority |
|---|---|---|---|---|
| GPWv4 population count (rev 11) | ~1 km | 2020 | Fallback population and cross-check only | Support |
| GPWv4 basic demographics (age/sex) | ~1 km | 2010 | Too old for vulnerable-group counts | Context |
| GRDI relative deprivation | ~1 km | 2010–2020 | Poorer areas need more help (context) | Context |
| GHSL population and built-up (SEDAC copy) | ~1 km | 2014/2015 | Too old | Skip |
| HBASE / GMIS built-up (Landsat) | 30 m | 2010 | Too old | Skip |
| gROADS | vector | 2010 | Too old | Skip |

NASA has no current population grid. Current population and age/sex data has to come from outside NASA (for example WorldPop, as the team planned). The required NASA dataset is NISAR, so this is allowed.

---

## 4. Ready-made web layers (Worldview / GIBS, no login)

These display quickly in the demo map. They are pictures for the eye, not for analysis (PDF practical note).

| Layer | Dates | Use |
|---|---|---|
| `NISAR_L2_Geocoded_Polarimetric_Covariance` | 2025-10-29 → 2026-11-10 (PROVISIONAL and V1 dates only) | NISAR backdrop. Tested over south Lebanon: renders on 26 Jun 2026, blank on 9 Jan 2026 (BETA). |
| `OPERA_L2_Radiometric_Terrain_Corrected_SAR_Sentinel-1` | 2025-01-10 → today | Sentinel-1 backdrop |
| `OPERA_L3_DIST-ALERT-HLS_Color_Index` | 2023 → 2026-11-05 | Land-disturbance overlay |
| `OPERA_L3_Dynamic_Surface_Water_Extent-Sentinel-1` / `-HLS` | to 2026-11-13 / 11-05 | Water overlay |
| `VIIRS_NOAA20_GapFilled_BRDF_Corrected_DayNightBand_Radiance`, `VIIRS_NOAA21_...` | to 2026-11-11 / 11-12 | Night-lights overlay (tested, renders) |
| `VIIRS_NOAA20/NOAA21_Thermal_Anomalies_375m_All`, `MODIS_Combined_Thermal_Anomalies_All` | to today | Fire points |
| `HLS_S30/L30_Nadir_BRDF_Adjusted_Reflectance` | to 2026-11-05 | 30 m true-colour before/after |
| `VIIRS_NOAA20/21_CorrectedReflectance_TrueColor` | to today | Daily cloud check |
| `MODIS_Terra/Aqua_Aerosol_Optical_Depth_3km`, `OMPS_NOAA20_SO2_*`, `AIRS_L2_Carbon_Monoxide_*` | to today | Smoke and pollution overlays |
| `OCI_PACE_Chlorophyll_a`, `VIIRS_NOAA20_Chlorophyll_a` | to 2026-11-12 | Coastal water overlay |
| `IMERG_Precipitation_Rate` | to 2026-11-11 | Rain overlay |
| `MODIS_Terra/Aqua_Land_Surface_Temp_Day`, `VIIRS_*_Land_Surface_Temp_Day` | to today | Heat overlay |
| `SMAP_L4_Analyzed_Surface_Soil_Moisture` | to 2026-11-10 | Wet-ground overlay |
| `ASTER_GDEM_Color_Shaded_Relief`, `SRTM_Color_Index` | static | Terrain backdrop |
| `GPW_Population_Density_2020`, `Landsat_Human_Built-up_And_Settlement_Extent` | static | Old baselines only |

Note: GIBS's only "Black Marble" layer named as such (`VIIRS_Black_Marble`) stops at 2016. Use the DayNightBand layers above instead.

---

## 5. Recommended NASA stack for the 48-hour build

In order of importance:

1. **NISAR GSLC + GCOV**, track 172A frames 18/19 (or 151D frame 72). Before = BETA Jan 2026, after = PROVISIONAL Jun 2026 onward. Our own coherence plus backscatter change. *(Required.)*
2. **NISAR GUNW** 12/24-day pairs for the time slider after June.
3. **OPERA RTC-S1** for C-band cross-check and extra dates.
4. **Black Marble VJ146A2 + VJ246A2 + NRT** for the power layer.
5. **VIIRS 375 m fire (FIRMS NRT + standard)** for the fire layer.
6. **HLS + OPERA DIST-ALERT-HLS** for optical before/after and farmland or orchard loss.
7. **OPERA DSWx-S1 + GPM IMERG + EONET floods** to filter out rain and flood false alarms, and as the wet-site filter.
8. **NASA POWER** for shelter temperature mode and water needs.
9. **NASADEM** for slope and routing terrain.
10. **GIBS layers** (section 4) for the base map and visual story.

Extras if time allows: SWOT reservoirs, TROPOMI SO2/NO2 and MAIAC smoke, SMAP/SME2 soil moisture, the `NISAR_COP` "next pass" feature, PACE/VIIRS coastal water for Gaza, and GEDI/ICESat-2 height samples.

---

## 6. Checked and not useful (and why)

| Item | Reason |
|---|---|
| NASA Exoplanet Archive, NASA Open | Not Earth observation |
| api.nasa.gov: APOD, NeoWs, DONKI, Mars/InSight, GeneLab, Techport, Image Library, EPIC | Space or planetary data. EPIC is whole-Earth discs, far too coarse. |
| api.nasa.gov Earth imagery (Landsat) | Returned HTTP 503. Use HLS instead. |
| EONET "manmade" | Newest event is from 2018. No wildfire events near Lebanon or Gaza. |
| NISAR Urgent Response, GOFF, RIFG | No granules over our areas |
| OPERA CSLC-S1, DISP-S1, ARIA S1 GUNW | No current coverage (CSLC has only Oct 2023 over Lebanon) |
| OPERA DIST-ALERT-S1 | Only Jan–Feb 2026 |
| TEMPO | North America only |
| GPCP daily | Ends Dec 2025. Use IMERG. |
| SEDAC GHSL, HBASE, GMIS, gROADS, dLIGHT | 2010–2015 or older |
| TROPOMI CH4, AIRS CO/CH4/dust | Tens of km. Shows regions, not war sites. |
| ALOS-2 PALSAR-2 | No open granules over our areas |

---

## 7. Access

| Access type | Datasets |
|---|---|
| **No login** | CMR / Earthdata Search metadata, ASF Search API metadata, NISAR browse PNGs, GIBS/Worldview tiles, NASA POWER API, EONET, data.nasa.gov |
| **Free Earthdata Login** | All NISAR and Sentinel-1 files (ASF), OPERA, HLS, Black Marble (LAADS), VIIRS/MODIS fire and land products (LP DAAC), TROPOMI and IMERG (GES DISC), SWOT and DSWx (PO.DAAC), PACE and VIIRS ocean colour (OB.DAAC), SMAP (NSIDC), SEDAC files, LANCE NRT |
| **Free key** | FIRMS area API (MAP_KEY), api.nasa.gov (api_key) |

Licence: the NISAR V1 record states "NASA ESDIS Data Use and Citation Guidance" (free and open). Most NASA Earthdata products follow the same policy. ESA Sentinel data carries Copernicus terms. Record both in citations.

---

## 8. Record to keep per dataset (from the PDF practical notes)

For each dataset we actually use, record:
- name and short name
- product level
- provider (and DAAC)
- acquisition dates
- processing version (for example NISAR CRID `X05010` = BETA 1.0.2, `P05023` = PROVISIONAL 1.0.11, `P05036` = V1)
- spatial coverage (track, frame, tile)
- resolution
- terms of use
- source URL
- date accessed
- known limits (from sections 2 and 6 above)

---

## 9. Still to do

1. Confirm GSLC posting and GCOV pixel size for the 20+5 MHz mode in the NISAR product specification.
2. Test BETA vs PROVISIONAL radiometric consistency on one stable area (for example bare rock), before trusting a Jan → Jun change map.
3. Get a FIRMS MAP_KEY and test the area API for south Lebanon.
4. Check whether GEDI and ICESat-2 footprints over Nabatieh and Tyre hit buildings often enough to help estimate building height.
5. Re-check S5P version 3 (no granules over our areas yet) and PACE latency (last over LB was 1 Oct 2026).
