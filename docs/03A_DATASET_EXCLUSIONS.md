# Dataset exclusions and deferred investigations

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.

| Decision/phase | Datasets or resources | Source section | Reason and re-entry condition |
|---|---|---|---|
| Conditional stretch | RSLC; NISAR_DEM; NISAR_WATERMASK; Sentinel-1C/1D SLC | NASA_DATASET_ANALYSIS.md §3.1 | Same-processor reprocessing and extra masks/coherence exceed weekend budget; permit only validated, scoped experiment. |
| After hackathon | NISAR SME2; SMAP SPL3SMP_E / SPL4SMGP; SMAP_L4 display | NASA_DATASET_ANALYSIS.md §§3.1/3.10/4; DATASETS.md §6 | Wet-ground regional support; not validated site safety; narrower source drops SMAP. |
| Excluded current coverage | OPERA DIST-ALERT-S1; CSLC-S1; DISP-S1; ARIA S1 GUNW; NISAR UR L1/L2; GOFF; RIFG; ALOS-2 PSR2 | NASA_DATASET_ANALYSIS.md §§3.1/6 | Stale Jan–Feb, no current coverage or no granules in snapshot; re-query before future use. |
| After hackathon analytical; GIBS context only now | HLS L30/S30 downloads; HLS VI; DIST-ALERT-HLS; DIST-ANN-HLS; MOD13Q1; VNP13A1 | NASA_DATASET_ANALYSIS.md §3.2; DATASETS.md §6 | Optical/cloud QA and livelihoods extend scope. DIST-HLS display is optional, not a new analytical promise. |
| After hackathon experimental | EMIT L2A reflectance; GEDI L2B v003; ICESat-2 | NASA_DATASET_ANALYSIS.md §§2/3.2/5/9 | Material/height samples uncertain over individual buildings; GHSL is the proposed coarse fallback. |
| Conditional backup or historical only | VJ146A1/A1_NRT; VJ246A1_NRT; VJ146A3; VNP46A3; VNP46A1/A2 | NASA_DATASET_ANALYSIS.md §3.3 | Uncorrected/monthly products are not interchangeable with daily corrected A2; S-NPP source says ended 2 Nov. |
| After hackathon | MCD14DL; MCD64A1; VNP64A1; VNP14IMG | NASA_DATASET_ANALYSIS.md §3.4 | Additional fire/burn history beyond selected NOAA-20/21 VIIRS; independence cannot be assumed. |
| After hackathon regional context | TROPOMI NO2/SO2/CO/Aerosol Index; TROPOMAER; MCD19A2 MAIAC; AERDB VIIRS Deep Blue; OMPS SO2; MERRA-2 M2T1NXAER; AIRS layers | NASA_DATASET_ANALYSIS.md §§3.5/4/6 | Regional smoke/pollution, not individual strikes; latency and attribution confounders. |
| Excluded geography | TEMPO | NASA_DATASET_ANALYSIS.md §§3.5/6 | North America only in source. |
| After hackathon; visual rain context optional | DSWx-S1/HLS; SWOT LakeSP/Raster; VJ128C2; GPM IMERG Early/Late; EONET floods | NASA_DATASET_ANALYSIS.md §3.6; DATA_AND_API_PLAN.md §3 | Investigation calls some Core; narrower catalogue drops them. Natural-event context only; no general-disaster scope. |
| After hackathon, mainly Gaza | PACE OCI L2 BGC/AOP; VIIRS ocean colour; Sentinel-1A GRD-H; OCI_PACE_Chlorophyll_a; VIIRS_NOAA20_Chlorophyll_a | NASA_DATASET_ANALYSIS.md §§3.1/3.7/4 | Coastal/sewage/oil use is beyond south-Lebanon demo; PACE latency unresolved. |
| After hackathon experimental / exclude coarse inference | EMIT L2B CH4; TROPOMI CH4 | NASA_DATASET_ANALYSIS.md §3.8 | Sparse methane samples and coarse regional measurements do not establish damaged pipes. |
| After hackathon | NASA POWER; MOD11A1; VJ121A1D; ECOSTRESS L2T LSTE/L4T ESI; MERRA-2 M2T1NXSLV; heat GIBS layers | NASA_DATASET_ANALYSIS.md §3.9; DATASETS.md §6 | POWER called Core in investigation but dropped in final catalogue. Climate mode manually selected and labelled; no inferred weather safety. |
| Alternative terrain / deferred | SRTMGL1; ASTER GDEM; MCD12Q1; IMERG+LHASA; terrain GIBS | NASA_DATASET_ANALYSIS.md §§3.10/4 | NASADEM selected; coarse land-cover/landslide context is not site verification. |
| Historical cross-check only; not current people | GPWv4 count 2020; GPWv4 age/sex 2010; GRDI; SEDAC GHSL 2014/2015; HBASE; GMIS; gROADS; dLIGHT | NASA_DATASET_ANALYSIS.md §§3.11/6; DATASETS.md §6 | Old baselines; distinguish SEDAC GHSL from JRC building-height product. Never substitute for current vulnerability counts. |
| Excluded or coverage/access VERIFY | SAOCOM; RCM; RADARSAT-1 | DATASETS.md §6 | Registration/unconfirmed coverage or no open Lebanon data in source. |
| Learning only | Intro to Remote Sensing; Intro to SAR; NASA ARSET; NISAR StoryMaps; Applications White Papers; UAVSAR Postcards; CSA SAR Python tutorial | DATASETS.md §6 | Challenge-linked educational resources, not analytical datasets. |
| Excluded tools/duplicates | AppEEARS; Giovanni; NASA SVS night-lights story | DATASETS.md §6 | Not necessary analytical inputs; use selected direct products. |
| After hackathon / outside source baseline | Sentinel-2; ERA5; FAO GAEZ; KNMI; NOAA CDO; US-only datasets | DATASETS.md §6 | Other challenge sources, scope/geography mismatch; no unrelated dataset bloat. |
| Access-limited post-hackathon | WHO HeRAMS; WHO attacks database; UNMAS; Logistics Cluster; Pacific Institute; HDX HAPI; UNHCR; healthsites.io | DATASETS.md §6; NASA_DATASET_ANALYSIS.md §1 | Not assumed accessible; OSM covers inventory only. UXO cannot be observed from space; real protection/ordnance checks remain mandatory. |
| Excluded unrelated APIs | Exoplanet Archive; NASA Open; APOD; NeoWs; DONKI; Mars/InSight; GeneLab; Techport; Image Library; EPIC | NASA_DATASET_ANALYSIS.md §6; PDF p1 §1 | Not relevant measurement data; EPIC too coarse; NASA Open remains informational. |
| Excluded current service / stale | api.nasa.gov Earth imagery; EONET manmade; GPCP daily | NASA_DATASET_ANALYSIS.md §6 | Source reports 503, 2018 newest manmade, Dec 2025 endpoint respectively; not freshly rechecked. |
| Prohibited all phases | Chinese-owned sources; live vehicle/phone/convoy tracks; military/frontline information | DATASETS.md §6; PROJECT_PLAN.md §10 | Project constraints retained; official competition rule independently VERIFY. |


Every individual scientific table row is also retained in the source-by-section traceability ledger, including source counts and dates. Nothing in this list is claimed downloaded or tested here.
