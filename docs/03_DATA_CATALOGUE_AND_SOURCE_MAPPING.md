# Data catalogue and source mapping

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Inventory policy

Sources: DATASETS.md §§1–7; DATA_AND_API_PLAN.md §§1–5 (proposal); NASA_DATASET_ANALYSIS.md §§0–9; PDF pp1–2. Current numbered 14: NISAR, OPERA, Black Marble, FIRMS, NASADEM, GIBS, HOTOSM, WorldPop, UNOSAT, UNDP/CNRS-L, ACLED, IODA, IOM+Meta, Insecurity Insight. Proposed 15: DS01–DS15 below. A01/A02 are separately disclosed supporting/optional assets; they are not hidden additions to the claimed family count. A list of product variants is not a count of independent datasets.

The recommended 15-family baseline is **PROPOSED**, not a replacement of DATASETS.md. Seven NASA-operated families does not mean seven directly linked challenge resources. The original count of six tab/tool families conflicts with explicit marks (D15). No collection, API or licence was live tested in this task. All rows: **live tested here = No**; previous check claims are only the dated sources. Metadata known from the supplied proposal is copied below, never invented.

## Identity, coverage, time and measurement matrix

| ID | Provider / family | Challenge mark | Extent | Temporal resolution | Latency | Version | Unit |
|---|---|---|---|---|---|---|---|
| DS01 | NASA/ISRO, ASF / NISAR GCOV/GSLC | Tab | LB 151D/72; 172A and 100A secondary | 12-day nominal; actual gaps | 36–72 h source estimate; VERIFY | BETA 1.0.2 / PROVISIONAL 1.0.11 / V1 per manifest | linear backscatter → dB; GSLC complex phase |
| DS02 | NASA/ISRO, ASF / NISAR GUNW | Tab tool (proposed classification) | LB footprint VERIFY by pair | 12/24-day pairs | VERIFY | BETA and PROVISIONAL; no V1 LB in snapshot | coherence 0–1; phase radians (metadata verify) |
| DS03 | NASA OPERA / ESA / ASF / OPERA RTC-S1 | Tab tool | LB; global mission coverage per burst | few days, actual acquisitions | latest snapshot 10 Nov 2026 | V1 plus burst processing version | backscatter; normalize per product metadata |
| DS04 | NASA LAADS/LANCE; NOAA-20/21 / Black Marble archive + NRT | Tab tool | LB crop; global product | daily | NRT rolling ~8 days; archive A2 ~16-day lag source report | VJ146A2/VJ246A2; granule version required | radiance units from scientific metadata; ratio dimensionless |
| DS05 | NASA FIRMS/LP DAAC; NOAA-20/21 / FIRMS VIIRS archive + NRT | Tab tool | LB AOI; global coverage | several overpasses/day | NRT; observed API latency VERIFY | VJ114IMGTDL_NRT/VJ214IMGTDL_NRT + VJ114IMG archive | point detection, confidence, FRP unit from product |
| DS06 | NASA LP DAAC / NASADEM_HGT | Tab tool | 2–3 tiles over AOI VERIFY | static | none; historical baseline | product/granule version from metadata | elevation m; derived slope degrees |
| DS07 | NASA GIBS/Worldview / GIBS display families | Other (PDF), even though NASA-operated | layer-specific AOI and dates | layer-specific daily/static | layer-specific VERIFY | WMTS capability identifier, style and time | rendered pixels; never numerical evidence |
| DS08 | OpenStreetMap/HOT/HDX / HOTOSM buildings/roads + bounded Overpass | Other | Lebanon exports, AOI crop | edits live; export monthly source estimate | export timestamp required | resource revision/OSM timestamp | geometry m² after projection; tags/levels |
| DS09 | European Commission JRC / GHSL building height | Other | 100 m tile covering AOI VERIFY | epoch static | not current individual building measurements | height product release/epoch VERIFY | m; height / 3 m illustrative floor estimate |
| DS10 | WorldPop / WorldPop R2025A 2026 + demographics | Other | Lebanon 100 m proposed product VERIFY | annual; age/sex may differ | publication-dependent | R2025A / 2026 source proposal; confirm release | people per pixel; age/sex ranges |
| DS11 | UNDP and CNRS-L / UNDP / CNRS-L assessments | Other | Lebanon exact overlap and dates VERIFY | event assessment | unknown | assessment publication and survey period VERIFY | reported damage categories |
| DS12 | ACLED / ACLED | Other | Lebanon, authorized subsets | weekly source cadence | publication delay VERIFY | dataset extract date | reported events; location precision |
| DS13 | Georgia Tech IODA / IODA v2 | Other | LB, South Lebanon/An Nabatiyah identifiers VERIFY | near-real-time source claim | observed lag VERIFY | endpoint and response version | outage metric native units; regional status |
| DS14 | IOM / Meta via HDX / IOM DTM + Meta Movement Distribution Maps | Other | Lebanon spatial support/coverage VERIFY | DTM weekly; Meta every 2 weeks source claim | publication lag VERIFY | report period / resource revision | aggregate people and movement index; never individual |
| DS15 | Insecurity Insight via HDX / Insecurity Insight | Other | Lebanon report geometry/precision VERIFY | weekly to monthly | report lag VERIFY | aid-security-risk-in-lebanon revision | reported incidents, facility attacks |
| A01 | OCHA/HDX / OCHA admin and cadasters (support asset) | Other | Lebanon: 8 governorates/26 districts/1,627 cadasters source claim | static revisions | VERIFY | boundary dataset/revision VERIFY | polygon boundaries and stable codes |
| A02 | NASA/ISRO, ASF / NISAR_COP (optional support) | Tab tool proposed | future AOI coverage must be intersected | updated observation plan | ~9 days ahead in snapshot | plan publication/version | scheduled time, track/frame |
| X01 | UNOSAT/HDX / UNOSAT Lebanon damage (current catalogue only) | Other | No usable LB dataset found in supplied checks | event-specific | not available | not known | damage classes if actually available |


## Access, rights and quality matrix

| ID | Download | Credentials | Licence/terms status | Quality limit | Update schedule | Live tested here |
|---|---|---|---|---|---|---|
| DS01 | ASF/CMR + earthaccess | Earthdata Login | NASA ESDIS citation; verify each version | Mixed processing, long gap, incidence and season | Each acquired pass, precompute | No |
| DS02 | ASF/CMR + earthaccess | Earthdata Login | NASA guidance, per-product verification | 22 BETA + 37 provisional reported; no cross-gap pair | Conditional per pass | No |
| DS03 | ASF + earthaccess | Earthdata Login | NASA citation + Copernicus terms VERIFY | 30 m spec; C/L-band differences | Optional pass check | No |
| DS04 | CMR + earthaccess | Earthdata Login | NASA use/citation VERIFY | ~500 m; clouds/moon/gap-fill; no building-level power certainty | Daily; 60 clear-night baseline | No |
| DS05 | FIRMS area API; CMR archive | server MAP_KEY; Earthdata for files | NASA citation and API limits VERIFY | 375 m spec; false/permanent hotspots; not strike attribution | Every 30 min; archive history | No |
| DS06 | CMR + earthaccess | Earthdata Login | NASA guidance VERIFY | 30 m spec; terrain not building stability | Once; source revision | No |
| DS07 | WMTS capability and tiles | none per source | layer-specific attribution and caching terms VERIFY | BETA NISAR blank in source check; resolution varies | Capabilities preflight; chosen display date | No |
| DS08 | HDX CKAN primary; small Overpass fallback | none source-reported | ODbL attribution/share-alike implications VERIFY | missing levels, roads and facility status; 0.28% levels source snapshot | Once demo; refresh on export revision | No |
| DS09 | JRC download, tile and metadata | access VERIFY | JRC product licence and citation VERIFY | pixel average cannot determine a building floor count | Once demo | No |
| DS10 | WorldPop REST/download | none source-reported | product-specific licence VERIFY | pre-displacement baseline, not people currently present | Once per release | No |
| DS11 | publisher/HDX if obtainable | licence/access VERIFY | permission and redistribution VERIFY | No usable 2026 reference found in architecture check | Only after verified acquisition | No |
| DS12 | ACLED API or permitted HDX export | account credentials server-only | ToS must authorize planned use; raw redistribution blocked pending review | approximate event location; strike ≠ collapse | Weekly; context snapshot sufficient demo | No |
| DS13 | IODA v2 API | none source-reported | API use/attribution VERIFY | regional availability ≠ a facility connection | Every 30 min | No |
| DS14 | DTM API / HDX CKAN | DTM key; HDX none source-reported | Meta source says CC BY; confirm exact licence and DTM terms | sampling, aggregation and displacement gaps | Stretch periodic import | No |
| DS15 | HDX CKAN / permitted export | none source-reported | dataset licence, disclosure restrictions VERIFY | reporting bias, approximate positions; duplicate reports possible | Bounded demo snapshot; periodic refresh later | No |
| A01 | HDX CKAN resource | none source-reported | resource-specific terms VERIFY | boundary versions and overlaps; retain fractional joins | Once | No |
| A02 | CMR/ASF metadata | none search; file auth VERIFY | NASA guidance VERIFY | schedule not a guarantee of acquisition | Stretch refresh | No |
| X01 | HDX discovery only | VERIFY | VERIFY before reuse | not a promised validation source | Recheck once H0 | No |


## Consumption, security and storage matrix

| ID | Layer | Function | Sensitivity | Local storage | Fallback | Owner task |
|---|---|---|---|---|---|---|
| DS01 | HH/HV change; candidate damage | Damage | restricted r9; delayed suppressed r8 | raw HDF5; cropped COG; cells | z-score on valid GCOV; no imagery substitution | M1-01 |
| DS02 | optional coherence | Damage | restricted | private rasters and paired manifest | omit feature; retain GCOV | M1-04 |
| DS03 | Sentinel-1 change | Damage; Alert | restricted detailed products | COG and cross-sensor QA | document unavailable; no fabricated agreement | M1-04 |
| DS04 | night lights; possible power loss | Services; Alert; Movement | aggregated services; restricted facility links | private raster + area statistics | last good Cached; insufficient clear nights → Unknown | M2-03 |
| DS05 | fires; alerts | Alert; Services; Corroboration | precise proximity restricted | observations and clustered GeoJSON | Cached recent feed; no recent signal ≠ no fires | M2-03 |
| DS06 | internal slope constraint | Shelter; Route | restricted derived site scores | cropped DEM/slope | open land Unknown if DEM absent | M2-01 |
| DS07 | backgrounds and context | none (presentation) | public approved background; restricted view proxy | bounded cached display tiles | neutral local background with provenance notice | M4-01 |
| DS08 | buildings/facilities/roads | Facility; Route; Shelter | critical sites/roads restricted | private GeoPackage/PostGIS/PMTiles | synthetic graph; type-default levels labelled | M2-01 |
| DS09 | capacity input, no public site layer | Shelter; People | restricted derivatives | private height raster, uncertainty flags | type default low/high; do not invent certainty | M2-01 |
| DS10 | population and affected ranges | People; Report | no identifiable public concentrations | private raster and aggregated values | Unknown demographics if not aligned; never old age data as current | M2-02 |
| DS11 | analyst validation overlay | Damage (check only) | licensed restricted report/geometry | private report and aligned comparison | quiet hold-out/manual QA; no accuracy claim | M1-03 |
| DS12 | restricted conflict context; future watch list | Corroboration; Alert | restricted reports; no tactical/military fields | private filtered event table | omit raw events; quiet sampling caveat if absent | M2-03 |
| DS13 | internet disruption | Services; Alert | regional aggregate | raw bounded response and normalized status | last-good Cached; no inference at building scale | M2-03 |
| DS14 | coarse delayed movement | Movement; People | sensitive displacement, no exact camps | private coarse tables; sanitized trend only | Unknown; retain static baseline | M2-06 |
| DS15 | reported attacks/corroboration | Facility; Corroboration | restricted; remove military/frontline details | private normalized reports | omit unavailable; no corroboration upgrade | M2-03 |
| A01 | area/admin joins | People; Report | public admin geometry allowed after review | PostGIS + area crosswalk | H3 only with unknown admin code | M2-01 |
| A02 | next pass note | Orchestrator | public generalized schedule after review | plan manifest | show schedule unavailable | M1-04 |
| X01 | none until approved availability | Damage (validation only) | restricted if obtained | no fictitious files | DS11 conditional or independent model QA | M1-03 |


## CMR identifiers from DATA_AND_API_PLAN.md §2

| Family | Identifiers |
|---|---|
| DS01 | GCOV BETA C3622214170-ASF; PROVISIONAL C2854338529-ASF; V1 C3622241360-ASF. GSLC BETA C2850259510-ASF; PROVISIONAL C2854332392-ASF; V1 C3622244601-ASF |
| DS02 | BETA C2850261892-ASF; PROVISIONAL C2854335566-ASF; V1 ID not supplied, no invention |
| DS03 | C2777436413-ASF |
| DS04 | archive VJ146A2 C3370789118-LAADS; VJ246A2 C4320924614-LAADS; NRT C4193331158-LANCEMODIS and C4249684820-LANCEMODIS |
| DS05 | NRT C3264430167-LANCEMODIS and C4377939055-LANCEMODIS; VJ114IMG archive C2734197957-LPCLOUD |
| DS06 | C2763264762-LPCLOUD |
| DS07 | GIBS is WMTS; underlying DIST-ALERT-HLS C2746980408-LPCLOUD |
| A02 | C2727904608-ASF |


Unlisted non-NASA CMR IDs: not applicable. Unknown product versions stay null/VERIFY until ingestion. Each downloaded granule records acquisition start/end, file URL, access time, product level, processor CRID (source examples X05010/P05023/P05036), CRS, units, nodata, pixel size, coverage, checksum and terms snapshot.

## API adapter register

| Adapter | Source URL / access | Credential and bounding rule | Owner / fixture |
|---|---|---|---|
| ASF Search | https://api.daac.asf.alaska.edu/services/search/param | no search key; AOI/date/track/frame/collection; paginate and dedup | M1-01 / metadata-only scene |
| CMR Search | https://cmr.earthdata.nasa.gov/search/ | no search key; concept IDs and time/extent; retain pagination evidence | M1-01 / granule manifest |
| earthaccess / Earthdata Login | https://urs.earthdata.nasa.gov/ | each member's account; server token; no shared secret | M1-01 / download skipped in fixtures |
| FIRMS | https://firms.modaps.eosdis.nasa.gov/api/ | MAP_KEY env; AOI/window bounded; redact key from path/logs | M2-03 / fire response |
| GIBS WMTS | https://gibs.earthdata.nasa.gov/ | no key; verify capabilities, matrix, time, resolution | M4-01 / cached background |
| HDX CKAN | https://data.humdata.org/api/ | package/resource version; permitted download URLs allowlist | M2-01 / package metadata |
| WorldPop REST | https://www.worldpop.org/rest/data | bounded country/year; check raster units and release | M2-02 / population crop |
| IODA v2 | https://api.ioda.inetintel.cc.gatech.edu/v2/ | no key per source; region code and bounded window | M2-03 / regional outage |
| ACLED | canonical endpoint/auth from account docs, VERIFY | server-only account; no undocumented URL assumed | M2-03 / synthetic event |
| IOM DTM | endpoint/version from key documentation, VERIFY | key env; coarse region/period only | M2-06 / aggregate |
| Overpass | selected public instance VERIFY | tiny bounded query only; no bulk Lebanon query, no routing | M2-01 / OSM extract |
| Local routing | internal Python callable or private OSRM | no internet destination request, egress denied | M2-04 / synthetic graph |

No generic api.nasa.gov download assumption. PDF p2 §4 requires current auth and rate-limit checks per service. Requests use bounded retries/backoff, Retry-After, timeouts and last-good fallback; M3 owns scheduling, M2 owns adapter parsing/science.

## GIBS display registry

MVP contexts: `VIIRS_NOAA20_GapFilled_BRDF_Corrected_DayNightBand_Radiance`, `VIIRS_NOAA21_GapFilled_BRDF_Corrected_DayNightBand_Radiance`, `VIIRS_NOAA20_Thermal_Anomalies_375m_All`, `VIIRS_NOAA21_Thermal_Anomalies_375m_All`, `HLS_S30_Nadir_BRDF_Adjusted_Reflectance`, `Reference_Features`, `Reference_Labels`. Proposed optional additions: `NISAR_L2_Geocoded_Polarimetric_Covariance`, `OPERA_L3_DIST-ALERT-HLS_Color_Index`, `OPERA_L2_Radiometric_Terrain_Corrected_SAR_Sentinel-1` and `IMERG_Precipitation_Rate` for visual rain confounders. Validate exact capabilities and dates; no BETA backdrop assumed. `VIIRS_Black_Marble` ends at 2016 in the source and is not current night-light evidence. Never calculate severity, capacity or population from rendered GIBS pixels.

## Licence, citation and retention register

For every ID, M2 records licence name/version/URL, rights holder, attribution text, permitted derivative sharing, redistribution, expiry and restrictions in SourceRecord. NASA/Copernicus/OSM obligations are recorded separately, not erased by combining data. ACLED/DTM/Meta/assessment terms remain VERIFY; hide unapproved raw layers and exports. Publication requires source_url, dates, version, coverage and access date. All sensitive values use the retention policy in [security](07_SECURITY_PRIVACY_AND_RBAC.md); no licence uncertainty is interpreted as permission.

## Exclusion and conditional backlog ledger

See [dataset exclusions](03A_DATASET_EXCLUSIONS.md) for every source-listed alternative, including investigation items called Core but omitted by the narrower proposal. This is an auditable decision, not permission to expand the demo.
