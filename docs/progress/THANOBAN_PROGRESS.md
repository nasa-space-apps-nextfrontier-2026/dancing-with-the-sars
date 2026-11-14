# Thanoban: ongoing work log (M1-04)

Read this to see where Thanoban's ML work stands. Udula: this is what you need to know about how it is done and what it hands to you. Plan: [18](../18_THANOBAN_ML_PLAN_AND_COLAB.md). Task: [Thanoban tasks](../tasks/MEMBER_2_THANOBAN_SMALL_DATA_ML.md). Last updated 14 November 2026.

## Status

| Item | State | PR |
|---|---|---|
| Colab set-up (CLI in WSL2, signed in, free account) | Done and tested | |
| Black Marble granule search (CMR) with 120-day default | Merged into `dev` | [#3](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/3), [#7](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/7) |
| Model A: night-light power-loss rule | Merged | [#4](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/4) |
| Black Marble history builder (Colab) and real-data evaluation | Merged; real run done (see below) | [#9](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/9) |
| Model A as a callable function (two-satellite agreement, alert events) | Done, 5 tests, runs on real data; open, needs review | [#10](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/10) |
| Model B: fire events (filter, permanent hot spots, 1 km / 12 h clustering) | Code and 6 tests on synthetic points; open, needs review | [#5](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/5) |
| Model C: strike-enrichment tests (near vs far, same-district control) | Harness and 4 tests on mock data; open, needs review. Event source will be UCDP, not ACLED | [#6](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/6) |
| FIRMS download | Blocked: needs the FIRMS map key | |
| Strike tests on real data | Waiting for Udula's damage table (first version by H16) | |

**Udula: please review PRs #10, #5 and #6** (you are the assigned reviewer); Rashiru merges after your approval. #3, #4, #7 and #9 are already merged. Thresholds are still the plan's starting values.

## How the work runs

- The code lives in the repo as normal Python modules, written with the standard library so they run the same on a laptop and on Colab.
- Training and downloads run on **free Google Colab** from a terminal (Colab CLI in WSL2 Ubuntu), not on Thanoban's laptop, which has little disk space. Commands and gotchas are in doc 18.
- Large files never go in Git. Colab downloads a tile, crops it to the demo box (35.0–36.0 E, 33.0–33.6 N), keeps only a small table, and deletes the tile.
- Only small result files come back to the laptop and into Git.

## What we found on 14 November 2026

Black Marble daily night-light products for the demo box, checked with NASA's CMR search from Colab:

| Product | Satellite | Granules found | Oldest to newest |
|---|---|---|---|
| VJ146A2_NRT (near real time) | NOAA-20 | 7 | 6 Nov to 12 Nov 2026 |
| VJ246A2_NRT (near real time) | NOAA-21 | 7 | 6 Nov to 12 Nov 2026 |
| VJ146A2 (archive) | NOAA-20 | 2,000 (search limit hit) | newest 28 Oct 2026 |
| VJ246A2 (archive) | NOAA-21 | 1,354 | 10 Feb 2023 to 4 Nov 2026 |

What this means:
1. **The near-real-time product only keeps about 7 days.** The 60-clear-night baseline must come from the archive.
2. **The archive lags by 1 to 2 weeks.** It ends on 28 Oct (NOAA-20) and 4 Nov (NOAA-21), and near real time starts on 6 Nov. So NOAA-20 has a gap of about a week (29 Oct to 5 Nov) between the two. The baseline must be built so that gap does not break it, and the model must say `Unknown` if too few clear nights are available.
3. One tile covers the whole demo box (`h21v05`), so each night is one file.
4. The CMR search page limit cut the NOAA-20 archive at 2,000 results. For the model we only need the last few months, so the next step is to search with a start date.

## First real data test (14 November 2026, Colab, Earthdata token)

Downloaded one night's Black Marble tile on Colab, cropped it to the demo box, then deleted the tile.

| Check | Result |
|---|---|
| Archive product `VJ146A2` (NOAA-20), night of 28 Oct 2026, tile `h21v05` | Downloads with the Earthdata token. The tile is only **20.5 MB**, so 60 nights is about 1.2 GB, which is fine on Colab |
| Tile coverage | 30–40 E, 30–40 N, 2400 x 2400 pixels (about 450 m); one tile covers the whole demo box |
| Demo box crop | 144 rows x 240 columns = 34,560 pixels |
| Layers present | `DNB_BRDF-Corrected_NTL`, `Gap_Filled_DNB_BRDF-Corrected_NTL`, `Mandatory_Quality_Flag`, `QF_Cloud_Mask`, `Snow_Flag`, `DNB_Lunar_Irradiance`, `Latest_High_Quality_Retrieval` |
| That night, valid pixels | 98%; median radiance 0.46, 95th percentile 9.4 |
| Quality flag | 91.5% good (0), 6.5% poor (1), 2.0% no retrieval (255) |
| Cloud bits (bits 6–7 of `QF_Cloud_Mask`) | 98.3% confident clear |
| Snow | none |

What this means for the model:
1. **The demo box includes sea**, so many pixels are dark. Per-pixel ratios on dark pixels are unstable. The rule must work on **cell totals over land pixels** (H3 cells with a minimum baseline), and the `MIN_BASELINE_RADIANCE` value in PR #4 has to be applied per cell, not per pixel. I will tune this on real history.
2. "Clear night" will be defined as quality flag 0 and cloud bits 6–7 equal to 0, as in the Black Marble guide. To be checked against the product guide before tuning.
3. **Near-real-time files (last 7 days) now work.** They were blocked until the Earthdata account authorised the application **"LANCE"** (Earthdata profile > Applications > Approve More Applications, then the auto-authorise list). After that the NRT URL on `nrt3.modaps.eosdis.nasa.gov` returns HTTP 200 with the token. The archive needs the "LAADS DAAC Cumulus" app, which was already authorised. **Udula:** NISAR downloads from ASF need the application "Alaska Satellite Facility Data Access" authorised on your own Earthdata account the same way.

## Real-data run of the night-light rule (14 November 2026)

Built the per-cell history on Colab (230 nightly tiles, NOAA-20 and NOAA-21, last 120 days, archive plus near real time; 228 downloaded, 2 failed because the 6 Nov near-real-time files return 404). 1.72 million rows over 7,546 H3 res-8 cells. Then ran the rule from PR #4 on it. Code: PR [#9](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/9) (stacked on #4).

| Result | NOAA-20 | NOAA-21 |
|---|---|---|
| Hold-out (45 nights): share of assessable cell-nights flagged | 2.6% | 3.3% |
| Latest night (12 Nov): flagged / assessable | 21 / 2,042 (1.0%) | 29 / 3,416 (0.85%) |
| Latest night: cells `unknown` (dark sea or land, or too few clear nights) | 5,504 | 4,130 |

- The false-alarm rate (2.6–3.3%) is **above the 1% target**. The hold-out also contains real events and counts a lasting drop several times, so it is an upper bound.
- **Requiring both satellites to agree works.** Measured over the 45-night hold-out on 59,868 cell-dates that both satellites could assess: a single satellite flags 2.7% of them, but both flag the same cell on the same date in only **0.73%** (438), under the 1% target. Proposed rule: both agree = "possible power loss"; a single-satellite flag stays low confidence. Code in PR #9.
- About 70% of cells are `unknown`, mostly sea and dark land where a ratio is meaningless. That is correct behaviour, but the map should show them as "no signal", not as working.

## What Thanoban hands over, and when

| To | What | When |
|---|---|---|
| Rashiru | Callable functions: night-light power-loss, fire events, returning events with area, time, source, label, confidence (or `Unknown` with a reason) | H12 |
| Rashiru | Strike-test results and limits text for the Sources page | H32 |
| Udula | Nothing needed to start. Only the strike tests need your damage table | |

## What Thanoban needs from Udula

1. **The damage table** (one row per H3 res-9 cell: class, score, confidence, top features, dates, `model_id`). A first version by H16 is enough; until then the tests run on mock data.
2. **The exact column names** so the tests can read it. Please confirm them at the H2 contract freeze.
3. A reviewer for the M1-04 PRs (you are the assigned reviewer).

## Open issues

| Issue | Who |
|---|---|
| `.gitignore` on `dev` ignores the whole `data/` folder, but docs say small manifests in `data/manifests/` are committed. The Black Marble summary file could not be committed because of this. Suggest ignoring `data/*` and allowing `!data/manifests/` | Rashiru |
| Earthdata Login token and FIRMS map key must be stored as Colab Secrets (never in code or Git) | Thanoban |
| `worker/tests/test_worker.py` has 3 existing lint warnings (Ruff) unrelated to this work | Rashiru |
| One Colab session (ID starting `m-s-usc1a4`) already existed in the Google account before this work; it is not ours and was left alone | Thanoban |

## Next steps (in order)

1. Get the FIRMS map key (it is emailed to the account owner).
2. Download the last 60 clear nights as cropped tiles on Colab and build the per-cell history.
3. Hand the callable night-light function (PR #10) to Rashiru for the alert plumbing; later check which flagged cells line up with UCDP events and the radar damage.
4. Download recent FIRMS points for the demo box, run the fire model from PR #5, and tune the permanent-spot rule.
5. Run the strike tests from PR #6 on Udula's damage table when the first version arrives (by H16); confirm column names at H2.
6. Hand callable functions to Rashiru (H12) and the test numbers for the Sources page (H32).
