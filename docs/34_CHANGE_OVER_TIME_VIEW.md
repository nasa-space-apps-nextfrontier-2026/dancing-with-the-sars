# 34 · Change over time: the NISAR time-series view

Status: 15 Nov 2026 (Thanoban). Agreed in chat before building. Branch `feature/m4-time-series-view` (from PR #47).

> **Objective.** ConflictPulse is an interactive NISAR time-series map for the "Dancing with the SARs" challenge: see how the war changed the area pass by pass (12-day passes; South Lebanon, NISAR track 151 descending, frame 72; 17 passes acquired, 15 missed), which polarization (HH/HV) shows it and the likely physical drivers.
> A **Responder** view shows what that change may mean for people and services. Radar is archive analysis per satellite pass, never live detection. No sign-in in the public app.

Name: ConflictPulse (the pulse of change in a conflict area, every 12-day NISAR pass), renamed from RescueForce on 15 Nov 2026.

## 1. Why

The "Dancing with the SARs" challenge asks for an interactive app that shows **how the surface changes over time** with NISAR radar (change maps, time-series animations, dashboards), **which polarizations** show the change, and the **physical drivers** behind it. Radar cannot support live rescue claims: NISAR passes every 12 days, products arrive days later, and 15 passes over our area are missing. So ConflictPulse now leads with **change over time, pass by pass**, and keeps the responder view next to it. Same map, same data, two equal modes.

**What we claim:** archive analysis of NISAR passes, updated per satellite pass. **What we do not claim:** live detection, confirmed damage, real-time rescue.

## 2. Study area and passes (real dates)

**South Lebanon · NISAR track 151 descending, frame 72** (`data/manifests/nisar.json`, product GCOV, HH and HV).

| Period | Passes (12-day repeat) |
| --- | --- |
| Before the war (baseline, tier A-before) | 2025-10-27, 11-08, 11-20, 12-26; 2026-01-07, 01-19 |
| After (tier A-after) | 2026-06-24, 07-06, 07-18 |
| Later passes (tier B) | 2026-08-11, 08-23, 09-04, 09-16, 09-28, 10-10, 10-22, 11-03 |
| **Missed** (never interpolated) | 2025-12-02, 12-14; 2026-01-31 … 06-12 (11 passes); 2026-07-30 |

17 passes acquired, 15 missed. The 2026-08-23 HV pass is about 2 dB too bright and is marked **suspect**. Before and after products have different processing versions (BETA vs PROVISIONAL); stable-area normalisation is applied before any comparison.

## 3. The two modes

A switch in the dashboard top bar: **Change over time** | **Responder**. The map, the incident pins and the date slider stay exactly as they are (no map or engine changes). The mode changes the right-hand panel.

| | Change over time | Responder |
| --- | --- | --- |
| For | scientists, students, journalists, planners | emergency officers |
| Shows | how an area changed after every pass, which polarization shows it, likely causes, cost over time | ranking, impacts, shelters, power, decision assistant, budget |
| Question it answers | "What changed, when, and why might that be?" | "Where should we check first?" |

## 4. What the Change over time panel shows (per selected incident)

1. **Chart, pass by pass** across all 32 dates (17 acquired + 15 missed):
   - Bars: **damage-candidate cells** in the area at each pass.
   - Line: **backscatter change vs the pre-war baseline** (dB) for the chosen polarization.
   - Missed passes are **gaps**, never joined or filled. The suspect pass is drawn hollow with a note.
   - A shaded band marks the war period with no passes (Feb–Jun 2026).
2. **Polarization switch: HH / HV / HH−HV.**
   - **HH** (horizontal send, horizontal receive): strongest from **walls and ground forming corners** ("double bounce"). Building collapse removes those corners → **HH drops sharply**.
   - **HV** (cross-polarized): from **rough, messy surfaces and vegetation** (volume scattering). Rubble fields can make HV **rise**; burnt orchards and fields make HV **drop**.
   - **HH−HV** (ratio): separates "structure lost" (HH down more than HV) from "vegetation lost" (HV down more than HH).
3. **Cost over time:** a line under the chart with the **rebuild budget range** at each pass (same formula as the budget agent, recalculated with the damage seen up to that pass). Label: "Planning indication only".
4. **Pass slider and Play:** step through the passes; missed passes are skipped; the chart cursor moves.
5. **"What changed" sentence** for the current pass, e.g. "Between 18 Jul and 11 Aug, candidate cells rose from 6 to 11; HH fell a further 0.9 dB."
6. **"Why the radar changed" (war-related drivers):** see section 5.

## 5. Drivers: rules, always a hypothesis

The panel reads the pattern of the series and states the most likely driver, the alternatives and what would confirm it. It never says "confirmed" or "safe".

| Pattern in the series | Likely war-related driver | Look-alikes to rule out | What would confirm it |
| --- | --- | --- | --- |
| Sharp **HH drop** (≤ −2 dB), HV smaller, appears between two passes and **stays** | **Building collapse** (loss of double bounce) | Building demolition for construction, wet season | Optical image, field report, still low on the next pass |
| **HV rise** with mixed HH, stays | **Rubble and debris** (rougher surface) | Construction sites, crops growing | Optical image of debris, Sentinel-1 agreement |
| **HV drop**, HH small, near a fire detection | **Fire scar** (burnt orchards, scrub) | Harvest, seasonal leaf loss | FIRMS detection near the date, optical burn scar |
| Both HH and HV up for one pass, back next pass | **Not war-related:** rain / soil moisture | — | Rainfall on that date |
| Slow HV rise and fall with the seasons | **Not war-related:** vegetation season | — | Same pattern in the pre-war passes |

Evidence label from the existing rules: one radar = **Observed**, Sentinel-1 agrees = **Corroborated**.

## 6. How the numbers are made

| Value | Source | Status |
| --- | --- | --- |
| Pass dates, missed passes | `data/manifests/nisar.json` | Real |
| Candidate cells per pass per area | Existing model results per pass (`model/slider/<date>/`) exported as `radar_candidate_change_cells` (`data/local/radar_contract/metric_values.json`) | Real in the backend; **sample in the public app** |
| HH / HV change vs baseline | The existing change rasters per pass (`change_<date>`, HH and HV), averaged per area | Real rasters exist; **sample in the public app** |
| Cost per pass | Budget formula (doc 33 §11) with the damage seen up to that pass | Sample in the public app |

**No new model training.** The trained model already has a result for every later pass; the series only reads existing outputs; drivers and sentences are rules.

The public app uses a labelled sample series shaped like the backend route `GET /layers/{id}/timeseries`. **Optional later:** open that route publicly at neighbourhood level (H3 r8) behind `PUBLIC_RELEASE_APPROVED`, and the chart switches to real numbers with no UI change.

## 7. Landing page

A new section **"Watch the change, pass by pass"**: a small interactive version of the chart for the sample incident (slider, HH/HV switch, the drivers in plain words). The hero subtitle says "pass by pass". The 3D Earth and the dive do not change.

## 8. Wording rules (unchanged plus two)

Evidence labels Observed / Reported / Corroborated / Unknown; ranges; candidates, not facts; never "safe"; no tracking. New: never "live detection"; say "per satellite pass" and "archive analysis". Causes are always "likely" with alternatives.

## 9. Future NISAR applications (for the submission)

Automatic processing of each new pass; coherence (interferometric) change once short-gap pairs are available; L-band and S-band together; the same view for floods, landslides and earthquakes; ground validation feeding back into the evidence labels.

## 10. Files

| Area | Files |
| --- | --- |
| Sample series | `frontend/public/sample/civisar-3d-sample.json`, `docs/design/civisar-3d-sample.json` (`change_series`) |
| Types and mapping | `frontend/src/types/map.ts`, `frontend/src/services/mapData.ts` |
| Panel | `frontend/src/features/map/ChangeOverTime.tsx` (+ `changeSeries.ts` rules, unit-tested) |
| Mode switch | `frontend/src/features/map/MapScreen.tsx` |
| Landing | `docs/design/rescueforce-landing-mockup.html` → `frontend/src/features/landing/` |
| Docs | this file, doc 35 (ConflictPulse overview and judge Q&A), doc 33, doc 26 |
