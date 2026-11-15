# Real-data test of the new inputs (15 November 2026)

Scope: only what is new today. Udula's radar, height and agent checks are in `UDULA_PROGRESS.md` sections 7 and 7b and were not repeated. All inputs below were rebuilt by Thanoban from public downloads (HOTOSM, GHS-OBAT, WorldPop, OCHA, Overpass) and loaded into the team's Supabase database.

## 1. Rebuilt inputs compared with Udula's numbers

| Input | Today | Udula | Same? |
|---|---|---|---|
| OSM buildings in the demo box | 268,536 | 268,536 | Yes |
| Facilities found / inside Lebanon | 543 / 383 | 543 / 383 | Yes |
| H3 r9 grid and population cells | 52,053 | not stated | n/a |
| Incidents | 179 | 131 | Differs, explained below |
| Recommendations | 537 | 393 | Differs (3 per incident) |
| Budgets / insights | 131 / 6 | 131 / 6 | Yes |

**Why 179 incidents, not 131:** the incident kinds are 129 damage-candidate areas, 1 fire and **49 possible power loss**. Udula's run had no night-light history on his machine, so it had no power-loss incidents. Today's run used the night-light history (`data/local/bm_history.csv.gz`), which adds the 49. The damage and budget parts are the same.

## 2. Night lights and fires on real data

| Model | Result |
|---|---|
| Possible power loss (Black Marble rule) | 49 events in 49 cells; 1 with both satellites agreeing (Corroborated), 48 from one satellite (labelled low confidence) |
| FIRMS fire feed (live, 15 Nov) | 3 detections in the demo box over 7 days, latest 14 Nov; 1 fire event |

The power-loss count is high relative to the corroborated count: 48 of 49 rest on one satellite only. These are shown as "one satellite, low confidence", never as confirmed outages.

## 3. Supabase database compared with the files

| Table | Rows | Matches files |
|---|---|---|
| areas / radar_area_results / metric_values | 13,669 / 52,786 / 41,508 | Yes (radar export) |
| alerts | 50 (49 power loss, 1 fire) | Yes |
| facilities | 383 | Yes |
| agent_incidents / recommendations / insights / budgets | 179 / 537 / 6 / 131 | Yes (`data/published`) |
| agent_buildings | 268,536 | Yes |

Safety: all 24 tables have Row Level Security on and the Supabase public roles (anon, authenticated) have no grants, so the data is reached only through our API.

## 4. Other checks

- Test suites `worker/`, `pipelines/`, `tests/`: **223 passed**.
- Published agent output (2,210 files): no low > high range, no use of the word "safe". Resident numbers appear only inside the budget file (used for cost, never served per building).
- Evidence labels in the published files include lowercase internal codes (`observed`, `none`, `unknown`) in the raw damage file; the API and screens must show only Observed / Reported / Corroborated / Unknown.

## 5. Limits

- One live fire in 7 days is a thin sample for the fire model.
- The night-light rule has no ground truth for Lebanon; most events rest on one satellite.
- No independent damage assessment exists for Lebanon, so radar results stay candidates.
