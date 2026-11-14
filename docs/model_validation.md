# NISAR damage model: validation results (M1-03)

Owner: Udula (M1). Run date: 14 November 2026. Numbers come from `data/manifests/model_tests.json`; the hand-off record is `data/manifests/radar_run.json`.

**What the model shows:** candidate radar change in dense built-up areas of south Lebanon. **What it does not show:** confirmed damage, accuracy, or totals. No damage labels exist for this area and period, so there is no precision or recall.

## 1. Data and method

| Item | Value |
|---|---|
| Radar | NISAR L2 GCOV, track 151 descending, frame 72, 20 m, HH and HV |
| Before | 6 BETA passes, 27 Oct 2025 → 19 Jan 2026 |
| After | 3 PROVISIONAL passes, 24 Jun → 18 Jul 2026 |
| Time slider | 8 later passes, 11 Aug → 3 Nov 2026, each compared with the June–July baseline |
| Area units | H3 resolution 9 cells (about 0.1 km²); results published at resolution 8 |
| Assessed cells | Cells at least 25% covered by OSM buildings plus 30 m (5,783 of 11,362 built-up cells) |
| Masks | Water (mean HV), terrain (NASADEM: layover, shadow, slope > 25°), GCOV validity mask |
| Model | Isolation Forest (scikit-learn), with robust Mahalanobis distance as a cross-check |
| Training areas | Cells with no UCDP event (exact location) within 2 km, 19 Jan – 24 Jun 2026 |
| Classes | Quantiles of training scores: above 95% possible, above 99% moderate, above 99.9% destroyed or severe; HH must fall (collapse direction), otherwise "other change" |

## 2. Checks on the input data

| Check | Result | Action |
|---|---|---|
| Same grid on all 17 dates | Yes | None needed |
| HH, BETA vs PROVISIONAL | Mean differs by 0.15 dB on built-up pixels (within-version spread about 0.85 dB) | Comparable |
| HV, BETA vs PROVISIONAL | PROVISIONAL about 1.2–1.5 dB brighter everywhere | Removed by centring (robust scaling) |
| Stripes in the change image | Up to 3.3 dB smooth column trend (known BETA banding) | Removed by destriping, estimated on all valid land pixels |
| Water | Clear split in mean HV (water about −23 dB, land about −15 dB) | Masked below −20.5 dB, plus 40 m |
| 23 Aug 2026 pass | HV about 2 dB brighter, with large bands | Flagged in the change index |
| Terrain (NASADEM) | Slopes over 25°: 5.2% of the area; layover 0.05%; shadow none | Masked as Unknown (5.8% of the area) |

## 3. Results

**Hold-out quiet cells** (spatial blocks never used for training, 345 cells):

| Level | Design rate | Observed |
|---|---|---|
| Possible | 5% | 8.7% |
| Moderate | 1% | 1.2% |
| Destroyed or severe | 0.1% | 1.2% |

The top level is unreliable: 1,301 training cells cannot estimate a 0.1% tail. That class is therefore shown with medium confidence, not high.

**Top-20 eye check** (radar image chips of the 20 highest-scoring cells):

| Round | Plausible damage | False | Main false causes |
|---|---|---|---|
| All built-up densities | 4 | 16 | Terrain edges, farm fields, coastline |
| Building density ≥ 25% | 15 | 5 | Terrain edges, noise |
| + terrain mask (final) | 15 (3 unclear) | 2 | Terrain edge, texture boundary |

**Strike context** (UCDP events; association only, not ground truth; for Thanoban's M1-04 to formalise):

| Measure | Value |
|---|---|
| Candidate rate, cells within 1 km of an event | 3.2% |
| Candidate rate, cells 5 km or more away | 4.3% |
| Top 20 cells within 1 km of an event | 50% (vs 37% of all assessed cells) |

Overall there is **no clear link** between candidates and recorded events. Only the highest-scoring cells lean towards events. Possible reasons: single-building strikes are below the cell size; much destruction may predate the BETA "before" images; backscatter alone is a weak signal.

**Time slider** (each pass vs the June–July baseline): 136–181 candidates per pass; hold-out moderate false alarms 0.1–0.5%. The 22 Oct and 3 Nov passes are V1 products compared with a PROVISIONAL baseline.

## 4. What may and may not be claimed

| Allowed | Not allowed |
|---|---|
| "Candidate change in dense built-up areas" | Confirmed damage or collapse |
| A known false-alarm rate on quiet hold-out areas | Precision, recall or accuracy |
| Change over time between passes | Destroyed vs severe as separate classes |
| | Totals (radar misses damage, so counts are minimums) |

## 5. Data sources and licences

- NISAR L2 GCOV: NASA/ISRO, via ASF DAAC (open).
- OSM buildings: HOTOSM export on HDX, ODbL.
- NASADEM elevation: NASA/JPL via LP DAAC (open).
- UCDP Candidate GED 2026 (Jan–Sep): Uppsala Conflict Data Program, CC BY 4.0.
- ACLED is **not** used: its terms forbid using ACLED data to train or test models.
- Insecurity Insight is **not** used for locations: its coordinates are censored.

## 6. Coherence: tested and excluded

Computed with `pipelines/radar/nisar/coherence.py` on the 20 m grid (both source grids nest exactly; nothing resampled).

| Layer | Source | Looks | Built-up median | Water median |
|---|---|---|---|---|
| Across the escalation | GSLC 19 Jan (BETA) × 24 Jun 2026 (PROVISIONAL) | 72 | 0.167 | 0.118 |
| Before (12 days) | GUNW 7 → 19 Jan 2026 | product, 3 × 3 mean | 0.706 | 0.239 |

The zero-coherence floor for 72 looks is about 0.10. Across the 156-day gap, coherence is close to that floor everywhere, including quiet built-up areas: only 12% of built-up pixels exceed 0.3. It is the same near recorded events (0.169), 1–5 km away (0.167) and 5 km or more away (0.167). The cells with the largest coherence drop are *less* often near events (26% within 1 km, vs 37% for all cells).

**Decision:** cross-gap coherence carries no usable damage signal here (long gap, season and product-version change), so it is **excluded from the model**, as the plan's T-COHERENCE rule requires. The 12-day January coherence is good (median 0.71 on built-up areas), so short-gap coherence remains useful for later work when passes on both sides of an event are 12 days apart.

## 7. Open items

- UCDP events stop at 15 Sep 2026, so later slider passes have incomplete quiet-area selection.
