# ADR: Modular monolith and shared contracts

Status: **PROPOSED — ARCHITECT RECOMMENDATION** (14 November 2026). Existing explicit safety/stack requirements remain binding; approval of added mechanics is pending.

[Decision log](../12_RISK_REGISTER_AND_DECISION_LOG.md)

## Source

ARCHITECTURE.md Parts 1–4 and H2 agreements

## Decision

Use one FastAPI API and worker sharing deterministic modules, PostGIS and private files; React/Vite/MapLibre. H2 OpenAPI and fixtures freeze before feature integration.

## Rationale

Minimizes deployment and schema drift for four members/48 h; worker isolates long radar jobs from HTTP.

## Alternatives

Independent microservices would add orchestration and service-auth work; no working implementation requires a stack change.

## Consequences and verification

Single host is a failure domain; mitigate through snapshots/recorded demo and bounded jobs. M3 owns service integration; M1/M2 own science. T-CONTRACT/T-JOBS/T-DEVOPS.
