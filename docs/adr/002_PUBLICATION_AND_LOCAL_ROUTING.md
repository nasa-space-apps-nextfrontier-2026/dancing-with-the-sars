# ADR: Private artifacts, publication and local routing

Status: **PROPOSED — ARCHITECT RECOMMENDATION** (14 November 2026). Existing explicit safety/stack requirements remain binding; approval of added mechanics is pending.

[Decision log](../12_RISK_REGISTER_AND_DECISION_LOG.md)

## Source

PROJECT_PLAN.md §10; UI_DESIGN.md §§5–7; PDF p2 §4; DATA_AND_API_PLAN.md §4

## Decision

Central server role+area+object policy on endpoints/files; >=72 h strike-change delay; public r8 plus suppression; local graph/in-app turns; private export no-store.

## Rationale

Coordinates, reports and fine-grained artifacts can leak even if UI buttons are hidden.

## Alternatives

External route service/phone handoff rejected by privacy requirement. Client-only guards and public object buckets rejected.

## Consequences and verification

Requires guarded Range/tiles/brief routes and role-aware cache invalidation. Public shell PWA stretch; private offline post-hackathon. M3 policy, M2 algorithms, M4 presentation. T-RBAC/T-LAYER/T-CACHE.
