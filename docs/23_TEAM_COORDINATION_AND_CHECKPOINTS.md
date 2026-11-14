# Three-member coordination and checkpoints

Status: working protocol for A (Rashiru, Team Lead), B (Udula, radar) and C (Thanoban, scoring/geodata). Use the [ownership map](18_THREE_MEMBER_EXECUTION_PLAN.md), [integration contract](21_ML_BACKEND_FRONTEND_INTEGRATION.md) and [conditional schedules](20_24H_AND_48H_HACKATHON_ROADMAP.md). This Markdown board works without an external service.

## Checkpoint routine

At H0/H2 and every 4 hours in a 24h event (every 6-8 hours in 48h), hold a 10-minute standup. Each member reports **done with evidence, next, blocker, handoff needed, risk to critical path**. A records decisions and links the exact commit/manifest/test, then updates the board below. A failed gate is recorded as BLOCKED, not changed to “done” because a mock exists. During focus blocks, asynchronous updates are acceptable; urgent security/science blockers interrupt the block.

| Gate | Owner | Required evidence | Escalation |
|---|---|---|---|
| H2 contract | A with B/C | Canonical fields, units, H3, CRS, UTC, schema version, role/visibility and synthetic fixture accepted | Freeze dependent real integration until resolved; keep fixture path |
| First B→C | B | Manifest, coverage, version, registration, checksum and missing passes | If no usable pair, declare real radar blocked and protect fallback |
| First C→A | C | Scored synthetic cells, Unknown cases and model QA plan | Reject incompatible schema; contract PR first |
| First full stack | A | Authenticated map→area→API→summary/source walkthrough plus tests | Fix access/contract errors before more screens |
| Real-data decision | A, B, C | B calibration QA + C evaluation + A protected API test | Any failure means no real candidate overlay claim |
| Freeze | A | Green P0 tests, citations, privacy check, backup recording | Fixes only; do not start P2 or incomplete P1 |
| Submission | A | Video, source/limitations text, challenge requirements and backup checked | Hold inaccurate or sensitive material; disclose blocked real data |

## PR and handoff rule

One branch per active member: A uses the combined full-stack branch; B and C retain their existing branch names and pointers until they choose to update them. Every PR targets `dev` and includes task ID, source, data classification, schema/manifest version, paths, tests, screenshots when safe, known limits, reviewer and rollback. A coordinates merges after independent review; nobody force-pushes or edits another member's branch. Never commit raw NISAR scenes, private geometry, credentials or real restricted records. Contract changes land ahead of their consumers. A's full-stack branch is not merged to `dev` automatically by this phase.

Risk escalation: any unauthorized location disclosure, source/licence ambiguity, failed BETA-versus-PROVISIONAL QA, apparent false scientific claim, data corruption, lost demo backup or blocked submission requirement becomes **RED** immediately. A halts the affected release path and assigns a reproduction/owner. A missing optional P1 item becomes **AMBER** and is cut at the next gate. Timebox debugging to one checkpoint interval; if unresolved, use the clearly labelled synthetic fallback and document the loss. The feature-freeze time is H17 for 24h, H38 for 48h; only reviewed fixes follow it.

## Small operational status board

Update this table in the team's next documentation PR; do not mistake a local working branch for a remote one.

| Work item | Owner | State | Evidence or blocker | Next checkpoint |
|---|---|---|---|---|
| Three-way contract sign-off | A/B/C | TODO | Canonical draft exists; B/C acknowledgement pending | H2 |
| NISAR scene/version manifest | B | TODO | Earthdata access and product QA unverified | First B→C |
| Synthetic scored-cell contract | C | TODO | Align with B features and canonical schema | First C→A |
| Map→area→API→source slice | A | IN PROGRESS | Phase 3 feature branch and tests | First full stack |
| Real radar publication gate | A/B/C | BLOCKED | No validated B/C artifact yet | Real-data decision |
| Demo/video/submission packet | A | TODO | Duration/rules not confirmed | Freeze |

Allowed states: TODO, IN PROGRESS, BLOCKED, REVIEW, DONE. A DONE row needs a commit/artifact and a passing check. The board intentionally contains no external account identifiers or private coordinates.
