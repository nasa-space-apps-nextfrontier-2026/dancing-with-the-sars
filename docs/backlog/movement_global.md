# Movement trend and global watch list: design (task M2-06)

Design only, written 14 November 2026 by Thanoban. **Stretch / after the hackathon core.** Nothing here is built. See [PROJECT_PLAN.md](../PROJECT_PLAN.md) section 6.8 for the feature and [DATASETS.md](../DATASETS.md) for the sources.

## Goal

Show **area-level** population movement as a delayed trend ("people leaving Area A, arriving around Town B"), never live people, never individuals, never camp or shelter coordinates.

## Inputs (all coarse and delayed)

| Signal | Source | How often | Access | Notes |
|---|---|---|---|---|
| Movement range change | Meta Movement Distribution Maps (HDX, CC BY) | Every 2 weeks, about 90 days kept | HDX download | Sample bias: only people who use Meta apps with location on. Coverage can drop in a crisis |
| Reported displacement | IOM DTM | Weekly | DTM API (free key), HDX | Reports by district; check the licence and citation text |
| Lights dropping or appearing | Black Marble (our night-light function) | Daily | Already built (M1-04) | Supporting signal only: a dark area is not proof people left |
| New tent or camp areas | NISAR / Sentinel-1 change on open land | Each pass | Radar pipeline | Never published as coordinates |
| Estimated displaced | People/impact results (M2-02) | Each pass | Rashiru's pipeline | Ranges only |

## Output (one row per area pair and period)

`origin_area, destination_area, period_start, period_end, direction, change_low, change_high, label, sources, safety_tag`

- Areas are neighbourhood or district level (H3 resolution 8 at most); small counts are suppressed (do not publish a flow under 10 people or one that identifies a place).
- The period is a multi-day window, shown **at least 72 hours after** the last observation, and often 1 to 2 weeks because of the source cadence.
- Every row carries an evidence label (Reported when from IOM, Observed only for satellite signals), source names and dates, and a `restricted` safety tag. Shown to logged-in roles only.
- Ranges, not single numbers. "Unknown" when the sources disagree or one is missing.

## Rules

1. No individual, vehicle, convoy or phone data, and no live tracking (project safety rule).
2. Aggregated and delayed only; no camp, shelter or displacement-site coordinates in any output.
3. A trend is never labelled "safe" or "confirmed"; it carries the weakest evidence label of its inputs.
4. If a source licence or terms do not allow the use, the trend stays disabled and the UI shows "not available".
5. A missing source gives `unknown`, never an interpolated guess.

## Global watch list (design)

Same idea, per country: a conflict-area list that grows from event data (UCDP, since ACLED's terms bar ML testing), with daily night-light and fire pre-alerts (the M1-04 functions) and radar change detection **only inside watched areas**. Radar for the whole planet each pass is too heavy and not needed.

## Tests to write when it is built

- Aggregation and delay: output is never newer than 72 hours and never below the small-count threshold.
- No individual payload: fixtures contain no coordinates finer than the area, no ids, no timestamps finer than the period.
- Source missing or disagreeing: output `unknown`.
- Disabled by licence: the function returns "not available", not an empty trend.

## Open questions

- Which Meta product is current for Lebanon and what is its latest release date (check on HDX at build time).
- IOM DTM coverage and cadence for south Lebanon (check at build time).
- Whether the small-count threshold of 10 fits the source granularity.
