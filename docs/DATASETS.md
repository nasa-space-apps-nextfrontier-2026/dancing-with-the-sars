# CIVISAR: Dataset Catalogue

Every dataset we may use, where it comes from and what it does for us. See [PROJECT_PLAN.md](PROJECT_PLAN.md) for how they fit together.

Sources collected on 13 November 2026 from:
- the **Dancing with the SARs** Resources tab (our challenge),
- the Resources tabs of other 2026 Space Apps challenges (allowed, as long as the data is open),
- the team PDF *NASA Open Data Links – Earth Impact Intelligence*,
- earlier planning research.

Rules: at least one NASA or partner space-agency dataset is required (ours is NISAR). Nothing Chinese-owned. Every dataset used must be cited with the record in section 7.

---

## 1. Required core dataset (from our challenge's Resources tab)

### NISAR via ASF Vertex / ASF Search API: **our primary dataset**

| Product | Level | What it is | Our use |
|---|---|---|---|
| **GCOV** | L2 | Geocoded, calibrated backscatter (multiple polarizations) | **Main input.** Backscatter change between dates gives candidate damage. Polarization comparison (HH vs HV) helps separate collapsed buildings from other changes. |
| **GSLC** | L2 | Geocoded single-look complex | Coherence loss between dates, the strongest damage signal for built-up areas. |
| **GUNW** | L2 | Geocoded unwrapped interferogram | Coherence layers ready-made, so we can skip some processing. |
| RSLC | L1 | Range-Doppler single-look complex | Only if L2 products are missing. |
| SME2 | L3 | Soil moisture | Not core. Possible use: wet ground check for shelter sites. |

**Coverage check (ASF Search API, 13 Nov 2026, all products, provisional "PR" granules):**

| Area (search box) | NISAR granules | Tracks found |
|---|---|---|
| South Lebanon (35.0–36.0 E, 33.0–33.6 N) | 336 | Path 100 ascending, 172 ascending, 151 descending |
| Gaza (34.2–34.6 E, 31.2–31.6 N) | 256 | Path 100 ascending, 151 descending, 79 descending |
| Kyiv (30.2–30.8 E, 50.2–50.6 N) | 250 | Path 71 and 143 ascending, 65 and 166 descending |

NISAR data exists over all three areas. **Still to do:** list acquisition dates per track and pick same-track before/after pairs for the main study area.

Related guides from the Resources tab:
- NISAR Data User Guide (ASF): https://nisar-docs.asf.alaska.edu/
- ASF Vertex: https://search.asf.alaska.edu/
- ASF Search API docs: https://docs.asf.alaska.edu/api/overview/
- Earthdata Search: https://search.earthdata.nasa.gov/
- Earthdata Login (needed for downloads): https://urs.earthdata.nasa.gov/
- Intro to SAR: https://www.earthdata.nasa.gov/learn/earth-observation-data-basics/sar
- NASA ARSET trainings (SAR, NISAR, disasters): https://appliedsciences.nasa.gov/get-involved/training
- NISAR Applications White Papers: https://nisar.jpl.nasa.gov/applications/societal-benefit/
- NISAR StoryMaps (presentation ideas): https://nisar.jpl.nasa.gov/applications/arcgis-storymaps/
- UAVSAR Postcards (false-colour composite ideas): https://uavsar.jpl.nasa.gov/education/postcards.html

## 2. Partner space-agency SAR (from our challenge's Resources tab)

| Dataset | Agency | Use for us | Notes |
|---|---|---|---|
| **SAOCOM** | CONAE (Argentina) | **Second L-band source.** Same band as NISAR, so it is a good cross-check or gap filler. | Needs registration (ONE CLICK profile). Check coverage over our area. https://catalogos.conae.gov.ar/catalogo/catalogoSatSaocomInfo.html |
| RADARSAT Constellation Mission (RCM) | CSA (Canada) | C-band cross-check, if open scenes exist over our area | Open data portal: https://donnees-data.asc-csa.gc.ca/en/dataset/rcm |
| RADARSAT-1 | CSA | Historic archive (1995–2013). Not useful for current war damage. | https://donnees-data.asc-csa.gc.ca/en/dataset/radarsat1 |
| CSA SAR Python tutorial | CSA | Learning and quick-start code for SAR processing | https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial |
| Sentinel-1 (via NASA OPERA RTC-S1, DIST-S1) | ESA, processed by NASA | Extra dates between NISAR passes. Reference method used by existing war-damage tools. | Via Earthdata / ASF |

## 3. NASA Earth data for impact layers

| Need | Dataset | Where | Notes |
|---|---|---|---|
| Power outage | Black Marble VJ146A1/A2 (NOAA-20), VJ246 (NOAA-21) | Earthdata | Daily, about 500 m. Do not use Suomi NPP (VNP46), which stopped delivering data on 2 Nov 2026 (unverified). |
| Fires after strikes | **FIRMS** (MODIS, VIIRS active fire) | https://www.earthdata.nasa.gov/data/tools/firms | Also listed in the *MODIS and VIIRS Hot Spots* challenge. Near real time. |
| Population | SEDAC GPWv4 | Earthdata / SEDAC | About 1 km. Age and sex breakdown only for 2010. |
| Roads (backup) | SEDAC gROADS | Earthdata / SEDAC | 1980–2010 only. Cross-check use. |
| Elevation and slope | NASADEM, SRTM | Earthdata | Shelter site slope filter, line-of-sight to roads. SRTM is listed in the *Adapting Farms* challenge. |
| Land cover | MODIS land cover (MCD12Q1) | LP DAAC https://lpdaac.usgs.gov/products/ | Open-land filter for shelter sites |
| Optical imagery | HLS (Harmonized Landsat Sentinel-2), Landsat | Earthdata, https://earthexplorer.usgs.gov/ | Visual before/after context, open-land check |
| Surface water | OPERA DSWx | Earthdata | Excludes wet or flooded sites |
| Rain check | GPM IMERG | https://gpm.nasa.gov/data | Rules out rain as a cause of radar change |
| Soil moisture | SMAP, NISAR SME2 | Earthdata | Optional ground condition for open-land shelter |
| Weather for responders | NASA POWER | https://power.larc.nasa.gov/ | Temperature, for heat/cold needs at shelters (also decides 3.5 vs 4.5 m² covered space) |
| Map layers | GIBS / Worldview | https://www.earthdata.nasa.gov/data/tools/gibs, https://worldview.earthdata.nasa.gov/ | Ready web-map layers (night lights, fires, true colour). Visual only, not a substitute for NISAR analysis. |
| Time series tools | AppEEARS, Giovanni | https://appeears.earthdatacloud.nasa.gov/, https://giovanni.gsfc.nasa.gov/ | From the *Earth System Trend Detective* challenge. Fast subsets and time series for night lights and land data. |
| Night-light storytelling | NASA SVS "Change in Night Lights 2012–2023" | https://svs.gsfc.nasa.gov/5313/ | From the *Earth Information Jukebox* challenge. Presentation context. |
| Dataset search | data.nasa.gov, api.nasa.gov | | Search and citation only. api.nasa.gov is mostly space APIs. EONET covers natural events only, so we do not use it. |

## 4. Other open datasets from Space Apps challenge pages

Allowed and open, but secondary for our case:

| Dataset | Challenge page | Possible use |
|---|---|---|
| Copernicus Sentinel-2 (Copernicus Data Space) https://dataspace.copernicus.eu/ | Adapting Farms | 10 m optical before/after, building and open-land check |
| ERA5 reanalysis https://cds.climate.copernicus.eu/ | Adapting Farms | Weather context |
| GEDI https://gedi.umd.edu/data | Adapting Farms | Not needed |
| ECOSTRESS https://ecostress.jpl.nasa.gov/data | Adapting Farms | Heat stress at shelters (optional) |
| FAO GAEZ https://gaez.fao.org/ | Adapting Farms | Food and farmland context (optional) |
| KNMI Climate Explorer https://climexp.knmi.nl/ | Trend Detective | Not needed |
| NOAA Climate Data Online https://www.ncei.noaa.gov/cdo-web/ | Trend Detective | Station weather (optional) |

US-only datasets on those pages (USDA, NLCD, NAIP, CropScape, PRISM, SSURGO, NWIS, CoCoRaHS, OpenET, LANDFIRE) do not cover our areas.

## 5. Humanitarian and ground-truth data (non-NASA)

| Dataset | Use | Notes |
|---|---|---|
| UNOSAT damage assessments (HDX) | Validation reference for damage classes | Destroyed / severe / moderate / possible |
| UNDP / CNRS-L Lebanon assessments | Validation for south Lebanon | |
| Conflict Ecology InSAR damage results | Validation and comparison | |
| OpenStreetMap | Buildings, building type, levels, roads, hospitals, schools, water, power | Main GIS base. `building:levels` gives floor area for shelter capacity. |
| healthsites.io | Health facilities | |
| WHO HeRAMS | Facility functionality (fully, partly, not functioning) | The reference for "working". Access may be restricted. |
| WHO Surveillance System for Attacks on Health Care | Reported attacks on facilities | Downloadable |
| Insecurity Insight (HDX) | Attacks on health, water, education | Updated weekly |
| UNMAS / mine-action data | Explosive hazard areas | Aggregated only |
| IOM DTM, UNHCR | Displacement numbers | Aggregated |
| OCHA HDX / HAPI | Humanitarian indicators, access constraints | |
| Logistics Cluster | Road access constraints | |
| WorldPop | Population about 100 m, age and sex | Main population source |
| Pacific Institute Water Conflict Chronology | Attacks on water systems | Context |

## 6. Not used

- Exoplanet Archive, NASA Open innovation pages: not relevant.
- EONET: natural events only.
- Any Chinese-owned dataset, API or service: barred by Space Apps rules.
- Live vehicle or phone-location data: not possible with our data and unsafe (see plan).

## 7. Record to keep for every dataset used

From the team PDF practical notes. Keep one record per dataset, so the AI agents and the citations page can read it:

| Field | Example |
|---|---|
| Dataset name | NISAR L2 GCOV |
| Product level | L2 |
| Provider | NASA/ISRO via ASF |
| Acquisition date(s) | (per scene) |
| Processing version | (from granule metadata) |
| Spatial coverage | Track, frame, bounding box |
| Resolution | |
| Terms of use / licence | |
| Source URL | |
| Date accessed | |
| Known limits | e.g. provisional, not validated before 21 Oct 2026 |
