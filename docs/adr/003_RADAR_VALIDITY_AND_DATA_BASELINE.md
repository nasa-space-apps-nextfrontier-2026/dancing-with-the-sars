# ADR: Conditional science and proposed 15-source baseline

Status: **PROPOSED — ARCHITECT RECOMMENDATION** (14 November 2026). Existing explicit safety/stack requirements remain binding; approval of added mechanics is pending.

[Decision log](../12_RISK_REGISTER_AND_DECISION_LOG.md)

## Source

DATASETS.md §§1–6; DATA_AND_API_PLAN.md §§1–5; ARCHITECTURE.md §1; NASA_DATASET_ANALYSIS.md §§2/9

## Decision

Recommend 15 families, retaining current 14 pending leader approval. Use BETA/PROVISIONAL/V1 GCOV with version QA; GSLC/GUNW only if scientifically valid and within tier budget.

## Rationale

Only BETA supplies before period in source snapshot; archives support time baselines; no valid ground truth is established.

## Alternatives

Silently approving proposal, interpolating missing passes, treating imagery as analysis or assuming coherence correction are rejected.

## Consequences and verification

All counts/dates remain 13 Nov source snapshot; verify scene access and aligned validation. No guaranteed damage proof or calibrated confidence. M1 science and M2 catalogue. T-RADAR/T-ML/T-VALIDATION.
