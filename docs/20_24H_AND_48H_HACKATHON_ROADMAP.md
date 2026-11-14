# Conditional 24-hour and 48-hour roadmaps

Status: planning scenarios, not official challenge rules or elapsed work. Hours are relative to event start. A is the full-stack Team Lead (Rashiru), B is radar engineer (Udula), C is model/geodata engineer (Thanoban). Tasks use the [three-member map](18_THREE_MEMBER_EXECUTION_PLAN.md). Each schedule has explicit review, rest and fallback time.

## If the event is 24 hours

| Hours | A: app, backend and coordination | B: radar | C: scoring and QA | Gate |
|---|---|---|---|---|
| 0-2 | Confirm rules/rights, branch and contract; run synthetic slice and auth tests | Metadata/access preflight, 151D/72 version manifest | Feature/output schema, synthetic scoring test and QA plan | H2 contract acknowledged by all three |
| 2-5 | Sign-in/session restoration; map selection and typed area/source API | Permitted tier-A download/crop only if access confirmed | H3/feature fixture, no-data rules and baseline model | Failing access keeps synthetic demo |
| 5-9 | NISAR controls, evidence and Sources on fixture; review B/C handoff | Registration, HH/HV features, version comparison | Candidate scoring and spatial hold-out harness | H9 usable common coverage and QA evidence |
| 9-13 | Integrate only verified artifact metadata; area summary and source trace | Change image/manifest with provenance | Candidate outputs, negative controls and uncertainty report | **H13 real-radar go/no-go**: no valid version QA means no real change claim |
| 13-17 | End-to-end role tests, build, accessible flow and demo fallback | Correct data defects, no new large tier | Review false alarms, top cells and interpretation | H17 integration freeze; P1 cut |
| 17-20 | Rehearsal, video capture and backup | Independent radar source check | Science wording/citation check | H20 recorded fallback ready |
| 20-24 | Final tests, video/submission buffer and release decision | Reproduction support | Sources/limits support | Submit only verified claims; unresolved gates disclosed |

P0 in 24h is an interactive, clearly identified NISAR-centred map with date/version and polarization controls, a candidate overlay **only if validated**, area summary, Sources and server-side role denial. If real products fail, demonstrate the synthetic interaction and state explicitly that real NISAR analysis is blocked. Do not stretch the same scope to alerts, routes, shelters or a trained large model. Reserve human breaks within each work block and rotate review duties rather than treating 24 hours as 24 productive hours per person.

## If the event is 48 hours

| Hours | A: app, backend and coordination | B: radar | C: scoring and QA | Gate |
|---|---|---|---|---|
| 0-2 | Rule/rights and contract freeze | Scene/version metadata | Feature schema, split/QA plan | H2 three-way acceptance |
| 2-8 | Auth, safe map, area/source API and ingestion boundary | Tier A/B only when permitted; crop/registration | Synthetic and then aligned feature tests | H8 common valid pixels/version metadata |
| 8-16 | NISAR comparison controls, Sources, freshness and area flow | HH/HV, change COG and pass manifest | Isolation Forest/fallback, spatial hold-out | H16 first contract-compatible cell artifact |
| 16-24 | First integrated real-data attempt; source/trace and denial checks | Change artifacts with checksums/QA | Candidate classes and independent controls | **H24 go/no-go** real radar vs labelled synthetic fallback |
| 24-32 | P1 alert/brief and protected fictional route/shelter UI only if P0 green | Repeatability and optional later-pass corrections | Validation report, ancillary joins if rights allow | H32 role/science/source review |
| 32-38 | Accessibility, CI, integration, privacy and backup rehearsal | Reproduce radar manifest | Reproduce model report | **H38 feature freeze**, fixes only |
| 38-44 | Record primary and backup demo; restore/failure rehearsal | Verify imagery and dates | Verify wording and metrics | H44 video/citations/submission packet ready |
| 44-48 | Final review and submission buffer | Reproduction support | Science/source support | Release only reviewed state |

The real-data critical path is permitted scene access -> registered, version-checked radar features -> model QA -> validated artifact ingestion -> protected API -> map and summary. A works the frontend and backend in vertical slices, not two separate parallel projects. The synthetic path runs from H2 so external access never blocks a coherent walkthrough. New work stops at each freeze even if an optional feature is tempting. No tunnel or production deployment is presumed.
