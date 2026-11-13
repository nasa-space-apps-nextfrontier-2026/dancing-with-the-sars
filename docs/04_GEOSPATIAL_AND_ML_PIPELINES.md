# Geospatial and ML pipelines

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Shared contracts and CRS

Sources: ARCHITECTURE.md Shared by all parts, §§1.1–1.6/2.1–2.4; PROJECT_PLAN.md §§6/8/9; NASA_DATASET_ANALYSIS.md §§2/8/9. Canonical numeric row: `area_id, metric, low, high, unit, label, source, date, safety_tag`. Proposed extensions: `value_id, lineage_ids, processing_run_id, processing_version, confidence, acquired_at, processed_at, freshness, cached, limitations, release_at, synthetic`. See [MetricValue](contracts/MetricValue.json).

ARCHITECT RECOMMENDATION: H3 IDs are lowercase hexadecimal strings with explicit resolution, not numeric JavaScript values. Use actual r9→parent r8 aggregation; cadaster intersections can be fractional and many-to-many. Preserve WorldPop total mass during resampling/area joins. CRS 4326 stores API GeoJSON and DB geography; local metric operations use EPSG:32636 for this AOI after checking source CRS. Raster processing retains source CRS until deliberate reprojection; use nearest for categorical masks and documented continuous-data resampling. Never measure metres in longitude degrees or silently equate pixel posting with resolution.

## Discovery, tiers and reproducible ingestion

M1 searches all three product versions on 151D/72. Source snapshot: BETA before through 19 Jan 2026; no acquisitions 20 Jan–17 Jun; first relevant after 24 Jun; eleven later passes through 3 Nov. Preserve actual timestamps, duplicate product versions and missing passes. A swath touching AOI does not prove complete usable overlap. Re-query and inspect valid-pixel footprint.

Tier A: six before GCOV (27 Oct–19 Jan) + three after (24 Jun–18 Jul), ~7.7 GB. Tier B: eight later (11 Aug–3 Nov), ~6.8 GB. Tier C conditional: GSLC Jan19/Jun24 plus Jan7 GUNW, ~15 GB. These sizes are source estimates, not measured here. Download only when development begins and challenge preparation rules are verified. Metadata/search/checksum first, crop immediately, share cropped derivatives, never commit raw granules.

Each run key hashes dataset versions + AOI + acquisition IDs + parameters + software revision. Save manifest and checksums, terms and retrieval dates. Download temporary file, verify size/checksum, atomically promote. Reprocessing with identical key is idempotent. Failed QA cannot update published pointers. Retain previous approved artifact set for rollback.

## Radar algorithm and failure gates

1. Validate HH/HV availability, linear/covariance semantics, band, calibration, incidence and matching track/frame; reject unsupported products. Clip AOI to common valid coverage. Detect nodata, NaN, zero/negative values before log conversion. `10*log10(power)` only when metadata establishes power; GSLC amplitude would require its own conversion.
2. Co-register using stable, distributed controls; record residual offsets. Mask water, shadow and steep slopes as Unknown. Proposed registration gate: residual median ≤0.5 output pixel and p95 ≤1 pixel on independent controls; threshold is engineering recommendation to validate, not source fact.
3. BETA 1.0.2 versus PROVISIONAL 1.0.11: fit stable-area normalization on training controls only, report before/after residuals by incidence and building density, evaluate independent stable controls. Test moisture/seasonality and noise-floor effects. Quiet-model training does not automatically eliminate calibration differences. If systematic bias/artifacts remain, mark comparisons scientifically blocked.
4. Document whether temporal aggregation averages linear power then converts to dB or averages dB. ARCHITECT RECOMMENDATION: mean calibrated power over valid dates, then dB; compare sensitivity to median/dB mean. Source says average six before/three after but does not fix this choice. Store valid-date/pixel counts.
5. Per r9 built-up cell: HH and HV dB differences; change in HH−HV; share of valid built-up pixels with HH drop >3 dB; incidence angle; building density; optional validated coherence drop. Reason codes include strong_hh_drop, hv_shift, polarization_shift, other_change, low_coverage, version_confounded.
6. Quiet sampling excludes reported ACLED/Insecurity Insight events within 2 km during Jan19–Jun24. Missing reports do not prove quiet. If fewer than ~500 cells, expand within frame only after source rights and controls review. Use spatial blocks: 80% training, 20% untouched hold-out; normalization and thresholds use training only. Store seed, blocks and leakage checks.
7. Isolation Forest primary, Robust Mahalanobis/MinCovDet comparison; z-score fallback on the same versioned feature contract if model setup fails. Record hyperparameters and feature scaling. Anomaly plus HH decrease (or separately validated coherence decrease) gives candidate damage; opposite-direction anomaly is other change. Null or failed QA is Unknown, not no damage.
8. Source candidate thresholds are training quiet-score quantiles: >95% possibly damaged, >99% moderately damaged, >99.9% destroyed/severely damaged candidate. These are provisional anomaly classes, not calibrated probabilities or proof of collapse. Do not invent separate destroyed versus severe labels when features cannot distinguish them. Report sample-size limits: ~500 controls cannot support a reliable 0.1% tail estimate.
9. Refit later-pass comparison against June baseline as source directs; store per-pass model/version and threshold so scores are not mistaken for directly comparable probabilities. Keep Jan→Jun and June→later comparisons distinct in UI. Publish r8 area results only after delay and suppression; building inference remains restricted candidate information.

## Model validation

T-ML: spatial hold-out false-alarm rate at 99th-percentile training threshold, target around 1% from source; report denominator and uncertainty interval, not guaranteed performance. ARCHITECT RECOMMENDATION: H32 science gate requires a predeclared acceptable interval after sample-size assessment at H2; report observed rate even on failure. Strike-context enrichment compares near/far and within district, with building density/incidence controls and location uncertainty buffers; association is not collapse ground truth. Inspect 20 top-change cells and some unflagged controls, logging strips/edges/shadow/vegetation alternatives. Cross-sensor agreement uses OPERA only if aligned and independent; no claimed accuracy without dated spatially matched ground truth. Retain failed tests on Sources.

T-COHERENCE: GUNW BETA/PROVISIONAL supplies short-baseline 12/24-day coherence, not a Jan–Jun pair. Cross-gap GSLC needs expert coregistration/phase assessment, matching bands, stable-area controls, baseline analysis and decorrelation attribution. Seasonal decorrelation can dominate; comparing short versus long baselines is confounded. If invalid or late, exclude coherence entirely from model and disclose that limitation.

## Humanitarian computations

Residents: WorldPop is a pre-displacement baseline. Allocate counts to residential floor-area weights only with mass-conservation checks and coverage flag; if building data incomplete, retain cell total and broaden uncertainty. Vulnerability counts need aligned age/sex data and date; missing groups are Unknown. Ranges are scenarios from input uncertainty, not statistical confidence intervals unless measured.

Affected/displaced: sum resident allocations weighted by candidate shares. Source scenario factors: destroyed/severe 1.0, moderate 0.5, possible 0.2. Label as potentially affected/displaced scenario; do not imply observed displacement. Avoid counting the same residence twice across classes/passes. Report low/high sensitivity to class/occupancy assumptions. IOM reports remain separate Reported evidence with their period.

Severity: show all five parts (damage, residents, critical facilities hit, service loss, roads cut). ARCHITECT RECOMMENDATION: normalized equal-weight exploratory rank only when all five inputs present; otherwise show partial profile and no composite rank. Team must approve weights; never hide missing inputs as zeros.

Facilities: HOTOSM type/inventory is not operating status. A dated verified report supports “Reported operating”; without it use “No detected damage. Not confirmed open.” Reported attack is not automatically damage. Nearest working hospital requires both a current credible operating report and route caveats; otherwise return Unknown.

Services: night-light decrease is possible power loss, not blackout. Water dependency requires reported/verified network relationship; satellite-observed proximity alone cannot prove substation→pump→hospital dependency. What-to-bring mapping uses source rules (water, generators/lights, medical team, radios); no invented counts, supply volumes or medical advice. Report output preserves weakest-input uncertainty.

## Alerts, cadence and corroboration

Black Marble: QA-clear nights only, use archives for 60-night baseline; keep usable-night count, date range and gaps. Below 50% baseline on two clear nights triggers possible power loss. Baseline, moon/cloud/noise masks and gap-fill influence are recorded; no trigger with insufficient valid nights. FIRMS: remove low-confidence and documented permanent hot spots; cluster within 1 km/12 h as source proposes; preserve original detections and dedup by source/product/id/time. Poll FIRMS and IODA every 30 min, lights daily, radar per actual acquisition, ACLED weekly.

IODA maps region outages, not building connectivity. Corroboration requires independent lineage families, overlapping time/space and compatible claim type. Two rehosts of one report, two visualizations of a product, or radar plus its derived class are one source. Fire plus radar supports coincident change, not a proven strike. Reviews are append-only with actor/time/reason. Fetch failure retains last-good data, marks Cached and gives last-success/error status; never overwrites with empty “all clear”.

## Local routes

Build network from permitted HOTOSM roads with topology/snap checks, directionality and access/vehicle tags; OSMnx/networkx initially, private OSRM only by ADR if needed. Source recommends 2–3 distinct paths; return fewer with reason when topology cannot support three. Confirmed closures are forbidden edges. Damage proximity alone means unknown-status edge, not confirmed closure. Unknown weights and assumed speeds are labelled engineering assumptions, not measured traffic.

Each option: (1) distance + estimated time, (2) confirmed closures avoided, (3) unknown segment number + length, (4) bridges/status, (5) nearby hazards, (6) newest evidence date plus oldest/stale essential input, (7) heavy-vehicle suitability or Unknown. Retain graph/closure revision. On confirmed closure increment revision, invalidate crossing routes, show warning and recompute. A new unverified report prompts caution/review, not automatic confirmed closure. No external route API, phone handoff or live GPS/convoy data. All results require field verification.

## Shelter candidates

Buildings first: eligible large civilian public-use buildings, no detected change is a screening input only. Exclude known hazardous/damaged/closed sites. Usable floor area = projected footprint × estimated levels × usable fraction. Source precedence: valid OSM levels; otherwise GHSL height/3 m; otherwise documented type default. ARCHITECT RECOMMENDATION: use illustrative 0.6–0.8 usable fraction and type-default 1–2 floors only in synthetic fixtures until M2 approves local assumptions. Missing height/structural information widens range or excludes candidate.

Capacity range = floor(usable area low/high ÷ selected space per person): 3.5 m² warm default, 4.5–5.5 cold, 30 m² short-term open site, 45 m² planned camp. These are source-specified planning settings, not certification of site safety or current standards. Open land needs eligible land use, slope, road access and hazard separation; thresholds require documented M2 choice. Rank by capacity near demand, access and warnings; always show basis, uncertainty and nearest reported water/health services. Protection, consent, structural and explosive-ordnance checks remain human prerequisites. Coordinates and site details coordinator-only.

## Artifact handoff

M1→M2 H16: schema-versioned cells, H3 r9, feature/reason columns, temporal pair, model/run IDs, valid coverage and QA manifest. M1→M3 H24: COG index plus bounds/CRS/nodata and checksum. M2→M3 H12/H24/H32: grid/cadaster crosswalk, MetricValue tables, permitted layer artifacts, deterministic adapter and route/shelter call signatures. M3 never infers missing lineage when loading. Data publication is atomic; rollback changes approved run pointer, not underlying evidence history.
