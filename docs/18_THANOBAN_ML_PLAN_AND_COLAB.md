# Thanoban's ML plan and how to train on Google Colab

[Blueprint index](README.md) · [Team assignment](17_TEAM_ASSIGNMENT_AND_BRANCHES.md) · task file: [Thanoban tasks](tasks/MEMBER_2_THANOBAN_SMALL_DATA_ML.md)

Written 14 November 2026. Scope: **M1-04** (night-light power-loss model, fire event model, strike-enrichment tests) and **M2-06** (movement design). Thanoban does not work on the backend or on large radar downloads (Udula does those).

## 1. What the three models are, and how heavy they are

All three are small models on small tables. **None needs a GPU or deep learning.** They run in seconds to minutes on a normal CPU, so the free Colab CPU runtime is enough; the real problem on a laptop is disk space and memory for downloading and holding the raw files, not training time.

| Model | Input | Method | Output | Weight |
|---|---|---|---|---|
| **A. Night-light power-loss** | Black Marble VJ146A2 (NOAA-20) and VJ246A2 (NOAA-21), archive + NRT, cropped to the demo box | Per-cell baseline from the last 60 clear nights; flag a drop when radiance is below 50% of baseline on 2 clear nights; anomaly score with confidence. Optional: Isolation Forest on cell features (baseline, recent mean, moon and angle quality flags) as a check | Per cell and day: `possible_power_loss`, score, confidence, clear-night count, `Unknown` if too few clear nights | Light: a few cells × a few hundred nights |
| **B. Fire events** | FIRMS VIIRS 375 m points (NOAA-20, NOAA-21), south Lebanon | Drop low-confidence points and permanent hot spots (same spot burning on many days over the baseline); cluster points within 1 km and 12 h (DBSCAN or simple distance grouping) | "Fire detected" events: time, place, satellite, confidence. Never a cause | Very light: thousands of points |
| **C. Strike-enrichment and evidence tests** | Udula's damage table (one row per H3 res-9 cell), ACLED and Insecurity Insight event points | Flagged share near events (within 2 km) vs far, same-district control, false-alarm rate on quiet cells by class, top-20 cell list | Test table for the Sources page, with limits written down | Very light |

Rules: show ranges and "Unknown", never a single exact claim; "Possible power loss", not "blackout"; evidence labels follow [PROJECT_PLAN.md](PROJECT_PLAN.md) section 9.

## 2. Where to run it: free options compared

| Option | What it is | Good for | Limits and caveats |
|---|---|---|---|
| **Google Colab (browser notebook), main choice** | Free hosted Jupyter notebook with a CPU runtime; GPU (usually a T4) sometimes available | Everything here: runs on any laptop, no install on Windows | Google does not publish fixed free-tier limits. Secondary sources commonly cite sessions of up to about 12 hours and an idle timeout of about 90 minutes, and GPUs can be unavailable at busy times. The VM disk is **temporary** and wiped when the session ends. Check Colab's own FAQ before relying on any number |
| **Colab CLI (optional)** | Google's official command-line tool for Colab, announced June 2026 (`googlecolab/google-colab-cli`). Commands include `colab new`, `colab exec`, `colab run`, `colab upload`, `colab download`, `colab usage`, `colab stop` | Running a script from the repo on a Colab VM from the terminal, without opening the browser | **Linux and macOS only; Windows is not supported** (use WSL2, which is not confirmed in its docs). Free-tier access is not stated clearly in its docs; run `colab usage` to see what your account gets. The README and the auth design doc disagree on the default login mode, so check `colab --help`. Treat the details as unverified until you try it |
| **Kaggle Notebooks (backup)** | Another free hosted notebook service | If Colab won't connect or runs out of quota | Reported at about 30 GPU hours a week, 12-hour sessions and about 20 GB of working disk by secondary sources (unverified); internet access in notebooks must be confirmed before relying on it |
| **Local laptop** | Normal Python | Fine for models B and C and for small crops of A, once data is cropped | Not enough disk or memory for raw Black Marble tiles, which is why we use Colab |

**Is there something better?** For these small CPU models, no: Colab (browser) is the simplest free option and needs nothing installed. The CLI is only useful if you want to script runs or let a coding agent drive them, and it needs WSL2 on Windows. A paid Colab plan is not needed. Do not build a deep-learning model just to use a GPU: it would be harder to explain and prove, and the anomaly approach is already the team's chosen method (ARCHITECTURE.md Part 1.2).

## 3. How to work (step by step)

### One-time setup (H0–H2)
1. Open Google Colab with a Google account. Create a Drive folder `civisar-ml/` for checkpoints and results.
2. Make a free Earthdata Login account and a token (for Black Marble through `earthaccess`). Get the free FIRMS map key.
3. Store them as **Colab Secrets** (the key icon in the notebook), never inside notebook cells, never in Git. Use a different notebook copy for sharing without secrets.
4. In the notebook, mount Drive, then `pip install earthaccess h3 scikit-learn pandas pyarrow geopandas rasterio`. Pin the versions in `requirements-ml.txt` in the repo.

### Keep the code in the repo, the notebook thin
- Write the real code as Python modules in `pipelines/services/` and `pipelines/evaluation/` (the folders Thanoban owns in doc 17). The notebook only installs packages, loads secrets, calls the module and saves outputs. That way the same code runs in Colab, on a laptop or through the CLI.
- Colab gets the code by cloning the repo (use a read-only token as a Colab Secret if the repo is private) or by uploading a zip. Edit and commit on your own branch, then pull again in Colab.

### The data flow (no storage problem)
1. **Stream, crop, delete.** In Colab, download a Black Marble tile, crop it to the demo box at once, append the small cell values to a table, then delete the tile. Keep only the small table (cell, date, radiance, quality flags) on Drive.
2. Save a **checkpoint to Drive after every step** (for example every 20 nights downloaded) so a disconnect does not lose progress. Make each step safe to re-run.
3. Copy results back to the laptop (download from Drive) and commit only the small files: `data/manifests/services_models.json` and small result tables. Large intermediate files stay on Drive.
4. Write a short `manifest` for each run: dataset names and versions, dates covered, parameters, run ID, and the git commit of the code.

### Optional: using the Colab CLI
Only on Linux, macOS or WSL2 (not native Windows). Commands as described by Google's repo, to be confirmed on first use:

```text
uv tool install google-colab-cli
colab new -s services                 # start a CPU session
colab upload requirements-ml.txt /content/requirements-ml.txt
colab exec -s services -f pipelines/services/run_nightlights.py
colab download /content/out/nightlights.parquet ./out/nightlights.parquet
colab stop -s services                # release the VM
```

## 4. Work plan and hours (about 22 h)

| Hours | Work | Done when |
|---|---|---|
| H0–H2 | Colab setup, secrets, Drive folder, small test downloads; agree the alert-event and test-result schemas at H2 | A notebook downloads one Black Marble tile and one FIRMS day and saves a cropped table |
| H2–H8 | **Model A:** download the baseline nights, crop, build the per-cell 60-clear-night baseline; clear-night logic from quality flags | Baseline table for all cells; known-drop test passes on synthetic data |
| H8–H12 | **Model B:** FIRMS filtering, permanent hot-spot removal, clustering. **Hand over callable functions to Rashiru at H12** | Fire events on a test week; permanent hot spot removed |
| H8–H16 | **Model C harness** on mock damage table and mock event points | Harness runs end to end on mock data |
| H12–H20 | Model A scoring and confidence; Isolation Forest cross-check (optional); daily run function for the live job | Daily run returns events or `Unknown` with reasons |
| H16–H24 | Run model C on Udula's real damage table (first version arrives at H16) | Test table with near-vs-far and false-alarm numbers |
| H24–H32 | Final runs, test numbers for the Sources page, limits text; review Udula's tests | Sources page numbers delivered; checker passes |
| H38–H48 | Demo story, video, submission page | Video recorded; submission filled in |

M2-06 movement design (max 1 h) fits anywhere before H38.

## 5. Tests and what counts as done

| Check | Pass if |
|---|---|
| Night lights, synthetic series with a known drop | Drop found; flat series not flagged; fewer than the minimum clear nights gives `Unknown` |
| Night lights, hold-out nights | About 1% false flags at the chosen threshold |
| Fires, permanent hot spot | Removed; a new fire next to it is kept |
| Fires, no cause | No event text states a cause |
| Strike tests | Flagged share near events is compared with far events and with the same district; numbers and limits written down |
| Reproducibility | Same inputs and parameters give the same outputs; run manifest saved |
| Safety | Outputs carry label, source, date; no live vehicle or phone data used |

## 6. Risks

| Risk | Plan |
|---|---|
| Colab disconnects or has no free runtime | Checkpoints on Drive; code in the repo so the run restarts at the last step; Kaggle as backup |
| Black Marble NRT has no January history | Join the archive product with NRT, as the data plan says; test for duplicates |
| Too few clear nights in winter | Output `Unknown`, never a guess |
| Udula's damage table is late | Finish the harness on mock data, report real numbers as soon as the table arrives |
| Colab CLI doesn't work on Windows | Use the browser notebooks; the CLI is optional |

## Sources

- Google Developers Blog, [Introducing the Google Colab CLI](https://developers.googleblog.com/introducing-the-google-colab-cli/) and the repo [googlecolab/google-colab-cli](https://github.com/googlecolab/google-colab-cli)
- [Colab free-tier limits, secondary guide](https://www.hivenet.com/post/google-colaboratory-gpu-complete-guide-to-free-cloud-gpu-access-and-limitations) (not Google's own numbers)
- [Free cloud GPUs in 2026](https://gpuperhour.com/blog/free-cloud-gpus-and-credits) (Kaggle limits, secondary)
