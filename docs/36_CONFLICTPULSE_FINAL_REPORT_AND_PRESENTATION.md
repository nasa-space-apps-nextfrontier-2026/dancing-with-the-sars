# 36 · ConflictPulse: final report and presentation pack

Status: 15 Nov 2026. New doc. Final report for NASA Space Apps 2026, challenge "Dancing with the SARs", plus the slides, video script, demo path and judge Q&A. Facts come from the files cited in each section. Where a number is not in a cited file, it is not in this doc.

---

## 1. Title and abstract

**ConflictPulse: how the war changed South Lebanon, one NISAR pass at a time.**

**Abstract.** ConflictPulse is an interactive time-series map built on free NISAR L-band radar data. It covers South Lebanon on NISAR track 151 descending, frame 72 (L2 GCOV, 20 m, HH and HV). Of 32 planned 12-day passes from 27 Oct 2025 to 3 Nov 2026, 17 were acquired and 15 are missing (`data/manifests/nisar.json`). For each acquired pass we compute per-area change in HH, HV and the HH−HV ratio against a pre-war baseline, score each built-up cell with an Isolation Forest anomaly model, check candidates against Sentinel-1, and propose likely physical drivers with look-alikes. A Responder view puts the change in context: fires, possible power loss, people, buildings, ranking and a rebuild budget per pass. All results are archive analysis per satellite pass, not live detection. Damage is always a candidate, not verified. The public app has no sign-in and shows labelled sample data; the backend holds the real results.

| Item | Value |
|---|---|
| Team | NASA Space Apps 2026 team "dancing-with-the-sars" (M1 radar: Udula; time series, docs: Thanoban) |
| Date | 15 Nov 2026 |
| Landing page (story map) | `/` |
| Dashboard | `/map` |
| Repository | https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars |
| Related docs | `docs/33_HOW_RESCUEFORCE_WORKS_AND_JUDGE_QA.md` (methods), `docs/34_CHANGE_OVER_TIME_VIEW.md` (time series), `docs/35_CONFLICTPULSE_OVERVIEW_AND_JUDGE_QA.md` (overview), `docs/model_validation.md` (model numbers) |

The product was renamed from RescueForce on 15 Nov 2026 (doc 35). Some file names keep the old name.

---

## 2. Challenge brief and how we answer it

| Challenge asks | ConflictPulse answer | Where |
|---|---|---|
| Pick a study area | South Lebanon, NISAR track 151 D, frame 72; demo box 35.0–36.0 E, 33.0–33.6 N | §3, `data/manifests/nisar.json` |
| Download free NISAR data | 17 L2 GCOV passes via ASF Search API and Earthdata; cropped in Google Colab | §4 |
| Add supplemental optical / GIS data | Sentinel-1 OPERA RTC, FIRMS, Black Marble, WorldPop, OSM, GHSL, NASADEM, Esri imagery, Cesium terrain | §4 |
| Present findings in an interactive medium | Scroll story map (landing) + interactive 2D/3D dashboard with a pass-by-pass chart | §9 |
| Hypothesize physical drivers (seen and not seen) | Driver table with radar physics, signature, alternatives and how to confirm; "what we don't see" list | §7 |
| Which polarizations highlight change | HH, HV and HH−HV, with L-band vs C-band notes | §8 |
| Future NISAR applications | Per-pass automation, short-pair InSAR, L+S band, hazards, recovery monitoring, open API | §11 |

---

## 3. Study area

### 3.1 Why South Lebanon

- **Humanitarian relevance.** The area saw heavy conflict damage. Responders and planners need to know where change happened and when.
- **Radar sees what optical cannot.** L-band radar works through smoke, cloud and at night. Smoke from strikes and fires often hides the ground from optical satellites.
- **A real time series exists.** NISAR passes every 12 days, so we can show change pass by pass, not just one before/after pair.

### 3.2 Geography

- Steep hills and valleys inland. Slopes cause radar shadow and layover (masked, §5).
- Dense villages and small towns with concrete buildings.
- Olive groves, orchards and fields between villages. These change with the season and with fire.
- A narrow Mediterranean coast with towns. Water is masked (mean HV about −23 dB vs land about −15 dB, `docs/model_validation.md` §2).

### 3.3 Pass calendar

Source: `data/manifests/nisar.json` (track 151, frame 72, descending; HH and HV).

**Acquired (17):**

| # | Date | Group | Processing version |
|---|---|---|---|
| 1 | 2025-10-27 | Before (pre-war baseline) | BETA |
| 2 | 2025-11-08 | Before | BETA |
| 3 | 2025-11-20 | Before | BETA |
| 4 | 2025-12-26 | Before | BETA |
| 5 | 2026-01-07 | Before | BETA |
| 6 | 2026-01-19 | Before | BETA |
| 7 | 2026-06-24 | After | PROVISIONAL |
| 8 | 2026-07-06 | After | PROVISIONAL |
| 9 | 2026-07-18 | After | PROVISIONAL |
| 10 | 2026-08-11 | Later | PROVISIONAL |
| 11 | 2026-08-23 | Later | PROVISIONAL (HV suspect) |
| 12 | 2026-09-04 | Later | PROVISIONAL |
| 13 | 2026-09-16 | Later | PROVISIONAL |
| 14 | 2026-09-28 | Later | PROVISIONAL |
| 15 | 2026-10-10 | Later | PROVISIONAL |
| 16 | 2026-10-22 | Later | V1 |
| 17 | 2026-11-03 | Later | V1 |

**Missed (15, no GCOV product):** 2025-12-02, 2025-12-14, 2026-01-31, 2026-02-12, 2026-02-24, 2026-03-08, 2026-03-20, 2026-04-01, 2026-04-13, 2026-04-25, 2026-05-07, 2026-05-19, 2026-05-31, 2026-06-12, 2026-07-30.

Most of the gap (31 Jan – 12 Jun 2026) falls in the war months. Missed passes are drawn as gaps and never filled in.

### 3.4 Data caveats

- **Version change.** The manifest warns: before = BETA, after = PROVISIONAL, "stable-area normalization and QA required before any comparison". Measured effect: HH differs by 0.15 dB on built-up pixels (comparable); HV is about 1.2–1.5 dB brighter in PROVISIONAL everywhere, removed by robust centring (`docs/model_validation.md` §2). The 22 Oct and 3 Nov passes are V1 products compared with a PROVISIONAL baseline.
- **Suspect pass.** 23 Aug 2026 HV is about 2 dB brighter with large bands. It is flagged and drawn hollow in the chart.
- **Stripes.** BETA banding up to 3.3 dB is removed by destriping.

---

## 4. Data downloaded

### 4.1 How we found and downloaded NISAR

1. Searched with the **ASF Search API** (`asf_search`); 336 NISAR granules over South Lebanon were found (`docs/progress/SOURCES_AND_TOOLS_USED.md`). 150 granules on other tracks were rejected (`nisar.json`).
2. Selected L2 GCOV on track 151 D, frame 72, full frame coverage, HH+HV.
3. Downloaded with an **Earthdata Login** token from the ASF Earthdata Cloud.
4. Cropped the HDF5 files to the demo box in **Google Colab** (each file is about 1.8 GB) and wrote GeoTIFFs on one 20 m grid (same grid on all 17 dates, `docs/model_validation.md` §2).

### 4.2 All data sources

| Dataset / API | Provider | Use | Public app | Freshness |
|---|---|---|---|---|
| NISAR L2 GCOV (HH, HV) | NASA/ISRO via ASF DAAC | Radar change, candidate model | Pass dates real; values sample | Per 12-day pass, archive |
| NISAR GSLC / GUNW | NASA/ISRO via ASF DAAC | Coherence test (excluded) | Not shown | Archive |
| OPERA RTC-S1 (Sentinel-1, C-band) | Copernicus / NASA OPERA via ASF | Second-sensor check | Sample | Archive |
| FIRMS VIIRS 375 m active fire | NASA FIRMS | Fire points | Sample | Every 30 min (backend) |
| Black Marble VJ146A2 / VJ246A2 (+ NRT) | NASA LAADS / LANCE | Possible power loss | Sample | Daily, night only (backend) |
| WorldPop | WorldPop | People range per cell | Sample | Yearly |
| OpenStreetMap | OSM contributors (HOTOSM / HDX) | Buildings (268,536 in the box), roads, facilities | Sample | Export date |
| GHSL GHS-OBAT building height | EU JRC | Height and floors range | Sample | Static |
| NASADEM | NASA/JPL via LP DAAC | Terrain mask | Used in model | Static |
| UCDP Candidate GED 2026 | Uppsala Conflict Data Program | Training areas, strike context only | Not shown | Jan–Sep 2026 |
| Esri World Imagery | Esri | Optical context in the map | Live tiles | Basemap |
| Cesium World Terrain / OSM Buildings | Cesium ion | 3D terrain and buildings | Live tiles | Basemap |
| World Bank Syria assessment (Aug 2025) | World Bank | Cost per m² anchor | Used in sample budget | Report |

ACLED is not used (its terms forbid model training/testing). Insecurity Insight is not used for locations (censored coordinates) (`docs/model_validation.md` §5).

---

## 5. Methods

### 5.1 Preprocessing

- **Grid:** all 17 passes on one 20 m grid.
- **Masks:** water (mean HV below −20.5 dB, plus 40 m); terrain from NASADEM (layover, shadow, slope > 25°; 5.8% of the area marked Unknown); GCOV validity mask.
- **Normalisation:** destriping and robust centring on stable areas, to remove the BETA/PROVISIONAL offset.
- **Cells:** H3 resolution 9 (about 0.1 km²); public results at resolution 8. Assessed cells: at least 25% covered by OSM buildings plus 30 m (5,783 of 11,362 built-up cells).

### 5.2 Change features (`pipelines/radar/nisar/features.py`)

| Feature | Meaning |
|---|---|
| `d_hh` | HH after − before, dB (median per cell) |
| `d_hv` | HV after − before, dB |
| `d_pol` | Change in (HH − HV): `(after_hh − after_hv) − (before_hh − before_hv)` |
| `strong_drop_share` | Share of valid pixels with HH drop below −3.0 dB (`STRONG_DROP_DB`) |
| Built density | Share of the cell covered by buildings |
| Coverage | Fewer than 8 valid pixels or under 50% valid → low coverage → **Unknown** |

**Coherence** (`coherence.py`): tested and excluded. Across the 156-day gap (19 Jan × 24 Jun), built-up median coherence is 0.167, near the 0.10 floor, with no link to events. The 12-day January pair has median 0.706 on built-up areas, so short-pair coherence is useful for future work (`docs/model_validation.md` §6).

### 5.3 Candidate model (`model.py`)

- **Isolation Forest** (scikit-learn), cross-checked with robust Mahalanobis distance.
- **Training:** quiet built-up cells with no UCDP event within 2 km (19 Jan – 24 Jun 2026).
- **Classes** from quantiles of training scores: above 95% possible, above 99% moderate, above 99.9% destroyed or severe. HH must fall (collapse direction); otherwise "other change". These are anomaly classes, not proof.
- **Hold-out false alarms** (345 quiet cells): possible 8.7% (design 5%), moderate 1.2% (design 1%), severe 1.2% (design 0.1%). The top class is shown with medium confidence only.
- **Top-20 eye check (final):** 15 plausible (3 unclear), 2 false.

### 5.4 Second-sensor check (`s1_check.py`)

| NISAR class | Sentinel-1 agrees |
|---|---|
| All candidates | 13 of 177 (7.3%, 95% CI 4.3–12.2%) |
| Moderate or severe | 6 of 43 (14.0%) |
| No detected change | 122 of 5,518 (2.2%) |

About 3.3 times more agreement in candidates than in no-change cells. The 13 cells seen by both get **Corroborated**; others stay **Observed**.

### 5.5 Per-pass slider (`change_images.py`)

Each of the 8 later passes is compared with the June–July baseline: **136–181 candidates per pass**; hold-out moderate false alarms 0.1–0.5% (`docs/model_validation.md` §3).

### 5.6 Night lights (`worker/services/nightlights.py`, `power_loss.py`)

- Baseline: median brightness of each cell's last **60 clear nights** (at least 30 needed).
- Possible power loss: below **50%** of baseline on **2 clear nights**. Too little evidence → Unknown.
- Two satellites: one alone flags **2.7%** of cell-nights; both agreeing flags **0.73%** (59,868 real cell-dates). Both → Corroborated; one → low confidence.
- Measured **at night only** (about 1:30 am); daytime shows the latest night.

### 5.7 Fires (`firms_feed.py`)

FIRMS VIIRS 375 m points from the public CSV feed, drawn with a 375 m uncertainty ring. A fire point is Observed by satellite, not a verified fire on the ground.

### 5.8 Buildings and heights (`pipelines/buildings/heights.py`)

Height from OSM levels, else GHSL (−3.0 / +4.5 m band, MAE 2.89 m), else a default range by use. Floors = height / 3 m, as a low–high range. Each row records its source.

### 5.9 Population (`worker/loaders/population.py`)

Per H3 r9 cell: `pop_low` = min(constrained, unconstrained WorldPop), `pop_high` = max. Always a range.

### 5.10 Ranking (`worker/agents/ranking.py`, `ranking_weights.json`)

Score out of 100. Weights: people 30, facility 20, damage 15, fire 15, services 10, time 5, access 5. Damage class values: severe 1.0, moderate 0.6, possible 0.3; single-sensor factor 0.75. Unknown inputs give a score **range**, not 0; a range wider than 40 points is flagged. Officers can change weights (must sum to 100).

### 5.11 Budget (`worker/agents/budget.py`, `budget_assumptions.json`)

**Cost range = affected floor area × damage share × cost per m².**

| Input | Value | Source |
|---|---|---|
| Housing | USD 450–900 /m² | World Bank Syria (Aug 2025), about US$600/m², −25% / +50% for Lebanon |
| Non-residential | USD 600–1,200 /m² | Same, about US$800/m² |
| Damage share | severe 100%, moderate 50%, possible 20% | Team rule (doc 24 §9) |
| Crews, m²/crew-month, start delay | 10–40 / 150–300 / 3–9 months | Assumptions, editable |

Recalculated at every pass from damage seen up to that pass. Label: "Planning indication only".

---

## 6. Findings

### 6.1 What the series shows

1. **Pre-war baseline (6 passes, Oct 2025 – Jan 2026):** flat, with small seasonal HV movement.
2. **War gap (31 Jan – 12 Jun 2026):** no passes. We cannot say when inside the gap a change happened.
3. **After the war (24 Jun – 18 Jul):** a step change in candidate built-up cells relative to the baseline.
4. **Later passes (11 Aug – 3 Nov):** 136–181 candidates per pass against the June–July baseline, i.e. change continued after July.

### 6.2 Real vs sample

| Statement | Status |
|---|---|
| Pass dates, missed passes, versions, suspect pass | **Real** (`nisar.json`, `model_validation.md`) |
| 177 candidates; 13 Corroborated; 136–181 per later pass; false-alarm rates | **Real** backend results (`model_validation.md`) |
| No clear link to UCDP events overall (3.2% within 1 km vs 4.3% at ≥ 5 km); top-20 lean to events (50% vs 37%) | **Real** |
| Night-light rates 0.73% / 2.7% | **Real** (doc 33) |
| Chart bars and lines, map pins, budget figures in the public app | **Sample**, labelled as sample |
| Routes and shelters | Demo drawings only |

What we may not claim: confirmed damage, accuracy, precision/recall, or totals. Counts are minimums because radar misses damage (`model_validation.md` §4).

---

## 7. Hypothesised physical drivers

Each driver is "likely", never certain. We check alternatives against the pre-war passes and the next pass.

| Driver | Radar physics | Polarization signature | What we see | Alternatives | How to confirm |
|---|---|---|---|---|---|
| **Building collapse** | Walls and ground form corner reflectors ("double bounce"). Collapse removes them. | Sharp **HH drop** (≤ −2 dB cell median; pixels below −3 dB), persists over passes; d_pol falls | Candidate cells in dense built-up areas; 13 also seen by Sentinel-1 | Demolition for construction; wet season; version offset | Persistence on next passes; Sentinel-1 VV drop; optical imagery; field reports |
| **Rubble and debris** | Broken concrete is a rough surface with many facets; more depolarised scatter | **HV rise**, HH may fall | "Other change" or mixed cells next to HH drops | Construction sites; crop growth | Persistence; optical view of debris fields |
| **Fire scars / burnt orchards** | Canopy volume is lost; less multiple scattering in leaves and branches | **HV drop**, HH small change; d_pol rises | HV drops in orchard areas near FIRMS points (sample in public app) | Harvest; seasonal leaf loss; pruning | FIRMS point within 375 m; optical burn index; season check against pre-war year |
| **Cratering / earthworks** | Ground is churned; roughness and local slope change | HH and HV both rise or change irregularly in open land | Not separated by the model (built-up cells only) | Ploughing; road works | High-res optical; short-pair coherence loss |
| **Abandoned farmland regrowth** | Untended fields grow weeds and shrubs; more volume | Slow **HV rise** over many passes | Possible gentle HV trend in later passes | Normal crop cycle; rain | Compare to the same season pre-war; optical NDVI |
| **Non-war look-alikes** | Rain raises soil moisture and dielectric constant | HH and HV **both up for one pass** only | Single-pass jumps | — | Rainfall records; check next pass |
| | Seasonal vegetation | Slow HV rise and fall | Seasonal wave in HV | — | Pre-war seasonal baseline |
| | New construction | HH rise (new corners) | Rare | — | Optical, permits |
| | Processing version change | Whole-scene offset (HV +1.2–1.5 dB in PROVISIONAL) | Removed by centring | — | Stable-area check |

### 7.1 What we don't see, and why

- **Missed passes.** 15 of 32 passes are missing, mostly in the war months. Change inside the gap cannot be dated.
- **Coherence lost over long gaps.** Across 156 days coherence is near its floor everywhere, so it gives no damage signal here.
- **Radar shadow and layover on slopes.** 5.8% of the area is masked as Unknown.
- **Small structures.** Single buildings are below the 20 m pixel / 0.1 km² cell; one-building strikes may vanish.
- **Rubble under intact roofs, or pancake collapse that keeps corners.** Backscatter may hardly change.
- **Damage before the baseline.** Destruction that predates the BETA "before" passes is invisible to the comparison (`model_validation.md` §3).

---

## 8. Polarizations

| Channel | Highlights on land | War use |
|---|---|---|
| **HH** | Double bounce from buildings; smooth surfaces | Building collapse → HH drop |
| **HV** | Volume scatter from vegetation and very rough surfaces | Rubble → HV rise; burnt orchards → HV drop; regrowth → slow rise |
| **HH − HV** | Balance of structure vs volume | Separates "structure lost" (HH falls more) from "vegetation lost" (HV falls more) |

**Note on ice (for completeness).** Over sea ice, HV/HH helps separate ice types and ridged/deformed ice, and L-band penetrates dry snow better than shorter bands. Not used in this project.

**L-band (NISAR, ~24 cm) vs C-band (Sentinel-1, ~5.6 cm).** L-band penetrates deeper into vegetation and scatters from trunks, branches and large structures, so it is less disturbed by leaves and keeps coherence longer. C-band reacts more to small elements and leaves. In our check, NISAR HH change and Sentinel-1 VV change are weakly related (Spearman 0.19, n = 5,779): the two sensors see partly different things, which is why agreement is a strong signal.

---

## 9. Interactive medium

### 9.1 Story map (landing `/`)

Scroll story: 3D globe → dive to South Lebanon → close-up of villages → cards (what NISAR is, what changed) → "Watch the change, pass by pass" section with a small interactive chart → links to the dashboard (`frontend/src/features/landing/markup.ts`).

### 9.2 Dashboard (`/map`)

- **Change over time mode** (`frontend/src/features/map/changeSeries.ts`, doc 34):
  - Chart with all 32 pass dates: bars = candidate cells, line = dB change; missed passes are gaps; war band shaded; suspect pass hollow.
  - HH / HV / HH−HV switch.
  - Budget range over time under the chart.
  - Pass slider and Play.
  - "What changed" sentence per step.
  - Likely-drivers box with alternatives.
- **Responder mode:** incident ranking, insights, decision assistant, rebuild budget, building and shelter details, Sources.
- **Views:** 2D, 3D and split; map features show in all views.
- **Labels:** Observed / Reported / Corroborated / Unknown; ranges; "candidate", "not verified".

---

## 10. Limitations and ethics

- No live claims. Radar results are archive analysis per pass. Only fires and night lights are near-real-time feeds on the backend.
- Candidates are not facts. No precision or recall; no totals.
- No vehicle or phone tracking.
- No sign-in in the public app; it shows labelled sample data. Real data needs a separate public-release step (doc 31).
- No real places are labelled as shelters; routes and shelters are demo drawings.
- Unknown is never shown as 0.
- We never use the word "safe" as a label.
- A person decides; the tool only suggests.

---

## 11. Future NISAR applications

- **Automatic per-pass processing** as each GCOV product appears.
- **Short-pair coherence / InSAR** (12-day pairs; January median 0.71 on built-up areas shows it works).
- **L + S band** (NISAR carries both) for better separation of structure and vegetation.
- **Other hazards:** floods, landslides, earthquakes, subsidence, glaciers.
- **Agriculture recovery** monitoring of orchards and fields after conflict.
- **Validation** with field reports and partner damage assessments.
- **Open API** at neighbourhood level (`GET /layers/{id}/timeseries`, H3 r8) after release approval.

---

## 12. Presentation pack

### 12.1 Ten-slide outline

| # | Title | Bullets | Speaker note |
|---|---|---|---|
| 1 | ConflictPulse | NISAR time-series map · South Lebanon · pass by pass | "We show how a war changed a landscape, one radar pass at a time." |
| 2 | The problem | Smoke, cloud, night hide the ground · Responders need where and when · Optical alone fails | "Radar sees through what optical cannot." |
| 3 | Study area | Track 151 D, frame 72 · Hills, villages, orchards, coast · 17 passes, 15 missed | "Gaps are real; we never fill them in." |
| 4 | Data | NISAR GCOV via ASF · Sentinel-1, FIRMS, Black Marble · OSM, GHSL, WorldPop | "All free and open." |
| 5 | Method | Stable-area normalisation · H3 change features · Isolation Forest + Sentinel-1 check | "Anomaly classes, not proof." |
| 6 | Findings | Step change after the war · 136–181 candidates per later pass · 13 Corroborated | "Real backend numbers from model_validation.md." |
| 7 | Physical drivers | Collapse → HH drop · Rubble → HV rise · Fire → HV drop | "Every driver is likely, with look-alikes." |
| 8 | Polarizations | HH structure · HV volume · HH−HV separates them | "L-band goes deeper than C-band." |
| 9 | Demo | Story map · Change over time · Responder | "Live click-through." |
| 10 | Limits and future | Candidates, not facts · No tracking, no sign-in · InSAR, L+S, open API | "Built to be honest about uncertainty." |

### 12.2 Three-minute video script

| Time | On screen | Voice |
|---|---|---|
| 0:00–0:15 | Landing: 3D globe spins | "This is ConflictPulse. It uses NASA-ISRO NISAR radar to show how war changed South Lebanon." |
| 0:15–0:35 | Scroll: dive to South Lebanon, close-up of villages | "Smoke and cloud hide the ground. L-band radar sees through them, every 12 days." |
| 0:35–0:55 | Cards; pass-by-pass mini chart | "17 passes acquired, 15 missed. Gaps stay gaps." |
| 0:55–1:20 | Open `/map`, Change over time mode, chart with war band | "Bars count candidate cells; the line shows HH change from the pre-war baseline." |
| 1:20–1:45 | Switch HH → HV → HH−HV | "HH drops when buildings collapse. HV drops when orchards burn. The ratio tells them apart." |
| 1:45–2:05 | Press Play; sentence and drivers box update | "Each step explains what changed and the likely driver, with alternatives." |
| 2:05–2:30 | Responder mode: ranking, fires, power, budget | "Responders see people, facilities, possible power loss and a rebuild budget range." |
| 2:30–2:45 | Toggle 2D / 3D / split; evidence labels | "Every item carries an evidence label: Observed, Reported, Corroborated or Unknown." |
| 2:45–3:00 | Closing title | "Candidates, not facts. Archive, not live. Next: short-pair InSAR and an open API." |

### 12.3 Live-demo click path

1. Open `/`; scroll through globe, dive, close-up, cards, chart.
2. Click into the dashboard (`/map`).
3. Select Change over time mode in the top bar.
4. Point at the war band and gaps; hover the hollow 23 Aug pass.
5. Switch HH, HV, HH−HV.
6. Drag the pass slider; press Play; read the sentence and drivers box.
7. Show the budget-over-time range.
8. Switch to Responder mode; open an incident; show ranking breakdown and budget.
9. Toggle 2D / 3D / split.
10. Open Sources; point at the "sample data" label.

### 12.4 Fifteen likely judge questions

1. **Why NISAR?** Free L-band, 12-day repeat, HH and HV, sees through smoke and cloud.
2. **Is this live?** No. Archive analysis per pass; products arrive days later and 15 passes are missing (doc 35 Q3).
3. **Is the public data real?** Pass dates are real; values are labelled sample. Real results are on the backend.
4. **How is a candidate found?** Isolation Forest on per-cell change features, quantile classes, HH must fall.
5. **How accurate?** No labels exist, so no accuracy. Hold-out false alarms: 8.7% / 1.2% / 1.2%; top-20 eye check 15 plausible.
6. **Independent check?** Sentinel-1 agrees 3.3× more often on candidates (7.3% vs 2.2%).
7. **Which polarization matters most?** HH for buildings, HV for vegetation and rubble; HH−HV separates them.
8. **Why not coherence?** Over 156 days it is near the floor everywhere; 12-day pairs work for future use.
9. **What about version changes?** Measured offsets; removed by stable-area centring; manifest warns.
10. **What's the 23 Aug issue?** HV about 2 dB bright with bands; marked suspect.
11. **Why no link to strike events?** Single-building strikes are small, some damage predates the baseline, backscatter is weak (model_validation §3).
12. **How is the budget computed?** Floor area × damage share × World Bank-anchored cost per m², as a range.
13. **How do you detect power cuts?** Night lights vs the cell's own 60 clear nights; below 50% on 2 nights; two satellites for high confidence.
14. **Privacy and safety?** No tracking, no sign-in, no shelters on real places, never "safe" as a label.
15. **What next?** Per-pass automation, InSAR, L+S band, field validation, open API.

---

## 13. Sources

- NASA Space Apps 2026, Dancing with the SARs, Resources tab: https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=resources
- NISAR L2 GCOV (NASA/ISRO), ASF DAAC: https://api.daac.asf.alaska.edu/services/search/param ; data at https://nisar.asf.earthdatacloud.nasa.gov/
- NASA Earthdata Search and Earthdata Login (CMR, LAADS DAAC, LANCE).
- ASF Data Search Vertex and NISAR Data User Guide (Resources tab).
- OPERA RTC-S1 (Copernicus Sentinel data processed by NASA OPERA), ASF DAAC.
- NASA FIRMS VIIRS 375 m active fire (public CSV feed).
- NASA Black Marble VJ146A2 / VJ246A2 and NRT (LAADS / LANCE).
- NASADEM (NASA/JPL, LP DAAC).
- WorldPop population.
- OpenStreetMap (© OpenStreetMap contributors, ODbL; HOTOSM export on HDX).
- GHSL GHS-OBAT building height (EU JRC, CC BY 4.0).
- UCDP Candidate GED 2026 (Uppsala Conflict Data Program, CC BY 4.0).
- Esri World Imagery; Cesium ion World Terrain and OSM Buildings; OSRM demo server.
- World Bank (Aug 2025), *The Syrian Conflict: Physical Damage and Reconstruction Assessment (2011–2024)*: https://documents1.worldbank.org/curated/en/099102025095540101/pdf/P510947-f30bd5f6-78d5-4712-9f1e-a558b5c8ba75.pdf
- World Bank Lebanon Rapid Damage and Needs Assessment (March 2025), to check housing costs (`budget_assumptions.json`).

Terms marked VERIFY in `docs/progress/SOURCES_AND_TOOLS_USED.md` must be checked before submission. AI tools (Claude) helped plan, write and check code and documents; people made the decisions.
