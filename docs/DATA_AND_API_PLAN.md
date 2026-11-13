# CIVISAR: Proposed Datasets and APIs

**Status:** proposal for the team leader to review. It does not replace [DATASETS.md](DATASETS.md) yet.
**Date:** 13 November 2026. Every dataset ID below was checked live in NASA CMR / ASF on this date.
**Based on:** the leader's [DATASETS.md](DATASETS.md) (14 sources) and our [NASA_DATASET_ANALYSIS.md](NASA_DATASET_ANALYSIS.md) (live checks of every portal in the team PDF).

Summary: keep the leader's 14 sources. Fix what the live checks showed is broken, and add one display layer that costs almost nothing. The result is **15 sources: 7 NASA, 8 non-NASA**.

---

## 1. Main decision: one NISAR track does both jobs

Demo box: south Lebanon, 35.0–36.0 E, 33.0–33.6 N.

| Track / frame | Before (BETA) | After (PROVISIONAL, V1) | Role |
|---|---|---|---|
| **151 descending, frame 72** | 6 scenes, last **19 Jan 2026** | 11 passes, **24 Jun → 3 Nov 2026** | **Main.** One before/after pair across the Mar–May 2026 strike peak (19 Jan → 24 Jun), and the time slider after June. |
| 172 ascending, frames 18/19 | 7 scenes, last 9 Jan 2026 | 10 passes, 26 Jun → 24 Oct 2026 | Second view. Sees buildings from the opposite side, which helps confirm collapses. |
| 100 ascending, frame 18 | 6 scenes, last 16 Jan 2026 | 8 passes, 21 Jun → 19 Oct 2026 | Spare |

There are no NISAR acquisitions from 20 Jan to 17 Jun 2026. Lebanon explosive-weapon incidents peaked in Mar–May 2026 (Insecurity Insight: 110, 109, 91 per month), so **without the BETA scenes the demo only shows the period after fighting paused.**

Caveat: the pair mixes software versions (BETA 1.0.2 vs PROVISIONAL 1.0.11). Check radiometric consistency on stable areas before trusting backscatter change.

## 2. NASA datasets

| # | Dataset | CMR concept IDs | Change from DATASETS.md |
|---|---|---|---|
| 1 | **NISAR L2 GSLC + GCOV, all 3 versions** | GSLC: BETA `C2850259510-ASF`, PROVISIONAL `C2854332392-ASF`, V1 `C3622244601-ASF`. GCOV: BETA `C3622214170-ASF`, PROVISIONAL `C2854338529-ASF`, V1 `C3622241360-ASF` | **Add BETA.** It is the only "before" data. |
| 2 | **NISAR L2 GUNW** (ready-made interferograms) | PROVISIONAL `C2854335566-ASF` (37 over LB), BETA `C2850261892-ASF` (22 over LB). V1 has none yet. | **Add.** DATASETS.md says "none over Lebanon", but only V1 is empty. Ready-made coherence for each 12/24-day step, so we compute our own coherence only for the one pair across the gap. |
| 3 | OPERA RTC-S1 (Sentinel-1) | `C2777436413-ASF` | Same. Current to 10 Nov 2026. |
| 4 | **Black Marble archive + NRT** | Archive: VJ146A2 `C3370789118-LAADS`, VJ246A2 `C4320924614-LAADS`. NRT: `C4193331158-LANCEMODIS`, `C4249684820-LANCEMODIS` | **Add the archive.** NRT keeps only about the last 8 days, so it has no "before" image. |
| 5 | FIRMS VIIRS 375 m fire | NRT: `C3264430167-LANCEMODIS`, `C4377939055-LANCEMODIS`. Archive: VJ114IMG `C2734197957-LPCLOUD` | **Add the archive** for fire history in the time slider. |
| 6 | NASADEM | `C2763264762-LPCLOUD` | Same |
| 7 | GIBS map layers | Leader's layers, plus `NISAR_L2_Geocoded_Polarimetric_Covariance` and `OPERA_L3_DIST-ALERT-HLS_Color_Index` | **Add 2 display layers.** The first is a free NISAR background picture (PROVISIONAL and V1 dates only). The second shows burned orchards and cleared land with no processing (DIST-ALERT-HLS, `C2746980408-LPCLOUD`, current to 5 Nov 2026). |

**Optional:** NISAR observation plan `NISAR_COP` (`C2727904608-ASF`, about 9 days ahead) for a "next radar pass over this area" note.

## 3. Non-NASA datasets

| # | Dataset | Decision |
|---|---|---|
| 8 | OSM / HOTOSM | Use the **HDX HOTOSM exports** (`hotosm_lbn_buildings`, `hotosm_lbn_roads`) as the main copy. Use Overpass only for small live queries; it was overloaded and returning errors when tested on 13 Nov 2026. |
| 9 | **GHSL building height** (EU JRC, 100 m) | **Add** as the height fallback for shelter capacity. Only 0.28% of about 798k OSM buildings in Lebanon have `building:levels`. Order: OSM `building:levels`, then GHSL height ÷ 3 m per floor, then a default by building type. **(unverified accuracy in south Lebanon)** |
| 10 | WorldPop | Same |
| 11 | UNDP / CNRS-L Lebanon assessments | **The main check for our damage map** |
| — | ~~UNOSAT~~ | **Drop for Lebanon.** HDX has no UNOSAT war-damage dataset for this area (checked 13 Nov 2026). |
| 12 | ACLED | Same. Read its terms of use before showing raw events. |
| 13 | IODA | Same |
| 14 | IOM DTM + Meta Movement Distribution Maps | Same |
| 15 | Insecurity Insight | Same. It also gives the demo story: the Mar–May 2026 peak. |

**Agreed with DATASETS.md section 6 (dropped):** DSWx, GPM IMERG, SMAP, NASA POWER, SEDAC, TROPOMI, SAOCOM, EONET.
One risk: rain can lower L-band coherence. If a change looks suspicious, the GIBS `IMERG_Precipitation_Rate` layer is a no-cost visual check.

## 4. APIs

| API | For | Key / login |
|---|---|---|
| **ASF Search API** (`https://api.daac.asf.alaska.edu/services/search/param`, Python `asf_search`) | NISAR (BETA, PROVISIONAL, V1) and OPERA RTC-S1 scenes by track and frame | None to search |
| **CMR Search API** (`https://cmr.earthdata.nasa.gov/search/`) | Black Marble, FIRMS archive, NASADEM, DIST-ALERT-HLS, NISAR_COP | None to search |
| **earthaccess** + **Earthdata Login** | All NASA downloads | Free account for each team member |
| **FIRMS API** (area endpoint) | Live fire points | Free MAP_KEY |
| **GIBS WMTS** (`https://gibs.earthdata.nasa.gov/`) | Map backgrounds and display layers | None |
| **HDX CKAN API** (`https://data.humdata.org/api/`) | HOTOSM, Meta movement, DTM, Insecurity Insight | None |
| IODA v2 API | Internet outages (`LB`) | None |
| WorldPop REST API | Population rasters | None |
| ACLED API | Conflict events | Free account |
| IOM DTM API | Displacement numbers | Free key |
| Overpass API | Small OSM queries only | None |
| **Routing: run locally** (OSMnx / networkx, or our own OSRM) | Inbound and outbound route options | **No outside service.** Route requests reveal where responders and evacuees are going, so they must not go to a public routing server. |

**Not used:** api.nasa.gov (Earth imagery endpoint returned 503 in testing; the rest is mostly space data) and EONET (natural events only).

## 5. Changes to raise with the leader

1. Add the NISAR **BETA** collections (section 2, row 1). Without them there is no "before" image for the 2026 escalation.
2. Add **GUNW** PROVISIONAL and BETA. "None over Lebanon" in DATASETS.md is true only for V1.
3. Add the **Black Marble archive** (VJ146A2, VJ246A2) next to NRT.
4. Add a **building-height fallback** (GHSL), because OSM `building:levels` is almost empty.
5. **Drop UNOSAT** for Lebanon; use UNDP / CNRS-L for validation.
6. Use track **151D frame 72** for both the before/after pair and the time series.
7. Keep **routing local**.
