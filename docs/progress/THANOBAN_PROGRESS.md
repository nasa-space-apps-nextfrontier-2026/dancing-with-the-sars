# Thanoban: ongoing work log (M1-04)

Read this to see where Thanoban's ML work stands. Udula: this is what you need to know about how it is done and what it hands to you. Plan: [18](../18_THANOBAN_ML_PLAN_AND_COLAB.md). Task: [Thanoban tasks](../tasks/MEMBER_2_THANOBAN_SMALL_DATA_ML.md). Last updated 14 November 2026.

## Status

| Item | State |
|---|---|
| Colab set-up (CLI in WSL2, signed in, free account) | Done and tested |
| Black Marble granule search (CMR) for the demo box | Done, ran on Colab, 4 unit tests pass |
| Black Marble download and cropping | Next (needs an Earthdata Login token as a Colab secret) |
| Model A: night-light power-loss | Not started (starts after downloads) |
| Model B: fire events (FIRMS) | Not started (needs the FIRMS map key) |
| Model C: strike-enrichment tests | Not started (harness first on mock data) |

Code is on branch `feature/m1-04-nightlight-discovery` (commit `f56ecff`), in `worker/services/` (`cmr.py`, `discover_nightlights.py`) with tests in `worker/tests/test_services.py`. It is not merged into `dev` yet; it needs a PR approved by Udula, then merged by Rashiru.

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

1. Add a start date to the CMR search and list the last 120 nights for both satellites.
2. Download the cropped tile for one night on Colab with an Earthdata token and check the radiance and quality flags.
3. Build the per-cell baseline table (60 clear nights), with `Unknown` when there are too few clear nights.
4. Fire events from FIRMS: filter, remove permanent hot spots, cluster within 1 km and 12 h.
5. Strike-test harness on mock data, ready for Udula's table.
6. Open a PR into `dev` for each of these (one task per branch).
