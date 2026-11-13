# Requirements and delivery scope

[Blueprint index](README.md)

Status: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.


## Mission and boundaries

CIVISAR supports authorised civilian humanitarian interpretation of war impacts. The judged example is south Lebanon, 35.0–36.0 E, 33.0–33.6 N, track 151 descending/frame 72. Those study bounds are public research metadata, not operational locations. NISAR is the challenge anchor. No reconstruction planning, general natural-disaster expansion, targeting, military/frontline objects or live people/vehicle/phone/convoy tracking belongs in this build.

Sources: PROJECT_PLAN.md §§1–13; ARCHITECTURE.md Ground rules, MVP, Parts 1–4; UI_DESIGN.md §§1–7. User's master request keeps provenance and safety as non-negotiable even under de-scope.

## Complete delivery inventory

Each story has one accountable task. Dependencies, expected files, estimates and tests are expanded in [four member allocation](08_FOUR_MEMBER_TASK_ALLOCATION.md) and individual task files; [roadmap](09_48_HOUR_DEVELOPMENT_ROADMAP.md) supplies gates.

| ID | Feature | Phase | Accountable task | Gate | Acceptance ID | Input → output |
|---|---|---|---|---|---|---|
| F01 | NISAR Jan–Jun HH/HV/HH−HV candidate changes, tiling, later passes and gaps | MVP | M1-02 | H16/H24 | T-RADAR | GCOV manifests → damage_cells + COGs |
| F02 | Population baseline, affected/displaced ranges and five-part severity | MVP | M2-02 | H24 | T-PEOPLE | WorldPop + cell shares → MetricValue |
| F03 | Facility inventory, reported operating state, service needs | MVP | M2-02 | H24 | T-FACILITY | HOTOSM + reports → AreaSummary |
| F04 | FIRMS, Black Marble archive/NRT, IODA, radar alerts and corroboration | MVP | M2-03 | H24 | T-ALERT | adapters → AlertDetail |
| F05 | People-first A4 brief, sources, vulnerable groups, no logistics counts | MVP | M4-03 | H32/H38 | T-BRIEF | AreaSummary → authorized HTML/print |
| F06 | Two or three inbound/outbound local route options, seven facts, closure update | MVP | M2-04 | H32 | T-ROUTE | local graph + closures → RouteOption[] |
| F07 | Ranked building shelters, modes, field checks; open-land candidates | MVP; open land reduced first if needed | M2-05 | H24/H32 | T-SHELTER | footprints + levels/height + hazards → ShelterCandidate[] |
| F08 | Sign-in, demo roles, public-safe view, protected map files and deny demo | MVP | M3-02 | H12/H38 | T-RBAC | session + area scopes → filtered resources |
| F09 | Sources, trace value, model results and reproducible lineage | MVP | M3-03 | H24/H32 | T-TRACE | run manifests + metrics → SourceRecord |
| F10 | Time comparison, polarization story, before/after/swipe and inspector | MVP | M4-02 | H24 | T-UI | Layer + series → map controls |
| F11 | Phone browser alerts, summary and routes; accessible light/dark UI | MVP basic; polish de-scope only | M4-04 | H38 | T-A11Y | same API → responsive views |
| F12 | OPERA RTC-S1 cross-sensor check, ascending track 172 | Stretch | M1-04 | Before H38 or later | T-ML | independent sensor → QA report |
| F13 | GUNW baseline and GSLC cross-gap coherence | Stretch; high scientific risk | M1-04 | Before H38 or later | T-COHERENCE | validated aligned phase → optional feature |
| F14 | UNDP/CNRS-L validation overlay; UNOSAT absent for LB | Conditional stretch / VERIFY | M1-03 | H32 or later | T-VALIDATION | aligned licensed reports → analyst-only overlay |
| F15 | ACLED and Insecurity Insight context and review workflow | MVP bounded licensed context | M2-03 | H24/H32 | T-INDEPENDENCE | reports + source families → reviewed alerts |
| F16 | Power→water→health→communications dependency graph | MVP explicit observed/reported links; full network after hackathon | M2-02 | H24 | T-SERVICES | verified dependency edges → possible loss |
| F17 | IOM DTM + Meta aggregated movement and displacement context | Stretch | M2-06 | Before H38 or later | T-MOVEMENT | coarse aggregate sources → delayed trends |
| F18 | Global watch list, manual areas, ACLED weekly candidates, selective radar jobs | After hackathon | M2-06 | Post-demo | T-BACKLOG | licensed events → watch areas |
| F19 | NISAR_COP future passes; OPERA land-disturbance GIBS context | Stretch | M1-04 | Before H38 or later | T-DISPLAY | schedule/display metadata → contextual Layer |
| F20 | GHSL height fallback and HOTOSM-primary bounded Overpass | MVP | M2-01 | H12 | T-GEO | source metadata → uncertain floor-area range |
| F21 | Installable public shell and public offline summaries | Stretch | M4-04 | Before H38 or later | T-CACHE | safe content only → offline shell |
| F22 | Protected offline briefs/routes, encryption and revocation | After hackathon | M3-04 | Post-demo | T-CACHE | approved device policy → restricted local store |
| F23 | Browser PDF print export; server PDF export optional | MVP print-to-PDF; server PDF stretch | M4-03 | H38 | T-BRIEF | authorized brief → A4/QR/source footnotes |
| F24 | Optional LLM/Gemini fixed-question explanation | After hackathon (deferred stretch) | M3-04 | Post-demo | T-LLM | trusted safe results → non-authoritative explanation; no numeric invention |
| F25 | No military/frontline, live tracking, targeting, reconstruction or general disaster app | Constraint all phases | M3-02 | Every gate | T-SAFETY | safety policy → rejection/filtering |
| F26 | 72 h delay, H3 r8 public aggregation plus concentration suppression | MVP invariant | M3-02 | H12/H38 | T-DELAY | acquisition/publication timestamps → release gate |
| F27 | Licences, non-Chinese-owned sources, NASA tab citation and uncertainty | MVP invariant | M2-01 | H2/H48 | T-LICENCE | source register → allowed use and attribution |
| F28 | Twelve named deterministic functions; no autonomous LLM pipeline | MVP modules; Movement deferred | M3-04 | H24 | T-AGENTS | typed functions → immutable evidence-bearing outputs |


## Evidence and scientific meaning

Use Observed, Reported, Corroborated, Unknown. These are evidence types, not a numeric confidence ladder: retain each source's type and derivation. Corroboration is a separate independence-tested agreement, and never converts a thermal signal or anomaly into a confirmed collapse. Derived service or population claims cannot exceed the support of their weakest essential input. Keep low/high, unit, source and date on every estimate; missing values are null, never zero.

Say “Fire detected”; “Possible power loss”; “Candidate damage”; “No detected damage. Not confirmed open.”; “No reported closure”. Never promise a route or shelter is safe. Fresh/Aging/Stale describe expected update age; Cached separately describes delivery from a last-good snapshot. Show acquisition, processing, fetched-at and last-success dates.

## MVP acceptance and fallback

All seven architecture MVP capabilities remain in the demonstration. If real input is unavailable, show a labelled synthetic journey and separately disclose that real-data MVP acceptance failed. A metadata-only NISAR picture is not a processed NISAR demo. Never claim validation, downloads, API availability or live tracking from mocked screens. The backup can demonstrate UI/RBAC behavior while scientific acceptance remains BLOCKED.

De-scope in source order: optional question box; tier-C coherence; phone/print polish (retain usable responsive views and A4); open-land shelters (retain building candidates); later slider passes after July (retain actual Jan/Jun pair and visible missing data). This is a declared reduced demonstration, not full F01/F07 acceptance. Never cut NISAR, role enforcement, provenance, public aggregation or safety.
