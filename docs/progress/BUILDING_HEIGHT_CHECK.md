# Building height check (U-03)

14 November 2026, Udula. Task: [doc 25](../25_NEW_PLAN_TASKS.md) U-03. Numbers: `data/manifests/buildings_height_calibration.json` (rebuild: `python -m pipelines.buildings.height_check`).

## Result

**The 70% "within one storey" target is not met: 57% overall. Ranges are widened instead (doc 25 fallback): the range holds the known height for 83% of buildings.**

| Known height | Buildings | Within one storey (3 m) | Range holds the height | Range width |
|---|---|---|---|---|
| 1-2 storeys | 198 | 77% | 90% | 10 m |
| 3-4 storeys | 104 | 57% | 91% | 16 m |
| 5-8 storeys | 64 | 39% | 73% | 21 m |
| 9+ storeys | 48 | 0% | 46% | 25 m |
| **All** | **414** | **57%** (was 39%) | **83%** (was 51%) | 15 m |

All scores are on held-out areas: 5-fold cross-validation grouped by H3 r8 neighbourhood (62 areas), so no building is scored by a table fitted on its own area.

## Method

- Reference: OSM `building:levels` x 3 m for 414 buildings that also have a GHSL height. No survey heights for Lebanon were found.
- GHSL height (GHS-OBAT, EU JRC, 100 m grid, around 2018) is grouped into bands; each band's middle value and range are the median and the 15th-85th percentiles of the reference heights in that band. A footprint-size split was tried and did not help.
- U-02 now uses this table for every GHSL height (`height_low_m`, `height_mid_m`, `height_high_m`).

## Limits (show these to users)

- Towers are underestimated badly (about 18 m too low): GHSL averages 100 m squares. The 3D view must not present tall buildings as measured.
- References are OSM-tagged buildings: mostly towns and taller than average, so rural accuracy is unknown.
- Heights describe the building stock before the war, not what stands today.
- Label for screens: "Height estimated from satellite data (range); towers may be much taller."
