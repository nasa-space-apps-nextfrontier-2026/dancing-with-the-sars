# 35 · ConflictPulse: overview, methods and judge Q&A

Status: 15 Nov 2026 (Thanoban). New doc. It sums up the product under its new name. It does not replace doc 33 (methods, sources, file paths) or doc 34 (the plan for the time-series view). Where this doc and doc 33 differ in wording about "live", this doc is the current position.

> **Objective.** ConflictPulse is an interactive NISAR time-series map for the "Dancing with the SARs" challenge. It shows how the war changed South Lebanon pass by pass (12-day passes; NISAR track 151 descending, frame 72; 17 passes acquired, 15 missed), which polarization (HH/HV) shows each change and the likely war-related drivers.
> A **Responder** view shows what that change may mean for people and services. Radar results are archive analysis per satellite pass, never live detection. The public app has no sign-in.

**Name:** ConflictPulse means the pulse of change in a conflict area, measured on every 12-day NISAR pass. It was renamed from RescueForce on 15 Nov 2026. Some older file names keep the old name, for example `docs/33_HOW_RESCUEFORCE_WORKS_AND_JUDGE_QA.md` and `docs/design/rescueforce-landing-mockup.html`.

---

## 1. Product in one minute

- **Landing page** (`/`): 3D Earth, a dive to the study area, and a "Watch the change, pass by pass" section with a small interactive chart (doc 34 §7).
- **Dashboard** (`/map`): a 3D, 2D and split map. The map, the Cesium effects and the backend are unchanged. A switch in the top bar picks between two equal modes (section 2).
- **No sign-in** (team decision, 15 Nov 2026, PR #47). The public app shows **labelled sample data**. Real released data needs a separate public-release step on the backend (doc 31).
- **Rules everywhere:**
  - Evidence labels **Observed / Reported / Corroborated / Unknown**.
  - Numbers are shown as ranges.
  - Damage and routes are candidates and not verified.
  - Never the word "safe".
  - No vehicle or phone tracking.
  - A missing input is Unknown, never 0.
  - Causes are always "likely", with alternatives.

## 2. The two modes

| | **Change over time** | **Responder** |
| --- | --- | --- |
| For | Scientists, students, journalists, planners | Emergency officers |
| Shows | The pass-by-pass chart, the HH / HV / HH−HV switch, likely drivers, a "what changed" sentence and the budget per pass | Incident ranking, insights, decision assistant, rebuild budget, building and shelter details, Sources |
| Question | "What changed, when, and why might that be?" | "What might this mean for people and services, and where should we check first?" |

The map, the incident pins and the date slider are the same in both modes. Only the right-hand panel changes.

## 3. Study area and passes

**South Lebanon, NISAR track 151 descending, frame 72.** The product is L2 GCOV with HH and HV (`data/manifests/nisar.json`).

- **Pre-war baseline:** 6 passes (27 Oct 2025 – 19 Jan 2026).
- **After:** 3 passes (24 Jun – 18 Jul 2026).
- **Later:** 8 passes (11 Aug – 3 Nov 2026).
- **17 passes acquired, 15 missed.** Missed passes are shown as gaps and never filled in. Most of the gap is from 31 Jan to 12 Jun 2026, during the war.
- **Data warnings:**
  - The 23 Aug 2026 HV pass is about 2 dB too bright and is marked **suspect**.
  - The before and after products come from different processing versions (BETA and PROVISIONAL). We normalise on stable areas before comparing them.

## 4. Real or sample?

| Part | Public app | Backend real-data mode (doc 31) |
| --- | --- | --- |
| Pass dates and missed passes | **Real** (manifest) | Real |
| Candidate cells per pass | Sample series | **Real** model results per pass (`model/slider/<date>/`) |
| HH / HV change vs baseline | Sample series | **Real** change rasters per pass, averaged per area |
| Budget per pass | Sample | Real formula on the real tables |
| Fires, power loss | Sample | **Real** FIRMS (every 30 min) and Black Marble (daily) |
| Population, buildings, facilities | Sample values | **Real** WorldPop, OSM, GHSL |
| Routes, shelters | Demo drawings only | Not built yet |

The sample series has the same shape as the backend route `GET /layers/{id}/timeseries`. If the backend later opens that route publicly at neighbourhood level (H3 r8, behind `PUBLIC_RELEASE_APPROVED`), the chart can show real numbers without any UI change.

## 5. How the time series works

Section 5 of doc 34 has the full plan.

1. **One point per pass date:** all 32 dates (17 acquired and 15 missed).
   - **Bars:** the number of damage-candidate cells in the selected area.
   - **Line:** the backscatter change from the pre-war baseline, in dB, for the chosen polarization.
2. **Gaps stay visible.** A missed pass is never joined to its neighbours or filled in. The suspect pass is drawn hollow with a note. A shaded band marks the war months that have no passes.
3. **Pass slider and Play** step through the acquired passes. A sentence describes each step, for example "Between 18 Jul and 11 Aug, candidate cells rose from 6 to 11; HH fell a further 0.9 dB."
4. **No new model training.** The series only reads outputs the model already made for each pass.

**How a cell becomes a candidate** (doc 33 §3):
- We compare change features per H3 cell (about 0.1 km²) between the pre-war and the later radar images.
- An Isolation Forest model, trained on quiet built-up cells, scores how unusual each cell's change is.
- The classes come from quantiles of the quiet-cell scores: possible (95th), moderate (99th) and severe (99.9th). They are anomaly classes, not proof of collapse.
- One radar gives **Observed**; agreement from Sentinel-1 gives **Corroborated**.

## 6. Polarizations and likely war drivers

- **HH** (horizontal send, horizontal receive) is strongest where walls meet the ground ("double bounce"). When a building collapses, those corners are lost and **HH drops**.
- **HV** (cross-polarized) comes from rough surfaces and vegetation. Rubble can make **HV rise**; burnt orchards and fields make **HV drop**.
- **HH−HV** helps tell "structure lost" (HH falls more) from "vegetation lost" (HV falls more).

The rules below give a likely driver for each pattern. Each driver is a hypothesis, with look-alikes we check against the pre-war passes and the next pass:

| Pattern | Likely driver | Look-alikes to rule out |
| --- | --- | --- |
| Sharp HH drop (≤ −2 dB) that persists | Building collapse | Demolition for construction, wet season |
| HV rise that persists | Rubble and debris | Construction sites, crop growth |
| HV drop near a fire detection | Fire scar | Harvest, seasonal leaf loss |
| HH and HV both up for one pass only | Not war-related: rain or soil moisture | — |
| Slow seasonal rise and fall in HV | Not war-related: vegetation season | — |

## 7. Budget per pass

- **Formula** (same as doc 33 §11): **cost range = affected floor area × damage share × cost per m²**.
- **Recalculated at every pass** using the damage seen up to that pass, and drawn as a range under the chart.
- **Damage share:** severe 100 %, moderate 50 %, possible 20 %.
- **Cost per m² (USD 2025):** housing 450–900, non-residential 600–1,200. These are anchored to the World Bank Syria assessment (Aug 2025) and adjusted for Lebanon.
- **Floor area:** footprints × a range of floors.
- **Label:** "Planning indication only", never a quote.

## 8. Responder view: what the change may mean

The Responder view puts the radar change in context with other open data (methods in doc 33 §§4–11):

- **Fires:** FIRMS points with a 375 m uncertainty ring.
- **Possible power loss:** night lights compared with each cell's own last 60 clear nights.
- **People:** WorldPop range.
- **Buildings and facilities:** OSM and GHSL.
- **Ranking and help:** a transparent ranking out of 100, insights, a rule-based decision assistant and the rebuild budget.

It suggests; a person decides.

---

## 9. Judge Q&A (short answers)

1. **What does the time series show?** For one area, it shows every 12-day NISAR pass from Oct 2025 to Nov 2026:
   - how many cells are damage candidates;
   - how far HH or HV has moved from the pre-war baseline;
   - the budget range at that pass.
   The 15 missed passes are left as gaps. A sentence and a likely driver explain each step.
2. **Which polarization shows what?** HH shows buildings, through double bounce; it drops when they collapse. HV shows rough surfaces and vegetation; rubble can raise it and burnt orchards lower it. HH−HV separates lost structure from lost vegetation.
3. **Why is it not live?** NISAR passes every 12 days, products arrive days later, and 15 of the 32 passes over our area are missing. So radar results are archive analysis per satellite pass, never live detection. Only fires (every 30 min) and night lights (daily) are near-real-time feeds. The public app uses labelled sample data.
4. **How is the budget per pass calculated?** Floor area × damage share × World Bank-anchored cost per m², shown as a range. It is recalculated with the damage seen up to each pass and labelled "planning indication only".
5. **How do you know the change is from the war and not seasons or rain?**
   - We compare with the six pre-war passes, which show the normal seasonal pattern.
   - We check that the change persists on the next pass.
   - We look for supporting signals: a FIRMS fire for burn scars, Sentinel-1 agreement for corroboration.
   Every cause is labelled "likely", with alternatives.
6. **Is the data real?** In the backend, yes: real NISAR, Sentinel-1, FIRMS, Black Marble, WorldPop, OSM and GHSL. The pass dates in the public app are real; the values are sample on purpose, because it is not an operational system.
7. **How do you know a building is damaged?** We don't claim to. A cell whose radar change is unusual compared with quiet areas becomes a candidate. A second radar can corroborate it, and a person must verify it.
8. **How do you detect power cuts at night?** Night lights are measured only at night, around 1:30 am. Each cell is compared with its own last 60 clear nights. Below 50 % on 2 clear nights means possible power loss. High confidence needs both satellites to agree, and in the daytime the map shows the latest night's result.
9. **Why radar?** It sees through cloud and smoke, day and night. L-band HH and HV separate structures from vegetation.
10. **How accurate is it?** For night lights, 0.73 % of cell-nights are flagged when both satellites agree, against 2.7 % for one satellite alone. Radar classes are anomaly quantiles (95 / 99 / 99.9 %), and field validation is still needed. We show ranges and Unknown instead of false precision.
11. **How do you prioritise (Responder view)?** Seven weighted parts: people 30, facilities 20, damage 15, fire 15, services 10, time 5 and access 5. Missing data widens the range instead of counting as zero, and every rank shows its reasons.
12. **How do you find routes and shelters?** This is planned and works offline. OSM roads are routed locally, and roads near damage candidates are flagged "possibly blocked". Shelters are OSM schools, halls and places of worship, with capacity from floor area at 3.5 m² per person. In the demo, both are sample drawings, always "not verified".
13. **Is it AI?** The damage model is machine learning (Isolation Forest). The drivers, ranking, insights, assistant and budget are transparent rules and formulas, not a chatbot, so every output can be traced.
14. **Privacy and safety?** No tracking of people or vehicles and no sign-in. No location is sent to external routing services, and alerts are stored per neighbourhood. Real places are not labelled as shelters publicly, and nothing is called "safe".
15. **What is the population number?** It comes from WorldPop 2020, which has two models; we show the smaller and the larger as a range. It is a pre-war figure, so it does not include displacement.
16. **Costs and keys?** All data is free and open. The only keys are a free Earthdata login and a free Cesium ion token. No paid APIs.
17. **What would you build next?**
    - Automatic processing of each new NISAR pass.
    - Coherence change once short-gap pairs exist.
    - L-band and S-band together.
    - The same view for floods, landslides and earthquakes.
    - Local road routing and real shelter capacities.
    - Field reports and ground validation feeding back into the evidence labels.

## 10. Where to look

| Topic | Doc or files |
| --- | --- |
| Time-series plan, drivers, files | `docs/34_CHANGE_OVER_TIME_VIEW.md` |
| Data sources, methods, repo paths | `docs/33_HOW_RESCUEFORCE_WORKS_AND_JUDGE_QA.md` |
| Backend real-data mode | `docs/31_BACKEND_REAL_DATA.md` |
| UI and frontend | `docs/26_3D_MAP_UI_AND_FRONTEND.md`, `frontend/README.md` |
