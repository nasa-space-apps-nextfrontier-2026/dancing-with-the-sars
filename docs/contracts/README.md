# Draft contract workspace

[Blueprint index](../README.md) · [API design](../05_BACKEND_DATABASE_AND_API_CONTRACTS.md)

Every example is synthetic, contains no operational geometry, and is not a claim about Lebanon. `demo-area-01` is an opaque fixture ID, not a valid production H3 index. Real production rows must use valid H3 IDs and stable admin crosswalks. JSON placeholders are deliberate redactions; nullable fields and optional arrays need final domain refinement at H2.

[openapi.yaml](openapi.yaml) uses JSON syntax, which is valid YAML 1.2. It is a draft OpenAPI 3.1 contract with typed essential responses, request examples, error responses, owner/role/rate extensions and endpoint paths. It has NOT been tested against a running service. Specification/schema validation results are recorded in [planning verification](../16_PLANNING_VERIFICATION.md); generated-client and live-server contract tests remain H2 implementation gates.

| Contract | Example | Purpose |
|---|---|---|
| MetricValue | [MetricValue.json](MetricValue.json) | H2 shared fixture, no sensitive coordinates |
| SourceRecord | [SourceRecord.json](SourceRecord.json) | H2 shared fixture, no sensitive coordinates |
| RouteOption | [RouteOption.json](RouteOption.json) | H2 shared fixture, no sensitive coordinates |
| ShelterCandidate | [ShelterCandidate.json](ShelterCandidate.json) | H2 shared fixture, no sensitive coordinates |
| AlertDetail | [AlertDetail.json](AlertDetail.json) | H2 shared fixture, no sensitive coordinates |
| Layer | [Layer.json](Layer.json) | H2 shared fixture, no sensitive coordinates |
| AreaSummary | [AreaSummary.json](AreaSummary.json) | H2 shared fixture, no sensitive coordinates |
| Error | [Error.json](Error.json) | H2 shared fixture, no sensitive coordinates |

## Endpoint ownership

M3 owns the HTTP implementations below. Domain tasks retain accountable algorithm ownership; M4 owns typed client/fixture consumption. Freeze request/response version 0.1 at H2 with all four reviewers. Breaking changes require contract PR first, fixture update and named downstream acknowledgement.

| Method | Path under /api/v1 | Roles | Params/body | Response | HTTP owner | Domain dependency | Limit class |
|---|---|---|---|---|---|---|---|
| POST | /session | public | username,password | Session | M3-02 | M3-02 | auth |
| GET | /session | signed_in | none | Session | M3-02 | M3-02 | read |
| DELETE | /session | signed_in | CSRF header | Empty | M3-02 | M3-02 | write |
| GET | /roles | signed_in | none | Roles | M3-02 | M3-02 | read |
| GET | /public/map | public | bbox optional; fixed demo AOI | PublicMap | M3-02 | M4-01 | public |
| GET | /health | public | none | Health | M3-04 | M3-04 | public |
| GET | /status | public | none; sanitized | Status | M3-04 | M2-03 | public |
| GET | /layers | public | public_only or authorized area_id | LayerList | M3-03 | M1-02 | read |
| GET | /layers/{layer_id} | public | layer_id; policy may deny | Layer | M3-03 | M1-02 | read |
| GET | /layers/{layer_id}/tiles/{z}/{x}/{y} | public | layer_id,z,x,y; same policy as layer | Binary | M3-02 | M1-02 | tiles |
| GET | /layers/{layer_id}/files/{file_id} | public | file_id; Range header; scoped manifest allowlist | Binary | M3-02 | M2-01 | tiles |
| GET | /layers/{layer_id}/timeseries | analyst+ | area_id,from,to,polarization | Series | M3-03 | M1-02 | read |
| GET | /areas | analyst+ | bbox,cursor,limit | AreaList | M3-03 | M2-01 | read |
| GET | /areas/{area_id}/summary | analyst+ | area_id,as_of | AreaSummary | M3-03 | M2-02 | read |
| GET | /areas/{area_id}/values | analyst+ | metric,as_of,cursor | MetricList | M3-03 | M2-02 | read |
| GET | /areas/{area_id}/people | analyst+ | as_of | MetricList | M3-03 | M2-02 | read |
| GET | /areas/{area_id}/services | analyst+ | as_of | ServiceList | M3-03 | M2-02 | read |
| GET | /areas/{area_id}/facilities | analyst+ | type,cursor; sensitive sites filtered | FacilityList | M3-03 | M2-02 | read |
| GET | /areas/{area_id}/damage | analyst+ | pass_id; r9 scoped | DamageList | M3-03 | M1-02 | read |
| GET | /areas/{area_id}/validation | analyst+ | assessment_id; licence/availability gate | ValidationList | M3-03 | M1-03 | read |
| GET | /alerts | analyst+ | area_id,type,since,cursor,limit | AlertList | M3-03 | M2-03 | read |
| GET | /alerts/{alert_id} | analyst+ | alert_id; area/object check | AlertDetail | M3-03 | M2-03 | read |
| POST | /alerts/{alert_id}/reviews | analyst+ | status,note; CSRF; append-only | Review | M3-03 | M2-03 | write |
| GET | /sources | public | cursor; sanitized catalogue | SourceList | M3-03 | M2-01 | public |
| GET | /sources/{source_id} | public | source_id; restricted lineage filtered | SourceRecord | M3-03 | M2-01 | read |
| GET | /values/{value_id}/trace | analyst+ | value_id; transitive lineage authorization | Trace | M3-03 | M1-03 | read |
| POST | /routes | officer+ | area_id,origin_id,destination_id,direction,vehicle_type | RouteList | M3-03 | M2-04 | compute |
| GET | /routes/{route_id} | officer+ | route_id; owner/area authorization | RouteOption | M3-03 | M2-04 | read |
| GET | /routes/{route_id}/status | officer+ | route_id,known_revision | RouteStatus | M3-03 | M2-04 | read |
| POST | /closures | officer+ | segment_id,report,evidence_ids; no coordinates in logs | Closure | M3-03 | M2-04 | write |
| POST | /closures/{closure_id}/review | coordinator+ | decision,reason,evidence_ids | Closure | M3-03 | M2-04 | write |
| GET | /shelters | coordinator+ | area_id,mode,space_per_person_m2,limit | ShelterList | M3-03 | M2-05 | compute |
| POST | /shelters/capacity | coordinator+ | candidate_id,mode,space_per_person_m2 | ShelterCandidate | M3-03 | M2-05 | compute |
| POST | /shelters/{candidate_id}/field-checks | coordinator+ | check_type,note; no external dispatch | FieldCheck | M3-03 | M2-05 | write |
| POST | /briefs | analyst+ | area_id,as_of; authorized sections only | Brief | M3-03 | M2-02 | write |
| GET | /briefs/{report_id} | signed_in | report_id; re-evaluate role/area at read | Brief | M3-03 | M4-03 | read |
| GET | /briefs/{report_id}/print | signed_in | report_id; role-filtered HTML | Binary | M3-03 | M4-03 | read |
| GET | /admin/audit | admin | cursor,from,to; redacted | AuditList | M3-02 | M3-02 | read |
| PATCH | /admin/users/{user_id}/roles | admin | role,area_scopes,reason; CSRF | Roles | M3-02 | M3-02 | write |
| POST | /admin/jobs/{job_id}/retry | admin | idempotency_key; no arbitrary command | Job | M3-04 | M3-04 | write |

`analyst+`: analyst/officer/coordinator/admin with area scope. `officer+`: officer/coordinator/admin with area scope. `coordinator+`: coordinator/admin with area scope. Admin does not bypass area/object/time checks. Public-capable layer paths still deny private layers to anonymous users. Role names are proposed capabilities, not authority granted by client input.

Rate classes and evidence/error rules: [backend contract](../05_BACKEND_DATABASE_AND_API_CONTRACTS.md). Read status/metadata/availability before rendering; null means unknown, not zero. Cached is an orthogonal boolean displayed as DataAge Cached alongside last-good dates.
