# Thanoban: reply to Udula's update of 14 November 2026

Udula, I read your progress log and checked the branches on GitHub. Short answer: **the work is done correctly and I agree with your proposals**, with the conditions below. Rashiru and Chames should confirm the two decisions that touch their work (1 and 5).

## 1. What I checked

| Check | Result |
|---|---|
| Branches U-01 to U-07, backend, contract and publish step are all pushed | Yes |
| Only small manifests and key names are in Git (no parquet, csv, zip, h5 or tiles) | Yes. Keep it that way: the 268,536 buildings, the 2,201 building files and the damage tables stay out of Git |
| PR #24 (contract) | Open, CI green |
| 3D-GloBFP not used (authors at Chinese institutions) | Correct, it follows our "no Chinese data" rule |
| Heights: 57% within one storey, range holds the true height for 83% | Honest result. See decision 2 |
| Budget US$0.4-4.3 billion, 0.5-14 years, "Planning indication only" | Fine as an indicative range. Keep the assumptions visible |
| No residents per building in the API, unknown cells in grey, heights from about 2018 | Correct, keep these three safety points on screen |

## 2. Decisions

1. **One data store: PostGIS. Agreed.** Conditions:
   - It must run with **no paid service**: Docker Compose on the demo machine, or a free host. Please write which one in the backend guide.
   - Keep #21's public-map approval gate (`PUBLIC_RELEASE_APPROVED`), the 72-hour hold, the `*` scope check and the night-light step. The worker's publish output is loaded into PostGIS.
   - Chames holds #22 and #23, and #18 and #19 until your backend PR is merged. After that Chames rebases or closes them, whichever is smaller. (Rashiru and Chames: please confirm.)
2. **Height target (57% instead of 70%): accepted.** Show the wider range and the label "Height estimated from satellite data (range); towers may be much taller." The range holds the true height for 83% of checked buildings, which is what the screen reports.
3. **People unknown:** fix at H2 if the population file is late. Until then people stay "unavailable".
4. **Fire alerts:** keep `FIRE_RELEASE_DELAY_HOURS=0` for signed-in roles (FIRMS is public and live). Fire alerts must still never appear on the public map unless `PUBLIC_RELEASE_APPROVED` is set.
5. **Rebuild scope:** adopted (doc 24). Rashiru or the plan owner updates the "No rebuilding" row in `PROJECT_PLAN.md` and the planning manifest hash. Label stays "Planning indication only".

## 3. What I (Thanoban) do

- **Night-light history:** the file is `data/local/bm_history.csv.gz` (about 10 MB, Black Marble per-cell history). It is **not for Git**; I will send it to you by the team drive. Put it at the path in `NIGHTLIGHT_HISTORY`. Then `python -m worker.main --publish --history <file> [--damage <table>] [--fires]` writes the possible-power-loss alerts.
- **GitHub Support:** I will ask for the Contributors list to be refreshed (the old co-author line came from a commit already removed from main).
- Fire and night-light additions for the 3D scene (confidence, FRP, time, satellite; lit or dark per cell) come after this, from my side.

## 4. What you do next

Order of work:

1. **Small PR: `.gitignore`.** I checked `dev`: it still has merge-conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`). Fix them and open a tiny PR.
2. **Worker entry point.** `worker/main.py` is changed both by the merged ML wiring (`--publish`, `--damage`, `--history`, `--fires`) and by your `feature/u-06-publish-agents` (`--agents`, `--table`). When you merge, **keep both sets of flags** and add one test for each mode.
3. **Open the PRs into `dev`**, in this order, one at a time so CI stays readable: U-07 keys, U-01 to U-04 (building data), U-05 agents, U-06 publish step.
4. **Backend PR** after decision 1 is confirmed by Rashiru and Chames.
5. **U-06 endpoints** (`/incidents`, `/incidents/{id}`, `/areas/{id}/budget`, `/buildings`) after PR #24 is merged.
6. **Budget check** against the World Bank Lebanon assessment (2025). You may download it, but keep the PDF out of Git.
7. **WorldPop source record** into `sources.json` (together with K-04, population).

## 4a. Still waiting on others (not on you)

| Needs | From |
|---|---|
| Population per H3 r9 cell (K-04, PR #28) | Kisara |
| Facilities (K-03, PR #27) | Kisara |
| Review of contract PR #24 | Rashiru |
| Frontend switch to `DEMO_SYNTHETIC=false` | Rashiru |
| Roads and shelters (M2-04, M2-05) | not started |

## 5. Notes for the next step (not tasks yet)

The map screen is moving to a 3D view with shelters, power loss, roads and an impact summary per incident. When the plan is agreed, the building table, the incident record and the budget will need to expose those fields. Please keep the incident record easy to extend. Do not build anything for this until it is written as a task.
