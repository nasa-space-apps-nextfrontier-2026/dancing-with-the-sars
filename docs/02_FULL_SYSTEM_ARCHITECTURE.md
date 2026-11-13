# Full system architecture

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Architectural baseline

Sources: ARCHITECTURE.md Parts 1–4, Shared by all parts; PROJECT_PLAN.md §8; UI_DESIGN.md §2.1. Use a simple modular monolith: React/Vite/MapLibre client; FastAPI API and a Python scheduler/worker sharing versioned domain modules; PostgreSQL/PostGIS; private filesystem artifacts. No microservice fleet or paid infrastructure. React client cannot confer authority on an endpoint or map file.

ARCHITECT RECOMMENDATION: cookie sessions, explicit area scopes, immutable processing runs, DB-backed jobs and publication views minimize integration overhead and provide a single enforcement point. Worker and API use different least-privilege DB accounts. All storage starts private; approved sanitized artifacts are promoted to a separate public directory.

## Context

```mermaid
flowchart LR
  Public[Logged-out visitor] --> Preview[Sanitized public preview]
  User[Analyst / Officer / Coordinator / Admin] --> App[CIVISAR web application]
  NASA[NASA / ASF scientific products] --> Ingest[Private ingestion]
  Human[Licensed humanitarian sources] --> Ingest
  Ingest --> App
  App --> Brief[Authorised A4 brief]
  App --> Preview
```

## Containers and trust boundaries

```mermaid
flowchart TB
  subgraph Browser[Untrusted browser]
    UI[React Vite MapLibre]
  end
  subgraph Local[Private demo host]
    API[FastAPI: session / policy / bounded API]
    DB[(PostgreSQL PostGIS)]
    Worker[Python scheduler and GIS worker]
    Private[(Restricted COG PMTiles GeoJSON)]
    Publish[Delay aggregation suppression gate]
    Safe[(Public approved artifacts)]
    Graph[Local road graph]
  end
  UI --> API
  API --> DB
  API --> Private
  API --> Graph
  Worker --> DB
  Worker --> Private
  Private --> Publish
  Publish --> Safe
  API --> Safe
  Sources[External source APIs] --> Worker
  GIBS[GIBS display tiles] --> UI
```

GIBS requests reveal viewport to an external service. ARCHITECT RECOMMENDATION: for restricted route/shelter views use a pre-fetched licensed AOI background through the host, disable external geocoding/analytics, and avoid precise viewport requests to third parties. No route origin/destination crosses the server's routing boundary. Public-safe mode can use GIBS with a coarse fixed AOI and attribution. TLS tunnel is transport only, not authorization.

## Components and deterministic agents

| Function | Input → stored output | Accountable implementation | API/UI use |
|---|---|---|---|
| Damage | GCOV + masks + models → damage cells and QA | M1-02 | damage, time slider |
| Facility | HOTOSM + damage + dated reports → status | M2-02 | facilities, inspector |
| Services | lights/IODA/facilities → service evidence + needs | M2-02 | summary, needs row |
| People | baseline + damage fractions → ranges + severity parts | M2-02 | summary, people |
| Shelter | buildings/height/terrain/hazards → restricted candidates | M2-05 | shelters, field checks |
| Route | private graph/closures/hazards → options/revision | M2-04 | routes, turns |
| Movement | aggregate DTM/Meta → coarse delayed trend | M2-06 | stretch layer |
| Alert | new observations → deduplicated alerts | M2-03 | feed/detail |
| Corroboration | sources + lineage + temporal/spatial match → agreement | M2-03 | evidence details |
| Orchestrator | events/revisions → jobs/invalidation | M3-04 | freshness, changed closure |
| Report | trusted structured results → brief model | M2-02 | M3-03 API / M4-03 print |
| Safety | role/area/tags/release time → allow/filter/deny | M3-02 | every response/file/export |

Named functions share contracts; they are not autonomous conversational agents. A future LLM only explains trusted safe outputs and cannot invent numbers or transmit restricted context.

```mermaid
flowchart TB
  Router[FastAPI routers] --> Policy[Safety and session policy]
  Policy --> Query[Read models and trace]
  Policy --> Domains[People Facility Services Report]
  Policy --> Restricted[Local Route and Shelter]
  Scheduler[Worker scheduler] --> Radar[Damage processing]
  Scheduler --> Live[Alert and Corroboration]
  Scheduler --> Orchestrator[Revision and publication orchestration]
  Radar --> Repository[Versioned repositories and artifact manifests]
  Live --> Repository
  Domains --> Repository
  Restricted --> Repository
  Query --> Repository
  Orchestrator --> Repository
```

## Proposed monorepo (only docs exist now)

```text
dancing-with-the-sars/
  README.md                         existing, unchanged
  docs/                             references + this blueprint
    contracts/                      draft OpenAPI and synthetic examples
    tasks/                          exactly four member work packages
    adr/                            proposed decisions
  apps/web/src/{screens,components,api,mocks}     planned M4
  backend/app/{api,auth,policy,models,schemas}    planned M3
  backend/migrations/                           planned M3
  pipelines/{radar,geodata,alerts,routing,shelter} planned M1/M2
  worker/                                      planned M3
  tests/{unit,geo,api,security,e2e}              planned shared
  infra/{compose.yaml,proxy,ci}                 planned M3
  scripts/{preflight,load_demo,verify_demo}      planned M3
  data/{raw,staging,private,public,manifests}     ignored, never committed
```

## Processing DAG

```mermaid
flowchart LR
  Discovery[Discover scenes] --> Licence[Licence and access gate]
  Licence --> Manifest[Metadata checksum manifest]
  Manifest --> Download[Tiered download and AOI crop]
  Download --> QA[CRS time version nodata QA]
  QA --> Align[Register mask harmonize]
  Align --> Features[Built-up HH HV features]
  Features --> Model[Quiet-trained anomaly score]
  Model --> Review[QA reason codes uncertainty]
  Review --> Cells[H3 r9 stable area tables]
  Pop[Population facilities services] --> Cells
  Cells --> Raster[COG and tiles]
  Cells --> Vector[PMTiles and bounded GeoJSON]
  Cells --> API[Filtered API values]
  Raster --> API
  Vector --> API
  API --> UI[Map summary sources]
```

## Radar pass ingestion

```mermaid
sequenceDiagram
  participant W as Worker
  participant S as ASF/CMR
  participant P as Radar pipeline
  participant D as DB/private files
  participant G as Publication gate
  W->>S: Search by collection/track/frame/AOI/date
  S-->>W: Metadata and acquisition/version
  W->>P: Licensed manifest and authorized download
  P->>P: Crop/register/mask/harmonize/model/QA
  P->>D: Atomic versioned run + lineage + checksums
  W->>G: Evaluate release and sensitivity
  G->>D: Publish approved r8 aggregate only after 72 h
```

## Live hazard alert

```mermaid
sequenceDiagram
  participant W as Worker
  participant S as Source adapter
  participant D as Database
  participant A as API
  participant U as UI
  W->>S: Bounded poll with credentials on server
  alt fetch succeeds
    S-->>W: Observation + source/fetch dates
    W->>D: Dedup cluster, independent corroboration, commit
  else timeout or rate limit
    W->>D: Keep last-good, cached=true, last_error redacted
  end
  U->>A: GET alerts and status
  A->>D: Role/area/time filtered read
  A-->>U: Evidence, age and cached flags
```

## Route and changed closure

```mermaid
sequenceDiagram
  participant O as Officer
  participant A as API policy
  participant R as Local route module
  participant D as DB
  O->>A: POST routes (authorized area, no external URL)
  A->>A: Session/role/area validation and throttle
  A->>R: Graph revision + origin/destination
  R-->>A: Distinct options with seven facts
  A->>D: Redacted audit + route revision
  A-->>O: Options and verification warning
  O->>A: POST closure report
  A->>D: Validate report, confirm separately
  D->>R: Confirmed closure increments graph revision
  O->>A: GET route status
  A-->>O: Invalidated route, recompute warning
```

## Source trace and brief export

```mermaid
sequenceDiagram
  participant U as User
  participant A as API
  participant P as Policy
  participant D as DB
  U->>A: GET value trace / POST brief
  A->>P: Session, area, object, evidence tags, release time
  P-->>A: Allowed field set or denial
  A->>D: Fetch immutable values/run/source lineage
  A-->>U: Filtered trace / printable brief with footnotes
  U->>U: Print A4, authenticated live-view QR
```

Storage, API responses and presentation are distinct artifacts: raw features never automatically become browser fields. [Security](07_SECURITY_PRIVACY_AND_RBAC.md) defines per-resource filtering; [API](05_BACKEND_DATABASE_AND_API_CONTRACTS.md) defines shape; [UI](06_FRONTEND_DESIGN_AND_SCREEN_PLAN.md) defines display.
