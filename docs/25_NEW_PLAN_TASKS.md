# New plan: tasks for Udula, Chames and the team

[Blueprint index](README.md) · [New direction (doc 24)](24_3D_BIRD_VIEW_AND_DECISION_SUPPORT_PLAN.md) · [Team assignment and branches](17_TEAM_ASSIGNMENT_AND_BRANCHES.md) · [ML wiring](progress/ML_WIRING.md)

Written 14 November 2026 by Thanoban. Read [doc 24](24_3D_BIRD_VIEW_AND_DECISION_SUPPORT_PLAN.md) first: it explains the new plan (3D bird view and 360 scene, ranking, decision assistant, rebuild budget). **The target is about 70% right, not exact.** A believable, data-grounded average is enough for the scene and the budget.

## M3 publication update (15 November 2026)

This task plan preserves the original PR #21 JSON publication roadmap for historical traceability. That architecture is superseded: PostGIS is the authoritative real-data API store, and the current `GET /public/map` endpoint is permanently suppressed. `PUBLIC_RELEASE_APPROVED=true` cannot enable publication; suppressed requests return without constructing a database engine or querying PostGIS.

Before any future public release system can be enabled, it requires immutable artifact-bound approval, licence and QA checks, high-risk-cell review, spatial-cohort controls and snapshot-differencing analysis. H3 r8 aggregation and a three-candidate threshold are not sufficient humanitarian protection. References below to `worker.publish`, `PUBLISHED_DIR`, the JSON Store, wildcard scope or configurable public release describe the original PR #21 plan, not current M3 runtime behavior.

## 1. Where we are

| Done | Who |
|---|---|
| NISAR damage model, tests, Sentinel-1 cross-check, contract export, time-slider tables | **Udula** (the ML work is finished; thank you) |
| Night-light power-loss model, fire event model, live FIRMS feed, dataset records | Thanoban |
| Historical PR #21 milestone: `worker.publish`, the published-artifact JSON Store and related endpoint design were merged, then superseded by the PostGIS-backed M3 integration described above | Thanoban |
| Final free data list for the 3D scene, building heights and the budget (doc 24, section 15) | Thanoban |

## 2. Rules for every task

- Work on `dev` through a branch `feature/<task-id>-<short-name>` and a PR into `dev`. No direct push, no force push. Rashiru merges.
- **Contract first:** a new field or endpoint goes into `docs/contracts/` in its own PR before code depends on it ([21](21_ML_BACKEND_FRONTEND_INTEGRATION.md)).
- No large data, no secrets in Git. Big files go to `data/local/` (ignored); a small manifest in `data/manifests/` says how to rebuild them.
- Safety wording: never "safe"; ranges not single numbers; evidence labels Observed / Reported / Corroborated / Unknown; no live vehicle or phone data; building-level results are for logged-in roles only. Current public output is suppressed; delayed area-level publication remains future work subject to the controls above.
- CI must pass: `ruff check backend worker tests scripts` (newer ruff, including FURB, BLE, ISC rules), `python -m pytest`. Check locally before pushing.
- Commits use your own name, no AI co-author line.

## 3. Udula: data, agents and backend for the new plan

You finished the ML. These tasks use the same skills (tables, joins, checks) on the new data. Estimated total 30 to 40 hours; do U-01 to U-05 first. Create the folder `worker/agents/` for the agents.

### U-01: Building footprints and types
| Item | Detail |
|---|---|
| Input | OSM buildings for the demo box from HDX: `hotosm_lbn_buildings` (and roads `hotosm_lbn_roads`). Demo box: 35.0–36.0 E, 33.0–33.6 N. |
| Do | Load, keep valid polygons, project to a metric CRS for areas, compute `footprint_m2`, map OSM `building` and amenity tags to `use` (residential, school, clinic, hospital, water, power, other) and `facility_flag`, find the H3 r9 and r8 cell of the centre. |
| Output | `data/local/buildings_base.parquet` and `data/manifests/buildings_base.json` (counts, source date, licence ODbL). |
| Test | Small fixture file: area in square metres is right, ids are unique, every building has a cell. |
| Branch | `feature/u-01-buildings-base` |

### U-02: Building heights
| Item | Detail |
|---|---|
| Input | **3D-GloBFP**, Asia part, Zenodo DOI `10.5281/zenodo.11397015` (grid shapefiles with height in metres; the grid index is in `10.5281/zenodo.11319912`). **GHSL building height** (JRC, 100 m grid). OSM `building:levels` and `height`. |
| Do | Read the licence on the Zenodo page and write it in the manifest (if it is not open, stop and tell Thanoban). Download only the grid tiles that cover the demo box. Match each footprint to a 3D-GloBFP height; if none, take the GHSL cell average; if none, a default by `use`. OSM tags override. Order and rules are in doc 24 section 15. Write `height_low_m`, `height_high_m`, `height_source`, `floors_low`, `floors_high` (height divided by 3 m). Ranges, not single values. |
| Output | `data/local/buildings_height.parquet`, `data/manifests/buildings_height.json` (source of each height, shares per source). |
| Test | Fixture: priority order works; floors are height / 3; low is not above high; every building has a source. |
| Branch | `feature/u-02-building-heights` |

### U-03: Height accuracy check (the 70% target)
| Item | Detail |
|---|---|
| Do | Pick about 30 buildings whose height is known (OSM `height` or `building:levels` tags, towers with published heights). Compare with U-02. Report the share within one storey (3 m) and the average error. Write the result and the limits in a short note. |
| Pass | At least 70% within one storey. If not met, widen the ranges, prefer GHSL or defaults, and say so in the note. This is not a failure of the project; it sets the label shown to users. |
| Output | `docs/progress/BUILDING_HEIGHT_CHECK.md` |
| Branch | `feature/u-03-height-check` |

### U-04: The building table
| Item | Detail |
|---|---|
| Do | Join U-02 with your damage table by `h3_r9` (class, evidence label, second-sensor flag, run id; these are cell results, never building results) and with WorldPop residents (spread the cell's people over residential floor area; low and high). Columns are in doc 24 section 15.1. |
| Output | `data/local/building_table.parquet`, a manifest, and a small published sample `data/published` file produced by `worker.publish` (see U-06). |
| Test | Fixture: residents sum to the cell total; no building gets a damage class the cell does not have. |
| Branch | `feature/u-04-building-table` |

### U-05: The agents (rules and templates first, no language model)
All are plain Python in `worker/agents/`, reading only computed tables, with tests, and returning small JSON. They never invent numbers; missing data is `unknown`.

| Agent | Input | Output |
|---|---|---|
| **Ranking** | incidents from the published `alerts.json`, damage, building table, people, facility and service flags | A ranked list with score 0–100 from the seven named parts in doc 24 section 6.1, weights in a config file, top two reasons, unknowns and data age |
| **Insights** | the ranking and the tables | Short template sentences, each with a source and a date |
| **Decision assistant** | one incident and its area summary | A situation line, 2 or 3 options from fixed playbooks (medical, water, power, evacuation, verification), trade-offs, "what we do not know", a checklist, next review time. Read-only; the officer decides; names itself "CIVISAR assistant" |
| **Budget estimator** | affected floor area (building table) × damage share (destroyed and severe 100%, moderate 50%, possible 20%) × cost per m² range, crew capacity | A low–high cost range and a low–high duration range with the assumptions listed. Label: "Planning indication only" |

Budget inputs: put cost per m² ranges, crew capacity and start delays in `worker/agents/budget_assumptions.json`. **Find a public source for each number** (for example published damage and needs assessments for Lebanon and construction cost indices) and write the source and date next to it. If no source is found, mark the value `assumption` and keep it editable. Ranges of plus or minus 30 to 50% are acceptable.

Tests: ranking shows reasons and unknowns; a part with no data is unknown, not zero; the assistant never prints a number that the tables did not provide; the budget returns a range and lists its assumptions; no text contains "safe" or "confirmed damage".
Branches: `feature/u-05-agent-ranking`, `...-insights`, `...-assistant`, `...-budget`.

### U-06: Publish and the backend endpoints (original roadmap; future work must use the current PostGIS architecture)
| Item | Detail |
|---|---|
| Contract first | Open a PR in `docs/contracts/` adding: `GET /incidents` (ranked list), `GET /incidents/{id}` (with insights and recommendation), `GET /areas/{id}/budget`, and a bulk `GET /buildings?bbox=` (GeoJSON, role and scope filtered, 72 hour gate). Agree it with Rashiru. |
| Do | Extend `worker/publish.py` to write `incidents.json`, `recommendations.json`, `budget.json` and a small buildings file for the visible area. Add handlers in the backend (the registry that Chames is finishing, section 4) reading those files, with the same release and scope gates as the existing published endpoints. |
| Test | Validate responses against the OpenAPI schemas, as in `backend/tests/test_ml_wiring.py`; analyst and officer role limits; withheld before `release_at`. |
| Branch | `feature/u-06-publish-endpoints` |

### U-07: Keys and secrets (read this before deploying)
We will need real keys when we deploy. **Never put a key in Git, in a PR, in chat or in a screenshot.**

| Key (name in `.env`) | What it is for | Who makes it | Notes |
|---|---|---|---|
| `EARTHDATA_TOKEN` | Download NASA data (NISAR, Black Marble) | Each person with their own free Earthdata Login account | Expires about 60 days after it is made. Thanoban's current token ends about 13 January 2027; make a new one when needed |
| `FIRMS_MAP_KEY` | FIRMS history API (optional; the 7-day files need no key) | Thanoban | Free, sent by email |
| `UCDP_ACCESS_TOKEN` | UCDP conflict events API | Whoever registers (Udula or Thanoban) | Free token; or download the CSV instead |
| `SESSION_SECRET`, `DATABASE_URL`, `CIVISAR_DEMO_USERS_JSON` | Backend sign-in and database | Rashiru | Generated locally; never shared |
| `COPERNICUS_USER`, `COPERNICUS_PASSWORD` | Sentinel-2 colour texture (optional) | Whoever uses it | Free account |
| `PUBLISHED_DIR`, `PUBLIC_RELEASE_APPROVED` | **Historical PR #21 settings; not active in current M3** | Rashiru | The JSON directory fallback was not retained, and `PUBLIC_RELEASE_APPROVED=true` cannot enable the hard-suppressed public map. A future replacement must use artifact-bound approval and the review controls above. |

Steps: (1) add every new key **name** (empty value) to `.env.example` in a PR; (2) keep real values only in your local `.env` and in the deploy secret store (GitHub Actions secrets or the server's environment); (3) when a key is made, rotated or about to expire, **tell Rashiru the key name and expiry date, not the value**, so the deploy store is updated; (4) if a key is ever pasted anywhere public, treat it as leaked and make a new one at once. Add a short `docs/progress/KEYS.md` listing names, owners and expiry dates (no values).

## 4. Historical merge instructions for Chames (completed/superseded)

The following instructions record how the PR #21-era JSON handlers were originally intended to be preserved while resolving conflicts. They are not current implementation guidance; the synchronized M3 branch retains PostGIS as authoritative and does not use the JSON Store, `PUBLISHED_DIR` fallback or wildcard scope.

Your three PRs conflict with `dev`, so none can merge: [#18](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/18) (C-01 handler registry), [#19](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/19) (C-02 status and sources), [#22](https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars/pull/22) (C-03 areas, summary, values). All conflict in **one file: `backend/app/api/v1.py`**.

**Why:** the ML wiring PR (#21) was merged into `dev` first. It rewrote handlers in that same file for `/status`, `/public/map`, `/areas`, `/areas/{area_id}/damage`, `/areas/{area_id}/values`, `/alerts` and `/alerts/{alert_id}`, reading real published data through `backend/app/services/published.py`.

**How to fix, in order #18, then #19, then #22 (merge each before starting the next):**

1. `git fetch origin`, then on your branch `git merge origin/dev` (do not rebase over shared history, no force push). Open `backend/app/api/v1.py`; keep **both** sides' intent.
2. **Keep the published-data handlers from `dev` for the endpoints they own:** `/status`, `/public/map`, `/areas` (list), `/areas/{area_id}/damage`, `/areas/{area_id}/values`, `/alerts`, `/alerts/{alert_id}`. Your registry must call `store()` for these, with the same `authorize` checks, area scope filter and release gate. Do not replace them with fixtures.
3. **Use your registry for everything else** (for example `/sources`, `/sources/{id}`, the area summary, and later `/incidents` and `/budget`). Fixtures are only a fallback when no published file exists, and every fixture response must say `synthetic: true`.
4. In #19: `/status` must keep returning the manifest sources from the store; add the `/sources` handlers on top. In #22: the values endpoint is already served from `values.json` (real anomaly scores); keep that, and put your summary logic only on `/areas/{area_id}/summary`.
5. Run before pushing: `ruff check backend worker tests scripts`, `python -m pytest backend worker` (`backend/tests/test_ml_wiring.py` must still pass), `python -m scripts.validate_scaffold`, `python -m scripts.check_secrets`. Fix any test that expected the old 501 or empty response by testing the real behaviour.
6. Push the merge commit to your branch, wait for CI to go green, ask Rashiru to merge. Then update the next branch.

After that, finish your remaining C tasks in [doc 20](20_KISARA_AND_CHAMES_TASKS.md), and take the registry handlers Udula needs for U-06 (agree the names in the contract PR).

## 5. Rashiru

- Review and merge in this order: Chames's #18, #19, #22; the contract PR from Udula; the U tasks.
- Contract PR for the new endpoints (with Udula); update `docs/contracts/` and the typed client in `frontend/src/services`.
- Frontend P0 from doc 24 section 3: bird view toggle (pitch and rotate the MapLibre map, extruded buildings from the building table), fire particle sprite instead of the emoji, the new colour tokens, the ranking list and the assistant panel. Use the Claude Design prototype as the source of truth.
- Update the scope row "No rebuilding" in [PROJECT_PLAN.md](PROJECT_PLAN.md) section 3 (the budget range is adopted), and update the planning manifest hashes if that file changes.
- **Superseded PR #21 deployment instruction:** `PUBLIC_RELEASE_APPROVED` was originally to remain false until human approval. Current M3 is hard-suppressed regardless of that setting; any future publication design requires immutable artifact-bound approval and the additional review controls above.

## 6. Thanoban

- Add to the fire events: confidence, FRP (fire radiative power), time and satellite, so the scene can size the flame; add a lit/dark state per cell to the night-light output. Small changes in `worker/services/`.
- Review U-03 and the agents' wording (the safety words), and write the demo script, video and submission from H38.
- Keep the earlier hand-offs: strike tests on Udula's damage table with UCDP events (the runner already reads the real columns).

## 7. Order and checkpoints

| Step | Who | When |
|---|---|---|
| Fix #18, #19, #22 | Chames | first, today |
| U-01, U-02, U-03 | Udula | next |
| Contract PR for the new endpoints | Udula with Rashiru | before U-06 |
| U-04, U-05 | Udula | then |
| U-06, U-07 | Udula, Rashiru | then |
| Frontend P0 | Rashiru (others help) | as time allows before the freeze at H38 |
| P1 and P2 (three.js scene, 360 camera) | whoever is free after the freeze | after H38 |

## 8. Acceptance checks for this plan

- All three conflicting PRs merged with CI green, and `backend/tests/test_ml_wiring.py` still passes.
- The building table has heights with sources and ranges, and the height check note exists (U-03); the 70% result or the fallback is written down.
- The agents return ranges, reasons, unknowns and data age; no text says "safe" or "confirmed damage"; no number appears that the tables did not provide.
- New endpoints are in the contract, validated against the OpenAPI schemas, role and scope filtered, and withheld before `release_at`.
- `.env.example` lists every new key name with an empty value; `docs/progress/KEYS.md` has names, owners and expiry dates; no key value is in the repository (`python -m scripts.check_secrets` passes).
- Every 3D and budget screen carries the labels "Reconstruction from satellite data, not footage" and "Planning indication only".
