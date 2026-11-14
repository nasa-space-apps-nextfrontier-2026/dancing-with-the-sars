# CIVISAR implementation blueprint

> **Current team plan:** [three-member execution](18_THREE_MEMBER_EXECUTION_PLAN.md), [Team Lead full-stack backlog](19_TEAM_LEAD_FULLSTACK_PLAN.md), [24h/48h scenarios](20_24H_AND_48H_HACKATHON_ROADMAP.md), [integration handoff](21_ML_BACKEND_FRONTEND_INTEGRATION.md), [demo acceptance](22_DEMO_AND_ACCEPTANCE_CHECKLIST.md), and [coordination board](23_TEAM_COORDINATION_AND_CHECKPOINTS.md). The four-member pages below are historical planning evidence. The challenge duration is unconfirmed.

**Implementation status:** [Phase 4 full-stack report](24_PHASE4_FULLSTACK_IMPLEMENTATION_REPORT.md) and [radar artifact handoff](25_RADAR_ARTIFACT_HANDOFF.md). The original source references below remain unchanged.

**Phase 5 prototype work:** [UI audit](26_PROTOTYPE_UI_AUDIT.md), [interaction matrix](27_PROTOTYPE_INTERACTION_MATRIX.md), [visual verification](28_PROTOTYPE_VISUAL_VERIFICATION.md), and [implementation report](29_PHASE5_PROTOTYPE_IMPLEMENTATION_REPORT.md). Visual fidelity is not yet verified.

Prepared 14 November 2026 from seven unchanged source references. This is a planning-only deliverable: no app, radar acquisition, live-data validation or deployment has been performed. Scientific observations are the source authors' **13 November 2026 snapshot**. Recommendations remain PROPOSED; missing scientific evidence stays VERIFY/BLOCKED.

Start with the source audit, scope, architecture and your member task file. Freeze shared contracts at hour 2. Safety, role enforcement and provenance are release blockers.

## Planning documents

- [00_SOURCE_AUDIT.md](00_SOURCE_AUDIT.md)
- [01_REQUIREMENTS_AND_SCOPE.md](01_REQUIREMENTS_AND_SCOPE.md)
- [02_FULL_SYSTEM_ARCHITECTURE.md](02_FULL_SYSTEM_ARCHITECTURE.md)
- [03_DATA_CATALOGUE_AND_SOURCE_MAPPING.md](03_DATA_CATALOGUE_AND_SOURCE_MAPPING.md)
- [04_GEOSPATIAL_AND_ML_PIPELINES.md](04_GEOSPATIAL_AND_ML_PIPELINES.md)
- [05_BACKEND_DATABASE_AND_API_CONTRACTS.md](05_BACKEND_DATABASE_AND_API_CONTRACTS.md)
- [06_FRONTEND_DESIGN_AND_SCREEN_PLAN.md](06_FRONTEND_DESIGN_AND_SCREEN_PLAN.md)
- [07_SECURITY_PRIVACY_AND_RBAC.md](07_SECURITY_PRIVACY_AND_RBAC.md)
- [08_FOUR_MEMBER_TASK_ALLOCATION.md](08_FOUR_MEMBER_TASK_ALLOCATION.md)
- [09_48_HOUR_DEVELOPMENT_ROADMAP.md](09_48_HOUR_DEVELOPMENT_ROADMAP.md)
- [10_TESTING_AND_ACCEPTANCE_PLAN.md](10_TESTING_AND_ACCEPTANCE_PLAN.md)
- [11_DEVOPS_DEPLOYMENT_AND_GIT_WORKFLOW.md](11_DEVOPS_DEPLOYMENT_AND_GIT_WORKFLOW.md)
- [12_RISK_REGISTER_AND_DECISION_LOG.md](12_RISK_REGISTER_AND_DECISION_LOG.md)
- [13_DEMO_STORY_SUBMISSION_AND_CITATIONS.md](13_DEMO_STORY_SUBMISSION_AND_CITATIONS.md)
- [14_REQUIREMENTS_TRACEABILITY_MATRIX.md](14_REQUIREMENTS_TRACEABILITY_MATRIX.md)
- [15_TEAM_ONBOARDING.md](15_TEAM_ONBOARDING.md)
- [17_TEAM_ASSIGNMENT_AND_BRANCHES.md](17_TEAM_ASSIGNMENT_AND_BRANCHES.md)

## Supporting artifacts

- [Dataset exclusions](03A_DATASET_EXCLUSIONS.md)
- [Source section coverage](14A_SOURCE_SECTION_COVERAGE.md)
- [Source URL register](14B_SOURCE_LINK_REGISTER.md)
- [Udula (Member 1): NISAR ML](tasks/MEMBER_1_UDULA_NISAR_ML.md)
- [Thanoban (Member 2): small-data ML](tasks/MEMBER_2_THANOBAN_SMALL_DATA_ML.md)
- [Rashiru (Member 3): frontend and backend](tasks/MEMBER_3_RASHIRU_FRONTEND_BACKEND.md)
- [Chames (Member 4): backend and data](tasks/MEMBER_4_CHAMES_BACKEND_DATA.md)
- [Contract inventory and eight synthetic JSON examples](contracts/README.md)
- [Draft OpenAPI](contracts/openapi.yaml)
- [Planning manifest](contracts/planning_manifest.json)
- [Rerunnable documentation validator](contracts/validate_planning.py)
- [ADR 001: modular monolith](adr/001_MODULAR_MONOLITH_AND_CONTRACTS.md)
- [ADR 002: publication and local routing](adr/002_PUBLICATION_AND_LOCAL_ROUTING.md)
- [ADR 003: scientific/data baseline](adr/003_RADAR_VALIDITY_AND_DATA_BASELINE.md)

## Untouched source references

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DATASETS.md](DATASETS.md)
- [DATA_AND_API_PLAN.md](DATA_AND_API_PLAN.md)
- [NASA_DATASET_ANALYSIS.md](NASA_DATASET_ANALYSIS.md)
- [NASA_Open_Data_Links_Earth_Impact_Intelligence.pdf](NASA_Open_Data_Links_Earth_Impact_Intelligence.pdf)
- [PROJECT_PLAN.md](PROJECT_PLAN.md)
- [UI_DESIGN.md](UI_DESIGN.md)

## Actual validation

The [Phase 5.1 UI fidelity report](30_PHASE5_1_UI_FIDELITY_COMPLETION.md) records the ten React view structures, repeatable Chrome screenshot pairs and the remaining major visual deviations. Browser capture is working; prototype fidelity is not yet accepted.

See [planning verification](16_PLANNING_VERIFICATION.md) for executed checks and limits. [Application acceptance](10_TESTING_AND_ACCEPTANCE_PLAN.md) contains future tests and does not imply they already ran. [Git workflow](11_DEVOPS_DEPLOYMENT_AND_GIT_WORKFLOW.md) distinguishes local branch setup from optional remote publication.
