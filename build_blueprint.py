from pathlib import Path
import json, re, hashlib, collections

ROOT=Path(r'D:\My Profission\Nasa Space App\dancing-with-the-sars')
D=ROOT/'docs'
created=[]
def write(name,body):
    p=D/name; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(body.strip()+'\n',encoding='utf-8'); created.append(name)
def table(headers,rows):
    def esc(x): return str(x).replace('|',' / ').replace('\n',' ')
    return '| '+' | '.join(headers)+' |\n|'+ '|'.join(['---']*len(headers))+'|\n'+''.join('| '+' | '.join(map(esc,r))+' |\n' for r in rows)
def doc(name,title,body):
    write(name,f'# {title}\n\n[Blueprint index](README.md)\n\nStatus: implementation blueprint, 14 November 2026. Source observations are the **13 November 2026 snapshot**, not fresh dataset verification. Unestablished implementation choices below are **ARCHITECT RECOMMENDATION (PROPOSED)**. No application or operational dataset was built in this planning task.\n\n'+body)

titles=['SOURCE_AUDIT','REQUIREMENTS_AND_SCOPE','FULL_SYSTEM_ARCHITECTURE','DATA_CATALOGUE_AND_SOURCE_MAPPING','GEOSPATIAL_AND_ML_PIPELINES','BACKEND_DATABASE_AND_API_CONTRACTS','FRONTEND_DESIGN_AND_SCREEN_PLAN','SECURITY_PRIVACY_AND_RBAC','FOUR_MEMBER_TASK_ALLOCATION','48_HOUR_DEVELOPMENT_ROADMAP','TESTING_AND_ACCEPTANCE_PLAN','DEVOPS_DEPLOYMENT_AND_GIT_WORKFLOW','RISK_REGISTER_AND_DECISION_LOG','DEMO_STORY_SUBMISSION_AND_CITATIONS','REQUIREMENTS_TRACEABILITY_MATRIX','TEAM_ONBOARDING']
names=[f'{i:02}_{t}.md' for i,t in enumerate(titles)]
hashes=json.loads((ROOT.parent/'planning-work/source-hashes.json').read_text())

conflicts=[
('D01','Catalogue count','DATASETS.md §1–3: 14','DATA_AND_API_PLAN.md §2–3: 15 (7 NASA, 8 other)','Add GUNW and GHSL; remove unavailable UNOSAT. OCHA is a supporting join asset, not a hidden sixteenth headline source. Keep both inventories. GIBS is NASA-operated but Other provenance.','Recommend 15, pending leader approval','PROPOSED','Member 2','Compare numbered families and terms at H2'),
('D02','Before/after coverage','PROJECT_PLAN.md §5: public data starts June','DATA_AND_API_PLAN.md §1; NASA_DATASET_ANALYSIS.md §2','Without BETA there is no pre-escalation baseline.','151D frame 72; six BETA dates through 19 Jan, first later 24 Jun, eleven later through 3 Nov; no invented 20 Jan–17 Jun passes','VERIFY','Member 1','Re-query ASF by collection, track, frame and actual overlap; save manifest'),
('D03','GUNW availability','DATASETS.md §6: none over Lebanon','DATA_AND_API_PLAN.md §2: 22 BETA + 37 PROVISIONAL; V1 none','Short-baseline products do not span Jan–Jun.','Conditional stretch; verify footprint and paired dates; GSLC cross-gap coherence high risk','VERIFY','Member 1','Inspect pair baselines, phase alignment, noise and decorrelation on quiet controls'),
('D04','Version and season correction','ARCHITECTURE.md §1.3: corrected automatically','DATA_AND_API_PLAN.md §1; NASA_DATASET_ANALYSIS.md §9: consistency test needed','Anomaly training cannot guarantee removal of version or seasonal effects.','Stable-area normalization, registration and incidence/seasonality tests; fail closed to Unknown','PROPOSED','Member 1','Version-stratified quiet hold-out, residual bias and spatial artifact report'),
('D05','Historical lights and fires','DATASETS.md §2: NRT','DATA_AND_API_PLAN.md §2: archive + NRT','NRT rolling retention cannot supply January baseline.','Join archives and NRT with product-quality/version precedence and timestamps','PROPOSED','Member 2','60 clear-night baseline completeness; duplicate archive/NRT test'),
('D06','Height and roads','PROJECT_PLAN.md §6.7: OSM levels','DATA_AND_API_PLAN.md §3: only 0.28% levels, GHSL fallback','Capacity uncertain; public Overpass unreliable.','HDX primary; OSM levels then GHSL 100 m / 3 m then type default; propagate range','PROPOSED','Member 2','AOI coverage audit; no per-building precision claim from 100 m grid'),
('D07','Damage validation','PROJECT_PLAN.md §4–6; DATASETS.md §3: UNOSAT and UNDP','ARCHITECTURE.md §1.2: no usable Lebanon UNOSAT; 2026 UNDP not found','No supervised ground truth or accuracy percentage is established.','No promised UNOSAT overlay. UNDP/CNRS-L exact time/space and permission VERIFY; independent QA if unavailable','BLOCKED','Member 1','Obtain licensed, aligned assessment before validation overlay or precision/recall'),
('D08','Display versus science','NASA_DATASET_ANALYSIS.md §5 expands core datasets','DATA_AND_API_PLAN.md §2–3 narrows them; PDF p2 §4','Extra imagery must not inflate analytical evidence or scope.','GIBS NISAR and DIST-HLS context only; BETA may be blank; document exclusions','PROPOSED','Member 1','Trace numeric inputs to scientific products, never rendered tiles'),
('D09','Web/PWA/offline','UI_DESIGN.md §1, §3.1: installable and saved routes','ARCHITECTURE.md Part 4 and stretch: responsive + print first','Sensitive offline data survives logout.','Web responsive MVP and A4 print; installable public shell stretch; restricted offline briefs/routes post-hackathon pending encryption/revocation design','PROPOSED','Member 4','No service-worker cache of protected responses; logout purge test'),
('D10','Login and public preview','PROJECT_PLAN.md §1: not public app','UI_DESIGN.md §6: login decided, public-safe view','Public preview must not expose sensitive buildings or population concentrations.','Protected roles plus strictly filtered public H3 r8 preview; briefs require sign-in','APPROVED','Member 3','401/403 and object/file/download/print tests'),
('D11','Navigation','PROJECT_PLAN.md §6.5: in-app or phone handoff','UI_DESIGN.md §7: in-app only; DATA_AND_API_PLAN.md §4 local routing','External URLs can leak destinations.','Local graph and in-app static turn list; no external handoff, no GPS tracking','PROPOSED','Member 2','Network egress test; closure revision invalidates selected route'),
('D12','Delay','PROJECT_PLAN.md §10: days','UI_DESIGN.md §5/7 and ARCHITECTURE.md §3.3: 72 h after pass','Delayed publication must cover derivatives and alternate files.','At least acquisition-end +72 h for all newly published strike-related changes; public also r8 and suppression; correction never resets old evidence to evade policy','APPROVED','Member 3','Boundary at 71:59/72:00; cache, tiles, trace and report export tests'),
('D13','Fire satellite label','UI_DESIGN.md §7 mockup S-NPP','DATASETS.md §2; DATA_AND_API_PLAN.md §2 NOAA-20/21','Mock label could misidentify data.','NOAA-20/21 product-specific labels; S-NPP archive only if actually used','PROPOSED','Member 4','SourceRecord satellite equals UI and export'),
('D14','Global and movement','PROJECT_PLAN.md §5/6.8 global watch list','ARCHITECTURE.md Ground rules: one area','Four-person capacity.','South Lebanon MVP; aggregated movement stretch; automatic global watch list and selective processing post-hackathon','PROPOSED','Member 2','No global scanning jobs in MVP; retained backlog'),
('D15','Challenge rules and provenance counts','DATASETS.md intro says 6 tab/tool; §2 marks GIBS Other','PROJECT_PLAN.md §3 says four additional then six; rules claim','The six-source total and official rules are not independently verified.','Count explicit marks: one Tab + four Tab tool = five in current rows; retain claimed six as conflict. Verify current rules; retain exclusion of Chinese-owned data as project constraint','VERIFY','Member 4','Capture Resources-tab/rule evidence and licences at H0; inaccessible here'),
('D16','Stretch after freeze','ARCHITECTURE.md stretch only after H38','ARCHITECTURE.md Timeline: freeze H38','Starting optional features after freeze threatens demo.','Only validated optional work completed before H38 can ship; post-H38 fixes only','PROPOSED','Member 4','Feature inventory frozen at H38'),
('D17','Counts are minimums','PROJECT_PLAN.md §11; ARCHITECTURE.md §1.4','ARCHITECTURE.md §1.3 allows false alarms','Misses do not make an uncertain estimate a rigorous lower bound.','Report candidate ranges and false positives/negatives; no guaranteed lower-bound claim','PROPOSED','Member 1','Sources page uncertainty review'),
('D18','Coherence and source breadth','NASA_DATASET_ANALYSIS.md §5 calls GSLC/GUNW, DSWx, POWER core','ARCHITECTURE.md tiers and DATA_AND_API_PLAN.md §3 drop/defer','Earlier investigation is broader than final weekend budget.','GCOV core; GSLC/GUNW conditional; broad environmental science backlog excluded from demo','PROPOSED','Member 1','Tier budget and exclusion ledger review at H2'),
]
conflict_table=table(['ID','Topic','Source A + section','Source B + section','Impact','Recommended decision','Status','Owner','Validation'],conflicts)
doc(names[0],'Source audit',f'''
## Scope and reading record

All six Markdown references were read in full, including tables, caveats and open items. Both PDF pages were text-extracted with pypdf and rendered with Poppler and visually inspected. Page 1 is the six-portal directory plus ASF links; page 2 continues access links, has a five-row priority table and five practical notes. No additional scientific chart or hidden map appeared. Poppler warned about Symbol/ArialUnicode fonts; visible text and the table remained readable. The original slide mentioned in the PDF was not supplied and was not claimed as reviewed.

{table(['Reference','Audit','SHA-256'],[(k,'READ; PDF both pages visually inspected' if k.endswith('.pdf') else 'READ completely',v) for k,v in hashes.items()])}

No mandatory reference is missing. Original documents remain unchanged. Conflicting scientific observations are source-reported, not independently validated. ARCHITECT RECOMMENDATION identifies additions; APPROVED below means explicit user requirement or recorded source decision, not fresh scientific certification.

## Repository and network reality

Repository: `dancing-with-the-sars`; original branch `docs/architecture-plan`, original HEAD `022599111ea437b62bf297851e0109f08cde94d8`; clean tracked and untracked state. Remote `https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars.git`. Detected default via `origin/HEAD`: `main`, fetched SHA `e99348c0aec238b4d4252f02001560f6f18d1fc7`. No AGENTS.md found in repository or accessible workspace ancestors. No application code, dependencies or tests existed: root README plus seven references only.

Git was absent from PATH but found at `C:/Program Files/Git/cmd/git.exe`. Initial fetch failed under sandbox; explicitly escalated retry succeeded. Planning branch created from origin/main, then fast-forwarded the two existing architecture commits from the original branch so ARCHITECTURE.md is retained with its history. No branch reset, deletion, reference edit, default-branch merge or bulk download occurred. Upstream to origin/main was removed from the new planning branch to avoid accidental push targeting.

External browse attempts: Claude UI mockup, Space Apps 2026 Resources tab, ASF NISAR documentation returned inaccessible via browser tool. Therefore exact token values in the remote mockup, current competition rules and new official product checks remain VERIFY. No CMR/ASF dataset query, FIRMS authenticated call, acquisition, deployment or scientific validation was executed. URLs in the source documents were read as references; reachability of all links was not tested. The 13 Nov snapshot is preserved, including unverified July/Aug outage and pre-21-Oct provisional claims. Recheck per-granule metadata instead of assuming date implies version.

## PDF practical rules

PDF p1 §1: Open Data is a metadata catalogue, API portal authentication varies, Earthdata filters by place/time, Worldview is context, Exoplanet Archive irrelevant, NASA Open is open-science information. PDF p1–2 §2: ASF Vertex/Search for SAR discovery, Earthdata Login for protected files, GIBS for web imagery, EONET natural-event context.

PDF p2 §3 priority order: ASF → Earthdata Search → Worldview/GIBS → Open Data catalogue → relevant general NASA APIs. PDF p2 §4: check service-specific auth/rate limits; GIBS is visualization, not analytical evidence; use NISAR product workflows instead of assuming api.nasa.gov; record dataset name/level/acquisition/version/coverage/terms/URL; never publish sensitive shelters or identifiable population concentrations. These rules are independently enumerated in [traceability](14_REQUIREMENTS_TRACEABILITY_MATRIX.md).

## Source discrepancies

{conflict_table}

## Reverification protocol

Member 1 saves metadata-only ASF/CMR query parameters, response time, collection IDs, counts, overlaps, track/frame and checksums at H0. Member 2 checks licences, dates, coverage, archives, GHSL units and humanitarian reports. Member 3 verifies credentials without recording secrets and local route isolation. Member 4 verifies challenge rules and mockup accessibility. Unavailable data remains Unknown or visibly synthetic; it cannot silently become a verified result.
''')

# Catalogue: each record is split across linked matrices so all requested fields remain readable.
datasets=[
('DS01','NISAR GCOV/GSLC','NASA/ISRO, ASF','Tab','LB 151D/72; 172A and 100A secondary','12-day nominal; actual gaps','36–72 h source estimate; VERIFY','BETA 1.0.2 / PROVISIONAL 1.0.11 / V1 per manifest','linear backscatter → dB; GSLC complex phase','ASF/CMR + earthaccess','Earthdata Login','NASA ESDIS citation; verify each version','Mixed processing, long gap, incidence and season','Each acquired pass, precompute','HH/HV change; candidate damage','Damage','restricted r9; delayed suppressed r8','raw HDF5; cropped COG; cells','z-score on valid GCOV; no imagery substitution','M1-01'),
('DS02','NISAR GUNW','NASA/ISRO, ASF','Tab tool (proposed classification)','LB footprint VERIFY by pair','12/24-day pairs','VERIFY','BETA and PROVISIONAL; no V1 LB in snapshot','coherence 0–1; phase radians (metadata verify)','ASF/CMR + earthaccess','Earthdata Login','NASA guidance, per-product verification','22 BETA + 37 provisional reported; no cross-gap pair','Conditional per pass','optional coherence','Damage','restricted','private rasters and paired manifest','omit feature; retain GCOV','M1-04'),
('DS03','OPERA RTC-S1','NASA OPERA / ESA / ASF','Tab tool','LB; global mission coverage per burst','few days, actual acquisitions','latest snapshot 10 Nov 2026','V1 plus burst processing version','backscatter; normalize per product metadata','ASF + earthaccess','Earthdata Login','NASA citation + Copernicus terms VERIFY','30 m spec; C/L-band differences','Optional pass check','Sentinel-1 change','Damage; Alert','restricted detailed products','COG and cross-sensor QA','document unavailable; no fabricated agreement','M1-04'),
('DS04','Black Marble archive + NRT','NASA LAADS/LANCE; NOAA-20/21','Tab tool','LB crop; global product','daily','NRT rolling ~8 days; archive A2 ~16-day lag source report','VJ146A2/VJ246A2; granule version required','radiance units from scientific metadata; ratio dimensionless','CMR + earthaccess','Earthdata Login','NASA use/citation VERIFY','~500 m; clouds/moon/gap-fill; no building-level power certainty','Daily; 60 clear-night baseline','night lights; possible power loss','Services; Alert; Movement','aggregated services; restricted facility links','private raster + area statistics','last good Cached; insufficient clear nights → Unknown','M2-03'),
('DS05','FIRMS VIIRS archive + NRT','NASA FIRMS/LP DAAC; NOAA-20/21','Tab tool','LB AOI; global coverage','several overpasses/day','NRT; observed API latency VERIFY','VJ114IMGTDL_NRT/VJ214IMGTDL_NRT + VJ114IMG archive','point detection, confidence, FRP unit from product','FIRMS area API; CMR archive','server MAP_KEY; Earthdata for files','NASA citation and API limits VERIFY','375 m spec; false/permanent hotspots; not strike attribution','Every 30 min; archive history','fires; alerts','Alert; Services; Corroboration','precise proximity restricted','observations and clustered GeoJSON','Cached recent feed; no recent signal ≠ no fires','M2-03'),
('DS06','NASADEM_HGT','NASA LP DAAC','Tab tool','2–3 tiles over AOI VERIFY','static','none; historical baseline','product/granule version from metadata','elevation m; derived slope degrees','CMR + earthaccess','Earthdata Login','NASA guidance VERIFY','30 m spec; terrain not building stability','Once; source revision','internal slope constraint','Shelter; Route','restricted derived site scores','cropped DEM/slope','open land Unknown if DEM absent','M2-01'),
('DS07','GIBS display families','NASA GIBS/Worldview','Other (PDF), even though NASA-operated','layer-specific AOI and dates','layer-specific daily/static','layer-specific VERIFY','WMTS capability identifier, style and time','rendered pixels; never numerical evidence','WMTS capability and tiles','none per source','layer-specific attribution and caching terms VERIFY','BETA NISAR blank in source check; resolution varies','Capabilities preflight; chosen display date','backgrounds and context','none (presentation)','public approved background; restricted view proxy','bounded cached display tiles','neutral local background with provenance notice','M4-01'),
('DS08','HOTOSM buildings/roads + bounded Overpass','OpenStreetMap/HOT/HDX','Other','Lebanon exports, AOI crop','edits live; export monthly source estimate','export timestamp required','resource revision/OSM timestamp','geometry m² after projection; tags/levels','HDX CKAN primary; small Overpass fallback','none source-reported','ODbL attribution/share-alike implications VERIFY','missing levels, roads and facility status; 0.28% levels source snapshot','Once demo; refresh on export revision','buildings/facilities/roads','Facility; Route; Shelter','critical sites/roads restricted','private GeoPackage/PostGIS/PMTiles','synthetic graph; type-default levels labelled','M2-01'),
('DS09','GHSL building height','European Commission JRC','Other','100 m tile covering AOI VERIFY','epoch static','not current individual building measurements','height product release/epoch VERIFY','m; height / 3 m illustrative floor estimate','JRC download, tile and metadata','access VERIFY','JRC product licence and citation VERIFY','pixel average cannot determine a building floor count','Once demo','capacity input, no public site layer','Shelter; People','restricted derivatives','private height raster, uncertainty flags','type default low/high; do not invent certainty','M2-01'),
('DS10','WorldPop R2025A 2026 + demographics','WorldPop','Other','Lebanon 100 m proposed product VERIFY','annual; age/sex may differ','publication-dependent','R2025A / 2026 source proposal; confirm release','people per pixel; age/sex ranges','WorldPop REST/download','none source-reported','product-specific licence VERIFY','pre-displacement baseline, not people currently present','Once per release','population and affected ranges','People; Report','no identifiable public concentrations','private raster and aggregated values','Unknown demographics if not aligned; never old age data as current','M2-02'),
('DS11','UNDP / CNRS-L assessments','UNDP and CNRS-L','Other','Lebanon exact overlap and dates VERIFY','event assessment','unknown','assessment publication and survey period VERIFY','reported damage categories','publisher/HDX if obtainable','licence/access VERIFY','permission and redistribution VERIFY','No usable 2026 reference found in architecture check','Only after verified acquisition','analyst validation overlay','Damage (check only)','licensed restricted report/geometry','private report and aligned comparison','quiet hold-out/manual QA; no accuracy claim','M1-03'),
('DS12','ACLED','ACLED','Other','Lebanon, authorized subsets','weekly source cadence','publication delay VERIFY','dataset extract date','reported events; location precision','ACLED API or permitted HDX export','account credentials server-only','ToS must authorize planned use; raw redistribution blocked pending review','approximate event location; strike ≠ collapse','Weekly; context snapshot sufficient demo','restricted conflict context; future watch list','Corroboration; Alert','restricted reports; no tactical/military fields','private filtered event table','omit raw events; quiet sampling caveat if absent','M2-03'),
('DS13','IODA v2','Georgia Tech IODA','Other','LB, South Lebanon/An Nabatiyah identifiers VERIFY','near-real-time source claim','observed lag VERIFY','endpoint and response version','outage metric native units; regional status','IODA v2 API','none source-reported','API use/attribution VERIFY','regional availability ≠ a facility connection','Every 30 min','internet disruption','Services; Alert','regional aggregate','raw bounded response and normalized status','last-good Cached; no inference at building scale','M2-03'),
('DS14','IOM DTM + Meta Movement Distribution Maps','IOM / Meta via HDX','Other','Lebanon spatial support/coverage VERIFY','DTM weekly; Meta every 2 weeks source claim','publication lag VERIFY','report period / resource revision','aggregate people and movement index; never individual','DTM API / HDX CKAN','DTM key; HDX none source-reported','Meta source says CC BY; confirm exact licence and DTM terms','sampling, aggregation and displacement gaps','Stretch periodic import','coarse delayed movement','Movement; People','sensitive displacement, no exact camps','private coarse tables; sanitized trend only','Unknown; retain static baseline','M2-06'),
('DS15','Insecurity Insight','Insecurity Insight via HDX','Other','Lebanon report geometry/precision VERIFY','weekly to monthly','report lag VERIFY','aid-security-risk-in-lebanon revision','reported incidents, facility attacks','HDX CKAN / permitted export','none source-reported','dataset licence, disclosure restrictions VERIFY','reporting bias, approximate positions; duplicate reports possible','Bounded demo snapshot; periodic refresh later','reported attacks/corroboration','Facility; Corroboration','restricted; remove military/frontline details','private normalized reports','omit unavailable; no corroboration upgrade','M2-03'),
('A01','OCHA admin and cadasters (support asset)','OCHA/HDX','Other','Lebanon: 8 governorates/26 districts/1,627 cadasters source claim','static revisions','VERIFY','boundary dataset/revision VERIFY','polygon boundaries and stable codes','HDX CKAN resource','none source-reported','resource-specific terms VERIFY','boundary versions and overlaps; retain fractional joins','Once','area/admin joins','People; Report','public admin geometry allowed after review','PostGIS + area crosswalk','H3 only with unknown admin code','M2-01'),
('A02','NISAR_COP (optional support)','NASA/ISRO, ASF','Tab tool proposed','future AOI coverage must be intersected','updated observation plan','~9 days ahead in snapshot','plan publication/version','scheduled time, track/frame','CMR/ASF metadata','none search; file auth VERIFY','NASA guidance VERIFY','schedule not a guarantee of acquisition','Stretch refresh','next pass note','Orchestrator','public generalized schedule after review','plan manifest','show schedule unavailable','M1-04'),
('X01','UNOSAT Lebanon damage (current catalogue only)','UNOSAT/HDX','Other','No usable LB dataset found in supplied checks','event-specific','not available','not known','damage classes if actually available','HDX discovery only','VERIFY','VERIFY before reuse','not a promised validation source','Recheck once H0','none until approved availability','Damage (validation only)','restricted if obtained','no fictitious files','DS11 conditional or independent model QA','M1-03'),
]
cmr={
'DS01':'GCOV BETA C3622214170-ASF; PROVISIONAL C2854338529-ASF; V1 C3622241360-ASF. GSLC BETA C2850259510-ASF; PROVISIONAL C2854332392-ASF; V1 C3622244601-ASF',
'DS02':'BETA C2850261892-ASF; PROVISIONAL C2854335566-ASF; V1 ID not supplied, no invention',
'DS03':'C2777436413-ASF','DS04':'archive VJ146A2 C3370789118-LAADS; VJ246A2 C4320924614-LAADS; NRT C4193331158-LANCEMODIS and C4249684820-LANCEMODIS',
'DS05':'NRT C3264430167-LANCEMODIS and C4377939055-LANCEMODIS; VJ114IMG archive C2734197957-LPCLOUD','DS06':'C2763264762-LPCLOUD','DS07':'GIBS is WMTS; underlying DIST-ALERT-HLS C2746980408-LPCLOUD','A02':'C2727904608-ASF'}
doc(names[3],'Data catalogue and source mapping',f'''
## Inventory policy

Sources: DATASETS.md §§1–7; DATA_AND_API_PLAN.md §§1–5 (proposal); NASA_DATASET_ANALYSIS.md §§0–9; PDF pp1–2. Current numbered 14: NISAR, OPERA, Black Marble, FIRMS, NASADEM, GIBS, HOTOSM, WorldPop, UNOSAT, UNDP/CNRS-L, ACLED, IODA, IOM+Meta, Insecurity Insight. Proposed 15: DS01–DS15 below. A01/A02 are separately disclosed supporting/optional assets; they are not hidden additions to the claimed family count. A list of product variants is not a count of independent datasets.

The recommended 15-family baseline is **PROPOSED**, not a replacement of DATASETS.md. Seven NASA-operated families does not mean seven directly linked challenge resources. The original count of six tab/tool families conflicts with explicit marks (D15). No collection, API or licence was live tested in this task. All rows: **live tested here = No**; previous check claims are only the dated sources. Metadata known from the supplied proposal is copied below, never invented.

## Identity, coverage, time and measurement matrix

{table(['ID','Provider / family','Challenge mark','Extent','Temporal resolution','Latency','Version','Unit'],[(x[0],x[2]+' / '+x[1],*x[3:9]) for x in datasets])}

## Access, rights and quality matrix

{table(['ID','Download','Credentials','Licence/terms status','Quality limit','Update schedule','Live tested here'],[(x[0],*x[9:14],'No') for x in datasets])}

## Consumption, security and storage matrix

{table(['ID','Layer','Function','Sensitivity','Local storage','Fallback','Owner task'],[(x[0],*x[14:]) for x in datasets])}

## CMR identifiers from DATA_AND_API_PLAN.md §2

{table(['Family','Identifiers'],cmr.items())}

Unlisted non-NASA CMR IDs: not applicable. Unknown product versions stay null/VERIFY until ingestion. Each downloaded granule records acquisition start/end, file URL, access time, product level, processor CRID (source examples X05010/P05023/P05036), CRS, units, nodata, pixel size, coverage, checksum and terms snapshot.

## API adapter register

| Adapter | Source URL / access | Credential and bounding rule | Owner / fixture |
|---|---|---|---|
| ASF Search | https://api.daac.asf.alaska.edu/services/search/param | no search key; AOI/date/track/frame/collection; paginate and dedup | M1-01 / metadata-only scene |
| CMR Search | https://cmr.earthdata.nasa.gov/search/ | no search key; concept IDs and time/extent; retain pagination evidence | M1-01 / granule manifest |
| earthaccess / Earthdata Login | https://urs.earthdata.nasa.gov/ | each member's account; server token; no shared secret | M1-01 / download skipped in fixtures |
| FIRMS | https://firms.modaps.eosdis.nasa.gov/api/ | MAP_KEY env; AOI/window bounded; redact key from path/logs | M2-03 / fire response |
| GIBS WMTS | https://gibs.earthdata.nasa.gov/ | no key; verify capabilities, matrix, time, resolution | M4-01 / cached background |
| HDX CKAN | https://data.humdata.org/api/ | package/resource version; permitted download URLs allowlist | M2-01 / package metadata |
| WorldPop REST | https://www.worldpop.org/rest/data | bounded country/year; check raster units and release | M2-02 / population crop |
| IODA v2 | https://api.ioda.inetintel.cc.gatech.edu/v2/ | no key per source; region code and bounded window | M2-03 / regional outage |
| ACLED | canonical endpoint/auth from account docs, VERIFY | server-only account; no undocumented URL assumed | M2-03 / synthetic event |
| IOM DTM | endpoint/version from key documentation, VERIFY | key env; coarse region/period only | M2-06 / aggregate |
| Overpass | selected public instance VERIFY | tiny bounded query only; no bulk Lebanon query, no routing | M2-01 / OSM extract |
| Local routing | internal Python callable or private OSRM | no internet destination request, egress denied | M2-04 / synthetic graph |

No generic api.nasa.gov download assumption. PDF p2 §4 requires current auth and rate-limit checks per service. Requests use bounded retries/backoff, Retry-After, timeouts and last-good fallback; M3 owns scheduling, M2 owns adapter parsing/science.

## GIBS display registry

MVP contexts: `VIIRS_NOAA20_GapFilled_BRDF_Corrected_DayNightBand_Radiance`, `VIIRS_NOAA21_GapFilled_BRDF_Corrected_DayNightBand_Radiance`, `VIIRS_NOAA20_Thermal_Anomalies_375m_All`, `VIIRS_NOAA21_Thermal_Anomalies_375m_All`, `HLS_S30_Nadir_BRDF_Adjusted_Reflectance`, `Reference_Features`, `Reference_Labels`. Proposed optional additions: `NISAR_L2_Geocoded_Polarimetric_Covariance`, `OPERA_L3_DIST-ALERT-HLS_Color_Index`, `OPERA_L2_Radiometric_Terrain_Corrected_SAR_Sentinel-1` and `IMERG_Precipitation_Rate` for visual rain confounders. Validate exact capabilities and dates; no BETA backdrop assumed. `VIIRS_Black_Marble` ends at 2016 in the source and is not current night-light evidence. Never calculate severity, capacity or population from rendered GIBS pixels.

## Licence, citation and retention register

For every ID, M2 records licence name/version/URL, rights holder, attribution text, permitted derivative sharing, redistribution, expiry and restrictions in SourceRecord. NASA/Copernicus/OSM obligations are recorded separately, not erased by combining data. ACLED/DTM/Meta/assessment terms remain VERIFY; hide unapproved raw layers and exports. Publication requires source_url, dates, version, coverage and access date. All sensitive values use the retention policy in [security](07_SECURITY_PRIVACY_AND_RBAC.md); no licence uncertainty is interpreted as permission.

## Exclusion and conditional backlog ledger

See [dataset exclusions](03A_DATASET_EXCLUSIONS.md) for every source-listed alternative, including investigation items called Core but omitted by the narrower proposal. This is an auditable decision, not permission to expand the demo.
''')

exclusions=[
('Conditional stretch','RSLC; NISAR_DEM; NISAR_WATERMASK; Sentinel-1C/1D SLC','NASA_DATASET_ANALYSIS.md §3.1','Same-processor reprocessing and extra masks/coherence exceed weekend budget; permit only validated, scoped experiment.'),
('After hackathon','NISAR SME2; SMAP SPL3SMP_E / SPL4SMGP; SMAP_L4 display','NASA_DATASET_ANALYSIS.md §§3.1/3.10/4; DATASETS.md §6','Wet-ground regional support; not validated site safety; narrower source drops SMAP.'),
('Excluded current coverage','OPERA DIST-ALERT-S1; CSLC-S1; DISP-S1; ARIA S1 GUNW; NISAR UR L1/L2; GOFF; RIFG; ALOS-2 PSR2','NASA_DATASET_ANALYSIS.md §§3.1/6','Stale Jan–Feb, no current coverage or no granules in snapshot; re-query before future use.'),
('After hackathon analytical; GIBS context only now','HLS L30/S30 downloads; HLS VI; DIST-ALERT-HLS; DIST-ANN-HLS; MOD13Q1; VNP13A1','NASA_DATASET_ANALYSIS.md §3.2; DATASETS.md §6','Optical/cloud QA and livelihoods extend scope. DIST-HLS display is optional, not a new analytical promise.'),
('After hackathon experimental','EMIT L2A reflectance; GEDI L2B v003; ICESat-2','NASA_DATASET_ANALYSIS.md §§2/3.2/5/9','Material/height samples uncertain over individual buildings; GHSL is the proposed coarse fallback.'),
('Conditional backup or historical only','VJ146A1/A1_NRT; VJ246A1_NRT; VJ146A3; VNP46A3; VNP46A1/A2','NASA_DATASET_ANALYSIS.md §3.3','Uncorrected/monthly products are not interchangeable with daily corrected A2; S-NPP source says ended 2 Nov.'),
('After hackathon','MCD14DL; MCD64A1; VNP64A1; VNP14IMG','NASA_DATASET_ANALYSIS.md §3.4','Additional fire/burn history beyond selected NOAA-20/21 VIIRS; independence cannot be assumed.'),
('After hackathon regional context','TROPOMI NO2/SO2/CO/Aerosol Index; TROPOMAER; MCD19A2 MAIAC; AERDB VIIRS Deep Blue; OMPS SO2; MERRA-2 M2T1NXAER; AIRS layers','NASA_DATASET_ANALYSIS.md §§3.5/4/6','Regional smoke/pollution, not individual strikes; latency and attribution confounders.'),
('Excluded geography','TEMPO','NASA_DATASET_ANALYSIS.md §§3.5/6','North America only in source.'),
('After hackathon; visual rain context optional','DSWx-S1/HLS; SWOT LakeSP/Raster; VJ128C2; GPM IMERG Early/Late; EONET floods','NASA_DATASET_ANALYSIS.md §3.6; DATA_AND_API_PLAN.md §3','Investigation calls some Core; narrower catalogue drops them. Natural-event context only; no general-disaster scope.'),
('After hackathon, mainly Gaza','PACE OCI L2 BGC/AOP; VIIRS ocean colour; Sentinel-1A GRD-H; OCI_PACE_Chlorophyll_a; VIIRS_NOAA20_Chlorophyll_a','NASA_DATASET_ANALYSIS.md §§3.1/3.7/4','Coastal/sewage/oil use is beyond south-Lebanon demo; PACE latency unresolved.'),
('After hackathon experimental / exclude coarse inference','EMIT L2B CH4; TROPOMI CH4','NASA_DATASET_ANALYSIS.md §3.8','Sparse methane samples and coarse regional measurements do not establish damaged pipes.'),
('After hackathon','NASA POWER; MOD11A1; VJ121A1D; ECOSTRESS L2T LSTE/L4T ESI; MERRA-2 M2T1NXSLV; heat GIBS layers','NASA_DATASET_ANALYSIS.md §3.9; DATASETS.md §6','POWER called Core in investigation but dropped in final catalogue. Climate mode manually selected and labelled; no inferred weather safety.'),
('Alternative terrain / deferred','SRTMGL1; ASTER GDEM; MCD12Q1; IMERG+LHASA; terrain GIBS','NASA_DATASET_ANALYSIS.md §§3.10/4','NASADEM selected; coarse land-cover/landslide context is not site verification.'),
('Historical cross-check only; not current people','GPWv4 count 2020; GPWv4 age/sex 2010; GRDI; SEDAC GHSL 2014/2015; HBASE; GMIS; gROADS; dLIGHT','NASA_DATASET_ANALYSIS.md §§3.11/6; DATASETS.md §6','Old baselines; distinguish SEDAC GHSL from JRC building-height product. Never substitute for current vulnerability counts.'),
('Excluded or coverage/access VERIFY','SAOCOM; RCM; RADARSAT-1','DATASETS.md §6','Registration/unconfirmed coverage or no open Lebanon data in source.'),
('Learning only','Intro to Remote Sensing; Intro to SAR; NASA ARSET; NISAR StoryMaps; Applications White Papers; UAVSAR Postcards; CSA SAR Python tutorial','DATASETS.md §6','Challenge-linked educational resources, not analytical datasets.'),
('Excluded tools/duplicates','AppEEARS; Giovanni; NASA SVS night-lights story','DATASETS.md §6','Not necessary analytical inputs; use selected direct products.'),
('After hackathon / outside source baseline','Sentinel-2; ERA5; FAO GAEZ; KNMI; NOAA CDO; US-only datasets','DATASETS.md §6','Other challenge sources, scope/geography mismatch; no unrelated dataset bloat.'),
('Access-limited post-hackathon','WHO HeRAMS; WHO attacks database; UNMAS; Logistics Cluster; Pacific Institute; HDX HAPI; UNHCR; healthsites.io','DATASETS.md §6; NASA_DATASET_ANALYSIS.md §1','Not assumed accessible; OSM covers inventory only. UXO cannot be observed from space; real protection/ordnance checks remain mandatory.'),
('Excluded unrelated APIs','Exoplanet Archive; NASA Open; APOD; NeoWs; DONKI; Mars/InSight; GeneLab; Techport; Image Library; EPIC','NASA_DATASET_ANALYSIS.md §6; PDF p1 §1','Not relevant measurement data; EPIC too coarse; NASA Open remains informational.'),
('Excluded current service / stale','api.nasa.gov Earth imagery; EONET manmade; GPCP daily','NASA_DATASET_ANALYSIS.md §6','Source reports 503, 2018 newest manmade, Dec 2025 endpoint respectively; not freshly rechecked.'),
('Prohibited all phases','Chinese-owned sources; live vehicle/phone/convoy tracks; military/frontline information','DATASETS.md §6; PROJECT_PLAN.md §10','Project constraints retained; official competition rule independently VERIFY.'),
]
doc('03A_DATASET_EXCLUSIONS.md','Dataset exclusions and deferred investigations',table(['Decision/phase','Datasets or resources','Source section','Reason and re-entry condition'],exclusions)+'\n\nEvery individual scientific table row is also retained in the source-by-section traceability ledger, including source counts and dates. Nothing in this list is claimed downloaded or tested here.')

doc(names[4],'Geospatial and ML pipelines','''
## Shared contracts and CRS

Sources: ARCHITECTURE.md Shared by all parts, §§1.1–1.6/2.1–2.4; PROJECT_PLAN.md §§6/8/9; NASA_DATASET_ANALYSIS.md §§2/8/9. Canonical numeric row: `area_id, metric, low, high, unit, label, source, date, safety_tag`. Proposed extensions: `value_id, lineage_ids, processing_run_id, processing_version, confidence, acquired_at, processed_at, freshness, cached, limitations, release_at, synthetic`. See [MetricValue](contracts/MetricValue.json).

ARCHITECT RECOMMENDATION: H3 IDs are lowercase hexadecimal strings with explicit resolution, not numeric JavaScript values. Use actual r9→parent r8 aggregation; cadaster intersections can be fractional and many-to-many. Preserve WorldPop total mass during resampling/area joins. CRS 4326 stores API GeoJSON and DB geography; local metric operations use EPSG:32636 for this AOI after checking source CRS. Raster processing retains source CRS until deliberate reprojection; use nearest for categorical masks and documented continuous-data resampling. Never measure metres in longitude degrees or silently equate pixel posting with resolution.

## Discovery, tiers and reproducible ingestion

M1 searches all three product versions on 151D/72. Source snapshot: BETA before through 19 Jan 2026; no acquisitions 20 Jan–17 Jun; first relevant after 24 Jun; eleven later passes through 3 Nov. Preserve actual timestamps, duplicate product versions and missing passes. A swath touching AOI does not prove complete usable overlap. Re-query and inspect valid-pixel footprint.

Tier A: six before GCOV (27 Oct–19 Jan) + three after (24 Jun–18 Jul), ~7.7 GB. Tier B: eight later (11 Aug–3 Nov), ~6.8 GB. Tier C conditional: GSLC Jan19/Jun24 plus Jan7 GUNW, ~15 GB. These sizes are source estimates, not measured here. Download only when development begins and challenge preparation rules are verified. Metadata/search/checksum first, crop immediately, share cropped derivatives, never commit raw granules.

Each run key hashes dataset versions + AOI + acquisition IDs + parameters + software revision. Save manifest and checksums, terms and retrieval dates. Download temporary file, verify size/checksum, atomically promote. Reprocessing with identical key is idempotent. Failed QA cannot update published pointers. Retain previous approved artifact set for rollback.

## Radar algorithm and failure gates

1. Validate HH/HV availability, linear/covariance semantics, band, calibration, incidence and matching track/frame; reject unsupported products. Clip AOI to common valid coverage. Detect nodata, NaN, zero/negative values before log conversion. `10*log10(power)` only when metadata establishes power; GSLC amplitude would require its own conversion.
2. Co-register using stable, distributed controls; record residual offsets. Mask water, shadow and steep slopes as Unknown. Proposed registration gate: residual median ≤0.5 output pixel and p95 ≤1 pixel on independent controls; threshold is engineering recommendation to validate, not source fact.
3. BETA 1.0.2 versus PROVISIONAL 1.0.11: fit stable-area normalization on training controls only, report before/after residuals by incidence and building density, evaluate independent stable controls. Test moisture/seasonality and noise-floor effects. Quiet-model training does not automatically eliminate calibration differences. If systematic bias/artifacts remain, mark comparisons scientifically blocked.
4. Document whether temporal aggregation averages linear power then converts to dB or averages dB. ARCHITECT RECOMMENDATION: mean calibrated power over valid dates, then dB; compare sensitivity to median/dB mean. Source says average six before/three after but does not fix this choice. Store valid-date/pixel counts.
5. Per r9 built-up cell: HH and HV dB differences; change in HH−HV; share of valid built-up pixels with HH drop >3 dB; incidence angle; building density; optional validated coherence drop. Reason codes include strong_hh_drop, hv_shift, polarization_shift, other_change, low_coverage, version_confounded.
6. Quiet sampling excludes reported ACLED/Insecurity Insight events within 2 km during Jan19–Jun24. Missing reports do not prove quiet. If fewer than ~500 cells, expand within frame only after source rights and controls review. Use spatial blocks: 80% training, 20% untouched hold-out; normalization and thresholds use training only. Store seed, blocks and leakage checks.
7. Isolation Forest primary, Robust Mahalanobis/MinCovDet comparison; z-score fallback on the same versioned feature contract if model setup fails. Record hyperparameters and feature scaling. Anomaly plus HH decrease (or separately validated coherence decrease) gives candidate damage; opposite-direction anomaly is other change. Null or failed QA is Unknown, not no damage.
8. Source candidate thresholds are training quiet-score quantiles: >95% possibly damaged, >99% moderately damaged, >99.9% destroyed/severely damaged candidate. These are provisional anomaly classes, not calibrated probabilities or proof of collapse. Do not invent separate destroyed versus severe labels when features cannot distinguish them. Report sample-size limits: ~500 controls cannot support a reliable 0.1% tail estimate.
9. Refit later-pass comparison against June baseline as source directs; store per-pass model/version and threshold so scores are not mistaken for directly comparable probabilities. Keep Jan→Jun and June→later comparisons distinct in UI. Publish r8 area results only after delay and suppression; building inference remains restricted candidate information.

## Model validation

T-ML: spatial hold-out false-alarm rate at 99th-percentile training threshold, target around 1% from source; report denominator and uncertainty interval, not guaranteed performance. ARCHITECT RECOMMENDATION: H32 science gate requires a predeclared acceptable interval after sample-size assessment at H2; report observed rate even on failure. Strike-context enrichment compares near/far and within district, with building density/incidence controls and location uncertainty buffers; association is not collapse ground truth. Inspect 20 top-change cells and some unflagged controls, logging strips/edges/shadow/vegetation alternatives. Cross-sensor agreement uses OPERA only if aligned and independent; no claimed accuracy without dated spatially matched ground truth. Retain failed tests on Sources.

T-COHERENCE: GUNW BETA/PROVISIONAL supplies short-baseline 12/24-day coherence, not a Jan–Jun pair. Cross-gap GSLC needs expert coregistration/phase assessment, matching bands, stable-area controls, baseline analysis and decorrelation attribution. Seasonal decorrelation can dominate; comparing short versus long baselines is confounded. If invalid or late, exclude coherence entirely from model and disclose that limitation.

## Humanitarian computations

Residents: WorldPop is a pre-displacement baseline. Allocate counts to residential floor-area weights only with mass-conservation checks and coverage flag; if building data incomplete, retain cell total and broaden uncertainty. Vulnerability counts need aligned age/sex data and date; missing groups are Unknown. Ranges are scenarios from input uncertainty, not statistical confidence intervals unless measured.

Affected/displaced: sum resident allocations weighted by candidate shares. Source scenario factors: destroyed/severe 1.0, moderate 0.5, possible 0.2. Label as potentially affected/displaced scenario; do not imply observed displacement. Avoid counting the same residence twice across classes/passes. Report low/high sensitivity to class/occupancy assumptions. IOM reports remain separate Reported evidence with their period.

Severity: show all five parts (damage, residents, critical facilities hit, service loss, roads cut). ARCHITECT RECOMMENDATION: normalized equal-weight exploratory rank only when all five inputs present; otherwise show partial profile and no composite rank. Team must approve weights; never hide missing inputs as zeros.

Facilities: HOTOSM type/inventory is not operating status. A dated verified report supports “Reported operating”; without it use “No detected damage. Not confirmed open.” Reported attack is not automatically damage. Nearest working hospital requires both a current credible operating report and route caveats; otherwise return Unknown.

Services: night-light decrease is possible power loss, not blackout. Water dependency requires reported/verified network relationship; satellite-observed proximity alone cannot prove substation→pump→hospital dependency. What-to-bring mapping uses source rules (water, generators/lights, medical team, radios); no invented counts, supply volumes or medical advice. Report output preserves weakest-input uncertainty.

## Alerts, cadence and corroboration

Black Marble: QA-clear nights only, use archives for 60-night baseline; keep usable-night count, date range and gaps. Below 50% baseline on two clear nights triggers possible power loss. Baseline, moon/cloud/noise masks and gap-fill influence are recorded; no trigger with insufficient valid nights. FIRMS: remove low-confidence and documented permanent hot spots; cluster within 1 km/12 h as source proposes; preserve original detections and dedup by source/product/id/time. Poll FIRMS and IODA every 30 min, lights daily, radar per actual acquisition, ACLED weekly.

IODA maps region outages, not building connectivity. Corroboration requires independent lineage families, overlapping time/space and compatible claim type. Two rehosts of one report, two visualizations of a product, or radar plus its derived class are one source. Fire plus radar supports coincident change, not a proven strike. Reviews are append-only with actor/time/reason. Fetch failure retains last-good data, marks Cached and gives last-success/error status; never overwrites with empty “all clear”.

## Local routes

Build network from permitted HOTOSM roads with topology/snap checks, directionality and access/vehicle tags; OSMnx/networkx initially, private OSRM only by ADR if needed. Source recommends 2–3 distinct paths; return fewer with reason when topology cannot support three. Confirmed closures are forbidden edges. Damage proximity alone means unknown-status edge, not confirmed closure. Unknown weights and assumed speeds are labelled engineering assumptions, not measured traffic.

Each option: (1) distance + estimated time, (2) confirmed closures avoided, (3) unknown segment number + length, (4) bridges/status, (5) nearby hazards, (6) newest evidence date plus oldest/stale essential input, (7) heavy-vehicle suitability or Unknown. Retain graph/closure revision. On confirmed closure increment revision, invalidate crossing routes, show warning and recompute. A new unverified report prompts caution/review, not automatic confirmed closure. No external route API, phone handoff or live GPS/convoy data. All results require field verification.

## Shelter candidates

Buildings first: eligible large civilian public-use buildings, no detected change is a screening input only. Exclude known hazardous/damaged/closed sites. Usable floor area = projected footprint × estimated levels × usable fraction. Source precedence: valid OSM levels; otherwise GHSL height/3 m; otherwise documented type default. ARCHITECT RECOMMENDATION: use illustrative 0.6–0.8 usable fraction and type-default 1–2 floors only in synthetic fixtures until M2 approves local assumptions. Missing height/structural information widens range or excludes candidate.

Capacity range = floor(usable area low/high ÷ selected space per person): 3.5 m² warm default, 4.5–5.5 cold, 30 m² short-term open site, 45 m² planned camp. These are source-specified planning settings, not certification of site safety or current standards. Open land needs eligible land use, slope, road access and hazard separation; thresholds require documented M2 choice. Rank by capacity near demand, access and warnings; always show basis, uncertainty and nearest reported water/health services. Protection, consent, structural and explosive-ordnance checks remain human prerequisites. Coordinates and site details coordinator-only.

## Artifact handoff

M1→M2 H16: schema-versioned cells, H3 r9, feature/reason columns, temporal pair, model/run IDs, valid coverage and QA manifest. M1→M3 H24: COG index plus bounds/CRS/nodata and checksum. M2→M3 H12/H24/H32: grid/cadaster crosswalk, MetricValue tables, permitted layer artifacts, deterministic adapter and route/shelter call signatures. M3 never infers missing lineage when loading. Data publication is atomic; rollback changes approved run pointer, not underlying evidence history.
''')

features=[
('F01','NISAR Jan–Jun HH/HV/HH−HV candidate changes, tiling, later passes and gaps','MVP','M1-02','H16/H24','T-RADAR','GCOV manifests → damage_cells + COGs'),
('F02','Population baseline, affected/displaced ranges and five-part severity','MVP','M2-02','H24','T-PEOPLE','WorldPop + cell shares → MetricValue'),
('F03','Facility inventory, reported operating state, service needs','MVP','M2-02','H24','T-FACILITY','HOTOSM + reports → AreaSummary'),
('F04','FIRMS, Black Marble archive/NRT, IODA, radar alerts and corroboration','MVP','M2-03','H24','T-ALERT','adapters → AlertDetail'),
('F05','People-first A4 brief, sources, vulnerable groups, no logistics counts','MVP','M4-03','H32/H38','T-BRIEF','AreaSummary → authorized HTML/print'),
('F06','Two or three inbound/outbound local route options, seven facts, closure update','MVP','M2-04','H32','T-ROUTE','local graph + closures → RouteOption[]'),
('F07','Ranked building shelters, modes, field checks; open-land candidates','MVP; open land reduced first if needed','M2-05','H24/H32','T-SHELTER','footprints + levels/height + hazards → ShelterCandidate[]'),
('F08','Sign-in, demo roles, public-safe view, protected map files and deny demo','MVP','M3-02','H12/H38','T-RBAC','session + area scopes → filtered resources'),
('F09','Sources, trace value, model results and reproducible lineage','MVP','M3-03','H24/H32','T-TRACE','run manifests + metrics → SourceRecord'),
('F10','Time comparison, polarization story, before/after/swipe and inspector','MVP','M4-02','H24','T-UI','Layer + series → map controls'),
('F11','Phone browser alerts, summary and routes; accessible light/dark UI','MVP basic; polish de-scope only','M4-04','H38','T-A11Y','same API → responsive views'),
('F12','OPERA RTC-S1 cross-sensor check, ascending track 172','Stretch','M1-04','Before H38 or later','T-ML','independent sensor → QA report'),
('F13','GUNW baseline and GSLC cross-gap coherence','Stretch; high scientific risk','M1-04','Before H38 or later','T-COHERENCE','validated aligned phase → optional feature'),
('F14','UNDP/CNRS-L validation overlay; UNOSAT absent for LB','Conditional stretch / VERIFY','M1-03','H32 or later','T-VALIDATION','aligned licensed reports → analyst-only overlay'),
('F15','ACLED and Insecurity Insight context and review workflow','MVP bounded licensed context','M2-03','H24/H32','T-INDEPENDENCE','reports + source families → reviewed alerts'),
('F16','Power→water→health→communications dependency graph','MVP explicit observed/reported links; full network after hackathon','M2-02','H24','T-SERVICES','verified dependency edges → possible loss'),
('F17','IOM DTM + Meta aggregated movement and displacement context','Stretch','M2-06','Before H38 or later','T-MOVEMENT','coarse aggregate sources → delayed trends'),
('F18','Global watch list, manual areas, ACLED weekly candidates, selective radar jobs','After hackathon','M2-06','Post-demo','T-BACKLOG','licensed events → watch areas'),
('F19','NISAR_COP future passes; OPERA land-disturbance GIBS context','Stretch','M1-04','Before H38 or later','T-DISPLAY','schedule/display metadata → contextual Layer'),
('F20','GHSL height fallback and HOTOSM-primary bounded Overpass','MVP','M2-01','H12','T-GEO','source metadata → uncertain floor-area range'),
('F21','Installable public shell and public offline summaries','Stretch','M4-04','Before H38 or later','T-CACHE','safe content only → offline shell'),
('F22','Protected offline briefs/routes, encryption and revocation','After hackathon','M3-04','Post-demo','T-CACHE','approved device policy → restricted local store'),
('F23','Browser PDF print export; server PDF export optional','MVP print-to-PDF; server PDF stretch','M4-03','H38','T-BRIEF','authorized brief → A4/QR/source footnotes'),
('F24','Optional LLM/Gemini fixed-question explanation','After hackathon (deferred stretch)','M3-04','Post-demo','T-LLM','trusted safe results → non-authoritative explanation; no numeric invention'),
('F25','No military/frontline, live tracking, targeting, reconstruction or general disaster app','Constraint all phases','M3-02','Every gate','T-SAFETY','safety policy → rejection/filtering'),
('F26','72 h delay, H3 r8 public aggregation plus concentration suppression','MVP invariant','M3-02','H12/H38','T-DELAY','acquisition/publication timestamps → release gate'),
('F27','Licences, non-Chinese-owned sources, NASA tab citation and uncertainty','MVP invariant','M2-01','H2/H48','T-LICENCE','source register → allowed use and attribution'),
('F28','Twelve named deterministic functions; no autonomous LLM pipeline','MVP modules; Movement deferred','M3-04','H24','T-AGENTS','typed functions → immutable evidence-bearing outputs'),
]
doc(names[1],'Requirements and delivery scope',f'''
## Mission and boundaries

CIVISAR supports authorised civilian humanitarian interpretation of war impacts. The judged example is south Lebanon, 35.0–36.0 E, 33.0–33.6 N, track 151 descending/frame 72. Those study bounds are public research metadata, not operational locations. NISAR is the challenge anchor. No reconstruction planning, general natural-disaster expansion, targeting, military/frontline objects or live people/vehicle/phone/convoy tracking belongs in this build.

Sources: PROJECT_PLAN.md §§1–13; ARCHITECTURE.md Ground rules, MVP, Parts 1–4; UI_DESIGN.md §§1–7. User's master request keeps provenance and safety as non-negotiable even under de-scope.

## Complete delivery inventory

Each story has one accountable task. Dependencies, expected files, estimates and tests are expanded in [four member allocation](08_FOUR_MEMBER_TASK_ALLOCATION.md) and individual task files; [roadmap](09_48_HOUR_DEVELOPMENT_ROADMAP.md) supplies gates.

{table(['ID','Feature','Phase','Accountable task','Gate','Acceptance ID','Input → output'],features)}

## Evidence and scientific meaning

Use Observed, Reported, Corroborated, Unknown. These are evidence types, not a numeric confidence ladder: retain each source's type and derivation. Corroboration is a separate independence-tested agreement, and never converts a thermal signal or anomaly into a confirmed collapse. Derived service or population claims cannot exceed the support of their weakest essential input. Keep low/high, unit, source and date on every estimate; missing values are null, never zero.

Say “Fire detected”; “Possible power loss”; “Candidate damage”; “No detected damage. Not confirmed open.”; “No reported closure”. Never promise a route or shelter is safe. Fresh/Aging/Stale describe expected update age; Cached separately describes delivery from a last-good snapshot. Show acquisition, processing, fetched-at and last-success dates.

## MVP acceptance and fallback

All seven architecture MVP capabilities remain in the demonstration. If real input is unavailable, show a labelled synthetic journey and separately disclose that real-data MVP acceptance failed. A metadata-only NISAR picture is not a processed NISAR demo. Never claim validation, downloads, API availability or live tracking from mocked screens. The backup can demonstrate UI/RBAC behavior while scientific acceptance remains BLOCKED.

De-scope in source order: optional question box; tier-C coherence; phone/print polish (retain usable responsive views and A4); open-land shelters (retain building candidates); later slider passes after July (retain actual Jan/Jun pair and visible missing data). This is a declared reduced demonstration, not full F01/F07 acceptance. Never cut NISAR, role enforcement, provenance, public aggregation or safety.
''')

doc(names[2],'Full system architecture','''
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
''')

# One set of synthetic fixtures and draft schemas shared by frontend/backend at H2.
metric={'synthetic':True,'value_id':'demo-value-01','area_id':'demo-area-01','metric':'residents_baseline','low':1200,'high':1800,'unit':'people','label':'Unknown','source':['demo-source-01'],'date':'2026-01-01','safety_tag':'restricted_aggregate','lineage_ids':['demo-lineage-01'],'processing_run_id':'demo-run-01','processing_version':'demo-v1','confidence':None,'acquired_at':'2026-01-01T00:00:00Z','processed_at':'2026-06-25T00:00:00Z','release_at':'2026-06-27T00:00:00Z','freshness':'Stale','cached':True,'limitations':['Synthetic range; no measured population.']}
source={'synthetic':True,'source_id':'demo-source-01','dataset_id':'DS01','name':'Synthetic NISAR contract fixture','provider':'NASA/ISRO via ASF (product attribution only)','product_level':'L2','cmr_concept_id':'C3622214170-ASF','challenge_provenance':'Tab','source_url':'https://search.asf.alaska.edu/','acquisition_start':'2026-01-19T00:00:00Z','acquisition_end':'2026-01-19T00:00:00Z','processing_version':'BETA 1.0.2 (source-reported)','spatial_coverage':{'area_id':'demo-area-01','geometry':None,'track':151,'frame':72},'resolution_m':None,'licence':'VERIFY before real data use','accessed_at':None,'api':'ASF Search + earthaccess','checksum':None,'independence_family':'synthetic-nisar','live_tested':False,'limits':['No granule downloaded; metadata is illustrative, not a fresh check.']}
route={'synthetic':True,'route_id':'demo-route-A','area_id':'demo-area-01','direction':'inbound','option':'A','geometry':None,'location_redacted':True,'distance_m':2400,'estimated_duration_s':600,'duration_basis':'synthetic assumed speed; no live traffic','confirmed_closures_avoided':2,'unknown_segments':{'count':3,'length_m':400},'bridges':[{'id':'demo-bridge','status':'Unknown'}],'hazard_exposure':[{'type':'synthetic_fire_context','label':'Unknown'}],'newest_evidence_at':'2026-06-24T12:00:00Z','oldest_essential_evidence_at':'2026-01-01T00:00:00Z','heavy_vehicle_suitability':'Unknown','graph_revision':1,'closure_revision':1,'invalidated':False,'turns':[{'instruction':'Synthetic turn list; field verification required','distance_m':200}],'label':'Unknown','source':['demo-source-01'],'date':'2026-06-24','freshness':'Stale','cached':True,'safety_tag':'officer_route','release_at':'2026-06-27T00:00:00Z','warning':'No reported closure. Field verification required; no live tracking.'}
shelter={'synthetic':True,'candidate_id':'demo-shelter-01','area_id':'demo-area-01','rank':1,'kind':'building','name':'Synthetic candidate A','geometry':None,'location_redacted':True,'usable_area_m2':{'low':350,'high':525},'floor_estimate':{'low':1,'high':2,'basis':'synthetic type default, uncertain'},'mode':'warm_building','space_per_person_m2':3.5,'capacity':{'low':100,'high':150,'unit':'people'},'distance_to_affected_m':None,'nearest_reported_health':None,'nearest_reported_water':None,'access_status':'Unknown','hazards':['No structural or explosive-ordnance assessment'],'field_check_status':'not_requested','label':'Unknown','source':['demo-source-01'],'date':'2026-06-24','freshness':'Stale','cached':True,'safety_tag':'coordinator_shelter','release_at':'2026-06-27T00:00:00Z','warning':'Candidate for checking; protection and explosive-ordnance checks required.'}
alert={'synthetic':True,'alert_id':'demo-alert-01','area_id':'demo-area-01','type':'fire_detected','title':'Fire detected (synthetic demonstration)','detected_at':'2026-06-24T12:00:00Z','processed_at':'2026-06-24T12:30:00Z','satellite':'NOAA-20','product':'VJ114IMGTDL_NRT','label':'Unknown','source':['demo-source-01'],'lineage_ids':['demo-lineage-01'],'independent_source_count':0,'freshness':'Stale','cached':True,'release_at':'2026-06-27T12:00:00Z','safety_tag':'restricted_alert','rings':[{'radius_m':1000,'people':metric},{'radius_m':3000,'people':metric}],'facilities':[],'services':[],'route_options_url':'/api/v1/routes','review_status':'unreviewed','cause':'Unknown','warning':'Synthetic signal; CIVISAR does not determine a cause.'}
layer={'synthetic':True,'layer_id':'demo-damage-r8','title':'Synthetic candidate change','kind':'raster','product':'NISAR GCOV','analytical':True,'polarizations':['HH','HV','HH-HV'],'available_acquisitions':['2026-01-19T00:00:00Z','2026-06-24T00:00:00Z'],'missing_intervals':[{'start':'2026-01-20','end':'2026-06-17','reason':'Source-reported acquisition gap; not interpolated'}],'default_comparison':{'before':'2026-01-19','after':'2026-06-24'},'tile_url':'/api/v1/layers/demo-damage-r8/tiles/{z}/{x}/{y}','min_role':'analyst','source_ids':['demo-source-01'],'label':'Unknown','date':'2026-06-24','acquired_at':'2026-06-24T00:00:00Z','processed_at':'2026-06-25T00:00:00Z','release_at':'2026-06-27T00:00:00Z','freshness':'Stale','cached':True,'public_resolution':8,'safety_tag':'restricted_until_review','extent':None,'attribution':'Synthetic fixture; no imagery supplied'}
summary={'synthetic':True,'area_id':'demo-area-01','name':'Synthetic neighbourhood','as_of':'2026-06-24T12:00:00Z','people':{'residents':metric,'potentially_affected':dict(metric,metric='potentially_affected',low=300,high=600),'potentially_displaced':dict(metric,metric='potentially_displaced',low=100,high=300)},'vulnerable_groups':[],'services':[{'type':'water','status':'Unknown','label':'Unknown','source':[],'date':None}],'what_to_bring':[{'item':'Verify water service before supply planning','basis_value_ids':[],'quantity':None}],'facilities':[],'hazards':[{'alert_id':'demo-alert-01','type':'synthetic_fire_context'}],'severity':{'rank':None,'parts':['damage','people','facilities','services','roads'],'reason':'Incomplete synthetic inputs'},'nearest_reported_operating_hospital':None,'route_options':[],'shelter_candidates':[],'permissions':{'routes':False,'shelters':False,'brief':True},'evidence':[metric],'freshness':'Stale','cached':True,'safety_tag':'restricted_aggregate','warning':'Entire response is synthetic. Not a field-use assessment.'}
error={'error':{'code':'FORBIDDEN','message':'Your role cannot access this resource.','request_id':'demo-request-01','details':[]},'synthetic':True}
examples={'MetricValue':metric,'SourceRecord':source,'RouteOption':route,'ShelterCandidate':shelter,'AlertDetail':alert,'Layer':layer,'AreaSummary':summary,'Error':error}
for k,v in examples.items(): write('contracts/'+k+'.json',json.dumps(v,indent=2,ensure_ascii=False))

def infer(v):
    if v is None: return {'description':'Nullable or redacted in synthetic example; refine semantics at H2.'}
    if isinstance(v,bool): return {'type':'boolean'}
    if isinstance(v,str): return {'type':'string'}
    if isinstance(v,int): return {'type':'integer'}
    if isinstance(v,float): return {'type':'number'}
    if isinstance(v,list): return {'type':'array','items':infer(v[0]) if v else {}}
    return {'type':'object','additionalProperties':False,'required':list(v),'properties':{k:infer(x) for k,x in v.items()}}
schemas={k:infer(v) for k,v in examples.items()}
schemas['MetricValue']['properties']['label']['enum']=['Observed','Reported','Corroborated','Unknown']
schemas['MetricValue']['properties']['freshness']['enum']=['Fresh','Aging','Stale']
schemas['MetricValue']['properties']['low']={'type':['number','null']}
schemas['MetricValue']['properties']['high']={'type':['number','null']}
schemas['MetricValue']['properties']['confidence']={'type':['number','null'],'minimum':0,'maximum':1}
for s in schemas.values():
    s['description']='DRAFT synthetic contract. No live-server validation. Nullable/redacted fields require role-aware implementation.'
schemas['RouteOption']['properties']['direction']['enum']=['inbound','outbound']
schemas['RouteOption']['properties']['heavy_vehicle_suitability']['enum']=['Unknown','reported_suitable','reported_unsuitable']
schemas['ShelterCandidate']['properties']['space_per_person_m2']={'type':'number','minimum':3.5,'maximum':45}

# method, path, roles, params/body, response contract, owner, domain input task, privacy/rate class
endpoints=[
('POST','/session','public','username,password','Session','M3-02','M3-02','auth'),
('GET','/session','signed_in','none','Session','M3-02','M3-02','read'),
('DELETE','/session','signed_in','CSRF header','Empty','M3-02','M3-02','write'),
('GET','/roles','signed_in','none','Roles','M3-02','M3-02','read'),
('GET','/public/map','public','bbox optional; fixed demo AOI','PublicMap','M3-02','M4-01','public'),
('GET','/health','public','none','Health','M3-04','M3-04','public'),
('GET','/status','public','none; sanitized','Status','M3-04','M2-03','public'),
('GET','/layers','public','public_only or authorized area_id','LayerList','M3-03','M1-02','read'),
('GET','/layers/{layer_id}','public','layer_id; policy may deny','Layer','M3-03','M1-02','read'),
('GET','/layers/{layer_id}/tiles/{z}/{x}/{y}','public','layer_id,z,x,y; same policy as layer','Binary','M3-02','M1-02','tiles'),
('GET','/layers/{layer_id}/files/{file_id}','public','file_id; Range header; scoped manifest allowlist','Binary','M3-02','M2-01','tiles'),
('GET','/layers/{layer_id}/timeseries','analyst+','area_id,from,to,polarization','Series','M3-03','M1-02','read'),
('GET','/areas','analyst+','bbox,cursor,limit','AreaList','M3-03','M2-01','read'),
('GET','/areas/{area_id}/summary','analyst+','area_id,as_of','AreaSummary','M3-03','M2-02','read'),
('GET','/areas/{area_id}/values','analyst+','metric,as_of,cursor','MetricList','M3-03','M2-02','read'),
('GET','/areas/{area_id}/people','analyst+','as_of','MetricList','M3-03','M2-02','read'),
('GET','/areas/{area_id}/services','analyst+','as_of','ServiceList','M3-03','M2-02','read'),
('GET','/areas/{area_id}/facilities','analyst+','type,cursor; sensitive sites filtered','FacilityList','M3-03','M2-02','read'),
('GET','/areas/{area_id}/damage','analyst+','pass_id; r9 scoped','DamageList','M3-03','M1-02','read'),
('GET','/areas/{area_id}/validation','analyst+','assessment_id; licence/availability gate','ValidationList','M3-03','M1-03','read'),
('GET','/alerts','analyst+','area_id,type,since,cursor,limit','AlertList','M3-03','M2-03','read'),
('GET','/alerts/{alert_id}','analyst+','alert_id; area/object check','AlertDetail','M3-03','M2-03','read'),
('POST','/alerts/{alert_id}/reviews','analyst+','status,note; CSRF; append-only','Review','M3-03','M2-03','write'),
('GET','/sources','public','cursor; sanitized catalogue','SourceList','M3-03','M2-01','public'),
('GET','/sources/{source_id}','public','source_id; restricted lineage filtered','SourceRecord','M3-03','M2-01','read'),
('GET','/values/{value_id}/trace','analyst+','value_id; transitive lineage authorization','Trace','M3-03','M1-03','read'),
('POST','/routes','officer+','area_id,origin_id,destination_id,direction,vehicle_type','RouteList','M3-03','M2-04','compute'),
('GET','/routes/{route_id}','officer+','route_id; owner/area authorization','RouteOption','M3-03','M2-04','read'),
('GET','/routes/{route_id}/status','officer+','route_id,known_revision','RouteStatus','M3-03','M2-04','read'),
('POST','/closures','officer+','segment_id,report,evidence_ids; no coordinates in logs','Closure','M3-03','M2-04','write'),
('POST','/closures/{closure_id}/review','coordinator+','decision,reason,evidence_ids','Closure','M3-03','M2-04','write'),
('GET','/shelters','coordinator+','area_id,mode,space_per_person_m2,limit','ShelterList','M3-03','M2-05','compute'),
('POST','/shelters/capacity','coordinator+','candidate_id,mode,space_per_person_m2','ShelterCandidate','M3-03','M2-05','compute'),
('POST','/shelters/{candidate_id}/field-checks','coordinator+','check_type,note; no external dispatch','FieldCheck','M3-03','M2-05','write'),
('POST','/briefs','analyst+','area_id,as_of; authorized sections only','Brief','M3-03','M2-02','write'),
('GET','/briefs/{report_id}','signed_in','report_id; re-evaluate role/area at read','Brief','M3-03','M4-03','read'),
('GET','/briefs/{report_id}/print','signed_in','report_id; role-filtered HTML','Binary','M3-03','M4-03','read'),
('GET','/admin/audit','admin','cursor,from,to; redacted','AuditList','M3-02','M3-02','read'),
('PATCH','/admin/users/{user_id}/roles','admin','role,area_scopes,reason; CSRF','Roles','M3-02','M3-02','write'),
('POST','/admin/jobs/{job_id}/retry','admin','idempotency_key; no arbitrary command','Job','M3-04','M3-04','write'),
]
envelopes={'LayerList':'Layer','MetricList':'MetricValue','AlertList':'AlertDetail','SourceList':'SourceRecord','RouteList':'RouteOption','ShelterList':'ShelterCandidate'}
for k,item in envelopes.items(): schemas[k]={'type':'object','required':['items','next_cursor','synthetic'],'properties':{'items':{'type':'array','items':{'$ref':'#/components/schemas/'+item}},'next_cursor':{'type':['string','null']},'synthetic':{'type':'boolean'}},'additionalProperties':False}
basic={
'Session':{'synthetic':True,'user_id':'demo-user','role':'analyst','area_scopes':['demo-area-01'],'expires_at':'2026-06-24T20:00:00Z','csrf_token':'synthetic-placeholder-not-a-secret'},
'Roles':{'synthetic':True,'role':'analyst','capabilities':['area_read'],'area_scopes':['demo-area-01']},
'PublicMap':{'synthetic':True,'resolution':8,'layers':[],'suppressed':True,'release_policy':'72h_and_review'},
'Health':{'status':'ok','synthetic':True},
'Status':{'synthetic':True,'sources':[{'id':'DS05','acquired_at':None,'processed_at':None,'last_success_at':None,'freshness':'Stale','cached':True,'failure':'Not configured'}]},
'Series':{'synthetic':True,'area_id':'demo-area-01','points':[],'missing_intervals':layer['missing_intervals']},
'AreaList':{'synthetic':True,'items':[{'area_id':'demo-area-01','h3_id':None,'cadaster_code':None}],'next_cursor':None},
'ServiceList':{'synthetic':True,'items':summary['services'],'next_cursor':None},
'FacilityList':{'synthetic':True,'items':[{'facility_id':'demo-facility','type':'clinic','operating_status':'Unknown','damage_status':'No detected damage. Not confirmed open.','label':'Unknown','source':[],'date':None,'geometry':None}],'next_cursor':None},
'DamageList':{'synthetic':True,'items':[{'area_id':'demo-area-01','candidate_class':'Unknown','score':None,'reason_codes':['no_real_data'],'run_id':'demo-run-01'}],'next_cursor':None},
'ValidationList':{'synthetic':True,'items':[],'availability':'VERIFY; no assessment acquired','next_cursor':None},
'Review':{'synthetic':True,'review_id':'demo-review','status':'reviewed','actor_id':'demo-user','created_at':'2026-06-24T13:00:00Z'},
'Trace':{'synthetic':True,'value':metric,'sources':[source],'runs':[{'run_id':'demo-run-01','model_tests':[]}],'redactions':['restricted locations omitted']},
'RouteStatus':{'synthetic':True,'route_id':'demo-route-A','invalidated':True,'current_closure_revision':2,'message':'New confirmed closure; recompute options.'},
'Closure':{'synthetic':True,'closure_id':'demo-closure','segment_id':'demo-segment','status':'reported_unverified','revision':1,'label':'Reported','source':[],'date':'2026-06-24'},
'FieldCheck':{'synthetic':True,'request_id':'demo-field-check','status':'requested','external_message_sent':False},
'Brief':{'synthetic':True,'report_id':'demo-report','area_summary':summary,'included_sections':['people','services','hazards','sources'],'omitted_sections':['routes','shelters'],'source_footnotes':[source],'live_view_path':'/briefs/demo-report','expires_at':None},
'AuditList':{'synthetic':True,'items':[{'actor_id':'demo-user','action':'shelters_denied','resource_type':'shelter','outcome':'denied','at':'2026-06-24T13:00:00Z'}],'next_cursor':None},
'Job':{'synthetic':True,'job_id':'demo-job','status':'queued','idempotency_key':'demo-key'},
}
for k,v in basic.items(): schemas[k]=infer(v)
request_schemas={
'POST /session':{'username':'demo-analyst','password':'synthetic-placeholder-not-a-password'},
'POST /routes':{'area_id':'demo-area-01','origin_id':'demo-origin','destination_id':'demo-destination','direction':'inbound','vehicle_type':'ambulance'},
'POST /closures':{'segment_id':'demo-segment','report':'Synthetic closure report','evidence_ids':[]},
'POST /closures/{closure_id}/review':{'decision':'confirmed','reason':'Synthetic reviewed evidence','evidence_ids':[]},
'POST /shelters/capacity':{'candidate_id':'demo-shelter-01','mode':'warm_building','space_per_person_m2':3.5},
'POST /shelters/{candidate_id}/field-checks':{'check_type':'protection','note':'Synthetic request'},
'POST /briefs':{'area_id':'demo-area-01','as_of':'2026-06-24T12:00:00Z'},
'POST /alerts/{alert_id}/reviews':{'status':'reviewed','note':'Synthetic review'},
'PATCH /admin/users/{user_id}/roles':{'role':'analyst','area_scopes':['demo-area-01'],'reason':'Synthetic scope'},
'POST /admin/jobs/{job_id}/retry':{'idempotency_key':'demo-key'}
}
spec={'openapi':'3.1.0','info':{'title':'CIVISAR DRAFT API','version':'0.1.0-draft','description':'Planning contract only. All examples synthetic. No server implemented or validated. H2 contract review required.'},'servers':[{'url':'http://localhost:8000/api/v1','description':'Planned local development only'}],'paths':{},'components':{'securitySchemes':{'sessionCookie':{'type':'apiKey','in':'cookie','name':'civisar_session'}},'schemas':schemas},'security':[{'sessionCookie':[]}]}
for i,(method,path,roles,params,response,owner,domain,rate) in enumerate(endpoints,1):
    operation={'operationId':f'op_{i:02}_{method.lower()}','summary':params,'x-owner-task':owner,'x-domain-task':domain,'x-required-roles':roles,'x-rate-class':rate,'description':'Server checks session, role, area, object, safety_tag and release_at before data/file access. All 401/403 errors are scrubbed. DRAFT.','parameters':[],'responses':{}}
    for name in re.findall(r'\{(\w+)\}',path): operation['parameters'].append({'name':name,'in':'path','required':True,'schema':{'type':'integer','minimum':0} if name in ['z','x','y'] else {'type':'string','maxLength':128}})
    if method=='GET':
        for q in ['area_id','bbox','cursor','limit','as_of','from','to','polarization','metric','type','since','pass_id','assessment_id','known_revision','mode','space_per_person_m2','public_only']:
            if re.search(r'\b'+q+r'\b',params) and '{'+q+'}' not in path:
                qs={'type':'integer','minimum':1,'maximum':100} if q=='limit' else {'type':'number','minimum':3.5,'maximum':45} if q=='space_per_person_m2' else {'type':'string','maxLength':256}
                operation['parameters'].append({'name':q,'in':'query','required':q=='area_id' and rate=='compute','schema':qs})
    if method in ['POST','PATCH','DELETE'] and not (method=='POST' and path=='/session'): operation['parameters'].append({'name':'X-CSRF-Token','in':'header','required':True,'schema':{'type':'string'}})
    if roles=='public': operation['security']=[] if path in ['/health','/public/map','/status'] or method=='POST' else [{},{'sessionCookie':[]}]
    key=method+' '+path
    if key in request_schemas: operation['requestBody']={'required':True,'content':{'application/json':{'schema':infer(request_schemas[key]),'example':request_schemas[key]}}}
    if response=='Empty': operation['responses']['204']={'description':'Session revoked; clear cookie and protected client state'}
    elif response=='Binary': operation['responses']['200']={'description':'Authorized binary artifact or printable HTML; protected Cache-Control private, no-store; Range authorization required','content':{'text/html' if path.endswith('/print') else 'application/octet-stream':{'schema':{'type':'string'}}}}
    else:
        ex=examples.get(response,basic.get(response))
        if response in envelopes: ex={'items':[examples[envelopes[response]]],'next_cursor':None,'synthetic':True}
        operation['responses']['200']={'description':'Role-filtered response; synthetic example','content':{'application/json':{'schema':{'$ref':'#/components/schemas/'+response},'example':ex}}}
    for code,desc in [('401','Missing or expired session'),('403','Role, object, area or publication policy denies access'),('404','Allowed resource absent; do not leak forbidden IDs'),('409','Revision conflict or source unavailable for requested operation'),('422','Invalid or over-broad query'),('429','Rate limit; Retry-After'),('503','Dependency unavailable and no last-good result')]:
        operation['responses'][code]={'description':desc,'content':{'application/json':{'schema':{'$ref':'#/components/schemas/Error'},'example':dict(error,error=dict(error['error'],code={'401':'UNAUTHENTICATED','403':'FORBIDDEN'}.get(code,'REQUEST_FAILED'),message=desc))}}}
    spec['paths'].setdefault(path,{})[method.lower()]=operation
write('contracts/openapi.yaml',json.dumps(spec,indent=2,ensure_ascii=False)) # JSON is valid YAML 1.2, avoids YAML parser ambiguity.
write('contracts/README.md','''# Draft contract workspace

[Blueprint index](../README.md) · [API design](../05_BACKEND_DATABASE_AND_API_CONTRACTS.md)

Every example is synthetic, contains no operational geometry, and is not a claim about Lebanon. `demo-area-01` is an opaque fixture ID, not a valid production H3 index. Real production rows must use valid H3 IDs and stable admin crosswalks. JSON placeholders are deliberate redactions; nullable fields and optional arrays need final domain refinement at H2.

[openapi.yaml](openapi.yaml) uses JSON syntax, which is valid YAML 1.2. It is a draft OpenAPI 3.1 contract with typed essential responses, request examples, error responses, owner/role/rate extensions and endpoint paths. It has NOT been tested against a running service. Specification/schema validation results are recorded in [planning verification](../16_PLANNING_VERIFICATION.md); generated-client and live-server contract tests remain H2 implementation gates.

'''+table(['Contract','Example','Purpose'],[(k,f'[{k}.json]({k}.json)','H2 shared fixture, no sensitive coordinates') for k in examples])+'''
## Endpoint ownership

M3 owns the HTTP implementations below. Domain tasks retain accountable algorithm ownership; M4 owns typed client/fixture consumption. Freeze request/response version 0.1 at H2 with all four reviewers. Breaking changes require contract PR first, fixture update and named downstream acknowledgement.

'''+table(['Method','Path under /api/v1','Roles','Params/body','Response','HTTP owner','Domain dependency','Limit class'],endpoints)+'''
`analyst+`: analyst/officer/coordinator/admin with area scope. `officer+`: officer/coordinator/admin with area scope. `coordinator+`: coordinator/admin with area scope. Admin does not bypass area/object/time checks. Public-capable layer paths still deny private layers to anonymous users. Role names are proposed capabilities, not authority granted by client input.

Rate classes and evidence/error rules: [backend contract](../05_BACKEND_DATABASE_AND_API_CONTRACTS.md). Read status/metadata/availability before rendering; null means unknown, not zero. Cached is an orthogonal boolean displayed as DataAge Cached alongside last-good dates.
''')

doc(names[5],'Backend, database and API contracts','''
## API first at H2

Sources: ARCHITECTURE.md Agree at hour 2 and Part 3; PROJECT_PLAN.md §§8.1–10; UI_DESIGN.md §§2/6. [Endpoint inventory and examples](contracts/README.md) is the authoritative draft path/owner/role/parameter/response inventory. [OpenAPI draft](contracts/openapi.yaml) contains every inventory operation with errors and response examples. Freeze at H2 before parallel feature integration. M3 owns schemas/loaders/HTTP, M1/M2 supply domain outputs, M4 owns client and mock fixtures.

ARCHITECT RECOMMENDATION: `/api/v1` conventions, opaque IDs, ISO 8601 UTC timestamps, ISO dates only for day-level source data, SI units explicitly named, cursor pagination (default 25/max 100), RFC-style JSON errors with request ID and no sensitive internals. A response may be partial with explicit Unknown fields; no fabricated measurements. Non-essential payloads remain draft shapes in OpenAPI; actual domains must refine them at H2.

## Endpoint rules applied to every inventory row

Success payloads carry relevant evidence fields: values/alerts/route/shelter use `label,source,date,freshness,cached,safety_tag`; Layer uses source_ids plus acquired/processed/release timestamps; SourceRecord holds dataset provenance; status exposes only sanitized freshness. Collections retain per-item evidence. No unauthenticated trace may traverse into restricted granule paths or precise sites.

Errors: 401 absent/expired session, 403 role/area/object/tag/time denial, 404 permitted object not found, 409 stale graph/closure revision or unavailable requested source, 422 invalid bounds/mode/time, 429 limit with Retry-After, 503 source failed without cached state. Denied private objects do not reveal their coordinates, type details or existence through counts. GET `/api/v1/shelters` must return 401 anonymous and 403 analyst. Protected layer/file/print paths use identical policy.

Proposed per-user/IP budgets: auth 5 attempts/min then backoff; public 60/min; read 120/min; write 20/min; compute 10/min and one concurrent task; tiles 300/min with bounded tile count and maximum zoom approved for role. Route endpoints bound area to demo AOI and 3 alternatives; shelter limit ≤50; temporal queries ≤366 days unless admin job; bbox area ≤the demo AOI. Tune against measured demo behavior; never query the entire world by default. File IDs resolve from allowed manifests, never arbitrary paths or URLs. Range requests must pass the same checks and cannot span another private artifact.

## Proposed relational schema

Proposed freshness thresholds distinguish source acquisition age from successful polling: FIRMS/IODA last successful fetch ≤45 min Fresh, ≤2 h Aging, otherwise Stale; Black Marble newest usable acquisition ≤36 h Fresh, ≤72 h Aging, otherwise Stale. Radar shows acquisition age and expected next pass explicitly; a known acquisition gap is not a fetch failure. Radar freshness uses the published expected pass + processing allowance when available, otherwise Unknown schedule, not a fabricated 12-day arrival. Cached=true can coexist with any age class. These are demo engineering defaults to review at H2, not provider latency guarantees.

All choices here are ARCHITECT RECOMMENDATION. UUID primary keys except H3 area IDs and source-defined immutable keys. `created_at`, `updated_at`, schema_version and provenance FK are required where applicable. Foreign keys enforce referential integrity. Decimal/numeric values use explicit units and CHECK(low <= high) when both non-null.

| Table | Key fields and constraints | Index/use |
|---|---|---|
| users, roles, user_roles, user_area_scopes, sessions | user_id, password_hash, enabled; role enum; area_id; hashed session token, expires_at, revoked_at | unique username; session hash lookup; scoped authorization |
| areas, cadaster, area_cadaster | area_id H3 string, resolution 8/9, parent_id, geom; admin codes; intersection_share | GiST geom; unique H3/resolution; FK parent; fractional joins sum check |
| datasets, source_versions | dataset_id, provider, product, CMR, mark, terms_url, approved_uses; immutable source version | source family/version unique; licence approval gate |
| granules | granule_id, dataset_version_id, start/end, track/frame, processor, CRS, bbox, checksum, private_uri | GiST bbox; acquisition B-tree; dataset+external_id+version unique |
| processing_runs, run_inputs, artifacts | run_id, algorithm/code/parameter hashes, status, QA; input granules; checksum,path,tag,release_at | idempotency unique; run/status index; no client path access |
| values, value_lineage | value_id, area_id, metric, low/high/unit, label, source/date/tag, run_id, validity period | area/metric/date index; run FK; lineage DAG cycle rejection |
| damage_candidates | area_id, pass_pair, score, candidate_class, reason_codes, valid_pixel_count, run_id | area/pass unique per run; no confirmed collapse label |
| facilities, facility_reports | inventory geometry/type; report status, observed_at, reporter, evidence | GiST geom; report chronology; separate inventory/operating status |
| service_dependencies | from/to facility or area, service, evidence_id, confidence/validity | only verified/reported edges; no proximity-derived certainty |
| road_segments, closures, closure_reviews | segment geom/access/bridge, graph_revision; report versus confirmed, validity | GiST geom; segment/revision; append-only reviews |
| observations, alerts, alert_evidence, alert_reviews | source event key, area, detected_at, status, label, release_at; independent families | event key unique; time/area; no duplicate rehost upgrade |
| shelter_candidates, field_checks | private geom, access_tag, capacity assumptions/ranges, state, run_id; check requests | GiST private geom; coordinator scope; no public copy |
| routes, route_segments, route_audit | private origin/dest/geometry, graph/closure revision, owner scope, expiry; redacted audit | scoped user/area; segment join for invalidation |
| freshness_status, jobs | last acquisition/process/success/error, age class,cached; next_due,lease,idempotency | source/job unique; bounded retry and lease expiry |
| reports, report_values | author, area, source run snapshot, role policy version, expiry, content hash | report ACL re-evaluated at export; no long-lived unguarded link |
| audit_events | actor, action, coarse resource type, outcome, timestamp, request_id | append-only restricted; no coordinates/tokens/raw request bodies |

## ERD

```mermaid
erDiagram
  USERS ||--o{ USER_ROLES : has
  USERS ||--o{ USER_AREA_SCOPES : scoped
  USERS ||--o{ SESSIONS : authenticates
  AREAS ||--o{ VALUES : contains
  AREAS ||--o{ AREA_CADASTER : intersects
  CADASTER ||--o{ AREA_CADASTER : joins
  DATASETS ||--o{ GRANULES : provides
  GRANULES ||--o{ RUN_INPUTS : feeds
  PROCESSING_RUNS ||--o{ RUN_INPUTS : consumes
  PROCESSING_RUNS ||--o{ ARTIFACTS : produces
  PROCESSING_RUNS ||--o{ VALUES : derives
  VALUES ||--o{ VALUE_LINEAGE : traced
  AREAS ||--o{ DAMAGE_CANDIDATES : scored
  AREAS ||--o{ FACILITIES : inventories
  FACILITIES ||--o{ FACILITY_REPORTS : reported
  ROAD_SEGMENTS ||--o{ CLOSURES : blocks
  CLOSURES ||--o{ CLOSURE_REVIEWS : reviewed
  ROUTES ||--o{ ROUTE_SEGMENTS : includes
  ROAD_SEGMENTS ||--o{ ROUTE_SEGMENTS : traverses
  AREAS ||--o{ ALERTS : aggregates
  ALERTS ||--o{ ALERT_REVIEWS : reviewed
  AREAS ||--o{ SHELTER_CANDIDATES : restricts
  SHELTER_CANDIDATES ||--o{ FIELD_CHECKS : requests
  REPORTS ||--o{ REPORT_VALUES : cites
  VALUES ||--o{ REPORT_VALUES : used
```

## Data loading and publication

M3 validates manifests/schemas/checksums and transactionally inserts run + results + lineage. Geometry validation rejects wrong CRS, empty/malformed shapes and unexpected AOI. Explicit projection precedes distance/area calculation. Public view is a precomputed r8 materialization stripped of shelters, exact critical infrastructure, dispatch/route details and identifiable concentrations. Aggregation alone is insufficient: suppression/manual protection review is required. Public derivatives never embed r9 source geometries in metadata.

No app migration, database instance or endpoint was implemented during planning. Target implementation commands and test paths appear in [onboarding](15_TEAM_ONBOARDING.md); they must not be reported as successful until the app exists.
''')

screens=[
('Sign-in','POST/GET /session; GET /roles','MVP','M4-01','UI_DESIGN.md §6','Form keyboard accessible; errors scrubbed; role never chosen in client; expired session clears private state'),
('Logged-out public-safe view','GET /public/map; /status; /sources','MVP','M4-01','UI_DESIGN.md §6','No route/shelter/brief/dispatch/private layer data in requests or payloads; sign-in explanation'),
('ScreenMainMap','GET /layers; /layers/{id}/tiles/...; /alerts; /areas/{id}/summary; /status','MVP','M4-02','UI_DESIGN.md §§3/3.1','Agent results first, NASA data next; CORE tag, HH/HV/HH−HV, track/opacity, folding side rails [, ], active legend, missing passes'),
('ScreenAlertDetail','GET /alerts/{id}; POST /alerts/{id}/reviews; POST /routes','MVP','M4-03','UI_DESIGN.md §3.1','Fire wording, no cause, local+UTC time, NOAA-20/21 product; restricted synthetic 1/3 km rings; compare routes and summary actions'),
('ScreenAreaSummary','GET /areas/{id}/summary; POST /briefs; POST /routes; GET /shelters','MVP','M4-03','UI_DESIGN.md §§2/3.1','People first; ranges, vulnerabilities, source-linked what-to-bring; no invented counts; role-filtered nearest options'),
('ScreenAreaBrief','POST /briefs; GET /briefs/{id}/print','MVP A4/print-to-PDF; offline later','M4-03','UI_DESIGN.md §§2/3.1','One black-on-white A4 page, numbered source footnotes, acquisition/save dates, QR to authenticated view without token/coordinates'),
('ScreenRoutes','POST /routes; GET /routes/{id}; /routes/{id}/status; POST /closures','MVP','M4-03','UI_DESIGN.md §3.1; PROJECT_PLAN.md §6.5','A/B/C solid/long dash/dot-dash; seven facts fixed order, in/out, vehicle type, local turn list, new-closure banner, never safe'),
('ScreenShelters','GET /shelters; POST /shelters/capacity; /shelters/{id}/field-checks','MVP buildings; open land may reduce','M4-03','UI_DESIGN.md §3.1; PROJECT_PLAN.md §6.7','Coordinator only; all four space settings; buildings first; capacity uncertainty; candidate sentence and protection/ordnance warning'),
('ScreenInspector','GET /areas/{id}/values; /layers/{id}/timeseries; /areas/{id}/validation; /values/{id}/trace','MVP; validation conditional','M4-02','UI_DESIGN.md §3.1','All agents/Time series/Validation tabs; Escape closes; focus returns; source trace; unavailable validation explicitly shown'),
('ScreenSources','GET /sources; /sources/{id}; /values/{id}/trace','MVP','M4-03','UI_DESIGN.md §3.1','Large NISAR core tile and pass strip; NASA next; provenance, dates, terms, uncertainty and actual model tests'),
('ScreenMobile','Same authorized alert/summary/routes contracts','MVP basic responsive; PWA deferred','M4-04','UI_DESIGN.md §1/3','Phone browser alerts/summary/routes; readable focus order, offline/cached status; no separate native app'),
]
components=[
('EvidenceLabel','MetricValue / AlertDetail / all derived outputs','M4-01','Four words and distinct icons/shapes; no colour-only meaning'),
('DamageClass','GET /areas/{id}/damage','M4-02','Hatched square/diamond/triangle/dashed circle; every class candidate; combined severe/destroyed if model cannot distinguish'),
('FacilityStatus','GET /areas/{id}/facilities','M4-03','H/C/S/W/P symbols; reported working only; no-damage ≠ open'),
('RangeValue','MetricValue in summary/people/values','M4-01','Round display to 100 below 10,000 and 1,000 above; preserve raw low/high for trace; never display null as zero'),
('SourceLine','SourceRecord / GET /values/{id}/trace','M4-01','Dataset, detail, date, NASA tag and DataAge; numbered print footnote'),
('DataAge','GET /status and per-value freshness/cached','M4-01','Date first; Fresh dot/Aging ring/Stale diamond/Cached dashed ring; show last-success and failures'),
('AlertCard','GET /alerts','M4-02','Type, area, source, time, label; attention bar not flashing or red'),
('RouteOption','POST /routes and GET /routes/{id}','M4-03','Seven fixed facts plus unknowns/revision warning; never safe'),
('ShelterCard','GET /shelters','M4-03','Rank/capacity assumptions/For checking; only authorized response'),
('TimeSlider','Layer.available_acquisitions and GET /layers/{id}/timeseries','M4-02','Actual pass dates only; gap dotted; before dashed/after solid; Before/Change/After/Swipe; swap dates requires valid ordering'),
('LayerToggle','GET /layers and layer metadata','M4-02','Symbol, source date and age; server denies private layer regardless of UI state'),
('MapLegend','GET /layers plus active client state','M4-02','Only active layers; above 8 layers Focus mode dims data backgrounds; patterns preserved'),
('SystemStates','GET /status; all errors','M4-01','Distinct loading/no-data/Unknown/Stale/offline/delay/denied states; visible synthetic badge'),
('Button','Screen primary endpoint/action','M4-01','One primary action per view; accessible name, disabled/busy/focus states and keyboard activation'),
]
doc(names[6],'Frontend design and screen plan',f'''
## Implementation contract

React + Vite + MapLibre GL JS, IBM Plex Sans text and IBM Plex Mono numbers/dates/sources. Source: UI_DESIGN.md §§1–7 and ARCHITECTURE.md Part 4. Readable light/dark themes, neutral background, NASA blue main actions/NISAR, violet candidate radar change, amber-brown attention. Outlined points and hatched area layers preserve map readability. Tokens are CSS variables; exact remote mockup colour/spacing values remain VERIFY because the external artifact could not be opened. Do not invent pixel-perfect fidelity.

ARCHITECT RECOMMENDATION: TypeScript client generated from reviewed OpenAPI, local fixture adapter selected by explicit demo flag, never a silent real-data fallback. Display “Illustrative demo data” on every synthetic map, panel and export. A mixed-source response flags individual synthetic values and the whole screen. Client calculations may format, not fabricate domain estimates. Source UTC timestamps render alongside explicit local timezone in alert details.

## All eleven views

{table(['View','API under /api/v1','Priority','Owner task','Source','Acceptance'],screens)}

## All fourteen shared components

Every row traces to UI_DESIGN.md §4, with §5 for wording/style; API links are draft contract mappings. Components are MVP except optional offline enhancements.

{table(['Component','Contract/API','Owner task','Acceptance'],components)}

## Interaction and accessibility acceptance

Map→area callout→summary→print is at most three actions; alert→detail→compare routes at most two. Authorized facility/area→route intent is one action, but server still checks role and scope. Route/shelter options must not preload in analyst state. Main top bar exposes freshness for NISAR/Sentinel-1/lights/fires/internet, including unavailable sources. Left/right rails collapse without losing focus, shortcuts do not fire while typing. Inspector Escape restores triggering focus. Before/after/swap/swipe respect missing passes and preserve explicit acquisition dates.

ARCHITECT RECOMMENDATION: WCAG 2.2 AA target, visible focus, semantic landmarks, labelled inputs, keyboard-accessible non-map lists, contrast checks in both themes, reduced motion, minimum comfortable touch targets. Check phone widths 360/390 px, desktop 1280 px and 200% zoom. A map-only interaction must have an equivalent list/control. No red/flashing urgency animation.

A4 brief contains people first, what-to-bring basis, vulnerable groups, facility/hazard caveats and numbered citations; no secret route/shelter details for analyst exports. QR encodes authenticated application path only, never an access token or exact coordinates. Basic browser Save as PDF is the MVP export; server PDF generation and offline persistence are deferred. At H38 audit every displayed metric against its fixture/real lineage and source date.

## Public and offline policy

Public view serves only publication-approved r8 aggregates with additional suppression. No sensitive population concentration or undamaged critical-site inventory appears in tiles, inspector or hidden JSON. Logged-out preview has explanatory sign-in affordances. No public brief, route, shelter or dispatch endpoint is introduced.

PWA installable public shell is stretch; restricted offline storage is post-hackathon. Protected responses use no-store, no service-worker cache, no browser localStorage tokens. On logout/role change remove private map sources, in-memory query caches, print models and any temporary download URLs. Offline mode shows last-known timestamps only where policy allows retention; it never claims a cached route is current.
''')

doc(names[7],'Security, privacy and RBAC','''
## Non-negotiable protection rules

Sources: PROJECT_PLAN.md §§9–10; ARCHITECTURE.md §3.3; UI_DESIGN.md §§5–6; DATA_AND_API_PLAN.md §4; PDF p2 §4. Civilian humanitarian use only. Exclude military sites, frontline information, targeting, live people/phone/vehicle/convoy tracking. Do not publish shelter/displacement sites, exact routes/dispatch reports, identifiable civilian concentrations or an inventory of undamaged critical infrastructure. No field-use assurance follows from a hackathon pass.

## Role and resource matrix

ARCHITECT RECOMMENDATION: cumulative functional capabilities below, always intersected with explicit area scope and resource tags. Admin is not a bypass for publication delay, licensed access or object scope. Team leader must assign actual names later; no real accounts are provisioned by planning.

| Resource/action | Anonymous | Analyst | Officer | Coordinator | Admin |
|---|---|---|---|---|---|
| Sanitized r8 public preview, safe source catalogue/status | Yes | Yes | Yes | Yes | Yes |
| Scoped damage/people/services/alerts/validation | No | Yes | Yes | Yes | Yes |
| Exact critical-site inventory | No | Need-to-know subset only | Scoped operational subset | Scoped operational subset | Scoped only |
| Routes and closure reports | No | No | Yes | Yes | Yes |
| Confirm closure (separate review) | No | No | No | Yes | Yes |
| Shelter coordinates/capacity/field checks | No | No | No | Yes | Yes |
| Area brief / print / source trace | No | Own permitted sections | Own permitted sections | Own permitted sections | Own permitted sections |
| User roles, jobs, redacted audit | No | No | No | No | Yes |

Every endpoint and every file performs: authenticate → capability → area scope → object tag/licence → release time → projection/field filtering. A guessed ID, alternate download URL, Range request, HEAD request, PMTiles range, COG tile, GeoJSON, brief, trace or cache hit must not bypass policy. Deny default. No storage folder is directly mounted by a public static server. Policy runs before fetching restricted object data; errors/logs are scrubbed.

## Publication delay and suppression

For newly published strike-related change, `release_at >= acquisition_end + 72 hours`; API, tiles, derived alerts, reports and source trace enforce the same UTC gate. Unknown acquisition time means hold, not immediate release. Late processing cannot reduce the minimum delay. Restricted operational field reports have separate role policy; they cannot publish withheld radar evidence through a derivative. Default deny precise public buildings even after 72 h.

Public publication requires r9→r8 aggregation, removal of precise geometry and sensitive fields, licence approval and humanitarian protection review. H3 r8 alone can still identify concentrations: suppress small/unique/high-risk cells and revealing differencing across successive snapshots. ARCHITECT RECOMMENDATION: no automatic population or facility layer publication until Member 3 reviews the sanitized demo with Member 2; use synthetic public cells if a safe threshold cannot be justified. Never pretend a fixed population threshold guarantees protection.

## Sessions and server secrets

ARCHITECT RECOMMENDATION: server-side sessions using random opaque token stored hashed, HttpOnly/Secure/SameSite=Lax cookie, short idle timeout and eight-hour maximum demo session. Local HTTP development may use an explicit nonproduction insecure-cookie setting only on loopback. Login rate limiting and session rotation; logout/revocation invalidates all cached permissions. Use password hashing with a maintained library; credentials supplied locally, no committed default working passwords. Mutation endpoints require CSRF token and Origin check; CORS allowlists exact app origin. Production needs reviewed identity lifecycle/MFA.

Earthdata/FIRMS/ACLED/DTM credentials live only in server environment or secret store. `.env.example` contains empty placeholders. No `VITE_` secret variables, browser tokens, source maps with sensitive fixtures, credentials in Git, screenshots or request logs. FIRMS key may be in URL path; redact upstream request paths too. SQL parameter binding, input schemas, bounded geometry/time queries, no arbitrary remote URLs, allowlisted source fetch destinations and archive path validation prevent injection/path traversal/SSRF. Separate DB migration, API and worker credentials.

## Sensitive flow and threat checks

```mermaid
flowchart LR
  U[Authenticated scoped user] --> P[Session role area object policy]
  P --> R[Private route/shelter function]
  R --> F[Field filtering and evidence policy]
  F --> U
  R --> A[Redacted audit]
  Private[Private granules and results] --> Delay[72 h delay gate]
  Delay --> Aggregate[H3 r8 aggregation]
  Aggregate --> Review[Concentration and licence review]
  Review --> Public[Separate public-safe artifacts]
```

Threats: IDOR across areas; analyst requesting shelter in summary/brief/trace; guessed PMTiles file; CSRF closure submission; role downgrade with stale cache; external routing/map telemetry; response-size/bbox abuse; source poisoning; leaked debug logs; fine-resolution time differencing. Tests in T-RBAC/T-LAYER/T-CACHE/T-DELAY/T-SAFETY exercise these, with synthetic data only.

## Retention and cache design

ARCHITECT RECOMMENDATION pending data owners: no sensitive real operational data in the hackathon. If later authorized, expire route request details within 24 h, briefs/private artifacts at event-defined expiry, audit metadata after 30 days unless terms require shorter/longer retention. Retention dates and deletion jobs require owner review before ingestion; no deletion is performed by this plan. Raw licensed data retention follows source terms. Backups inherit encryption, ACLs and expiry; deletion must cover copies and caches. Preserve non-sensitive manifests/checksums for reproducibility without retaining prohibited content.

Protected API/files `Cache-Control: private, no-store`, no CDN caching, service worker bypass, no signed URLs that outlive role revocation. Shared proxy caches key by public publication version only. Clear client state on logout/role change; refuse stale restricted saved routes. Public offline shell may cache only approved sanitized assets. No restricted data enters external LLMs; future fixed-question helper cannot send user-entered sensitive coordinates either.

## Required deny demonstration and operational warning

Anonymous `/api/v1/shelters` → 401. Analyst same path, capacity POST, guessed detail via field-check path, summary expansion, file, trace and print → 403 or authorized payload with shelter fields absent. Officer has route rights but still cannot retrieve shelter coordinates; coordinator can only in permitted area. Same role in other area → 403. This must be server evidence, not just a hidden button.

UI and briefs: “Candidate for checking. Field verification required.” Remote sensing cannot prove route passability, operating services, structural integrity or absence of explosive ordnance. Production deployment requires humanitarian protection and scientific expert validation beyond hackathon acceptance. No paid hosting, real deployments or external dispatch messages were authorized or performed in this planning work.
''')

# Each task has a single accountable member, one reviewer and an explicit artifact handoff.
tasks=[
('M1-01','Scene discovery, licence and tier preflight','Member 1','Member 2','MVP','H0–H8; 5 active h plus download wait','none; H2 contract freeze','ARCHITECTURE.md §1.1; DATA_AND_API_PLAN.md §§1–2; NASA_DATASET_ANALYSIS.md §9','Search BETA/provisional/V1, save actual overlap, track/frame, acquisition/version, download tiers only during development.','pipelines/radar/discover.py; data/manifests/nisar.json; pipelines/radar/config/demo_aoi.json','metadata-only synthetic granules, missing-pass list','AOI + collection IDs → versioned granule manifest','python -m pytest tests/geo/test_manifest.py','T-DATA, T-LICENCE: duplicate versions, gap retained, wrong track, unavailable credentials','H2 IDs and manifests to M3; H8 registered crop inputs to M1-02','Network, disk, Earthdata; bounded retries or explicitly synthetic data; never claim acquisition'),
('M1-02','Radar transformations, model and artifacts','Member 1','Member 2','MVP','H2–H24; 14 active h','M1-01; M2-01 grid; M3-01 schema','ARCHITECTURE.md §§1.3/1.5; DATA_AND_API_PLAN.md §1','Registration, masking, version normalization, HH/HV features, quiet blocks, Isolation Forest/Mahalanobis, fallback, reason codes and COGs.','pipelines/radar/process.py; pipelines/radar/model.py; data/private/damage_cells.parquet; data/private/change/*.tif; data/manifests/radar_run.json','small synthetic arrays and H3 cells; no war-zone geometry','granules + grid → damage_cells v0.1 + COG index','python -m pytest tests/geo/test_radar.py tests/unit/test_model.py','T-RADAR, T-GEO, T-ML: nodata, units, >3 dB share, quantiles, registration and drift','H16 first cells M2/M3; H24 COG/time-series manifest M3','Cross-version bias; stop invalid comparisons, retain Unknown; z-score only if valid features'),
('M1-03','Scientific QA and validation availability','Member 1','Member 4','MVP QA; overlay conditional','H24–H32; 6 active h','M1-02; permitted M2-03 context','ARCHITECTURE.md §§1.2/1.4; NASA_DATASET_ANALYSIS.md §9','Spatial hold-out, enrichment with controls, 20 manual top cells, uncertainty report; verify UNDP/CNRS-L without promising UNOSAT.','pipelines/radar/evaluate.py; data/manifests/model_tests.json; docs/model_validation.md (implementation output)','fixed synthetic score distribution and manual-review checklist','cells + hold-out + reports → measured test results and limitations','python -m pytest tests/unit/test_evaluation.py','T-ML, T-VALIDATION: no leakage; duplicate reports; false-alarm numerator/denominator; no fake accuracy','H32 QA results to M3 trace and M4 Sources','No aligned labels; report independent QA, no precision/recall or confirmed collapse claims'),
('M1-04','Conditional coherence and cross-sensor experiment','Member 1','Member 2','Stretch / later','H24–H36 only if core green; max 4 active h; otherwise after hackathon','M1-02 and M1-03 gates','ARCHITECTURE.md tier C/stretch; NASA_DATASET_ANALYSIS.md §§2/3.1','OPERA cross-check, track172, NISAR_COP note; GSLC/GUNW coherence only with validity evidence.','pipelines/radar/crosscheck.py; data/manifests/optional_features.json','disabled-feature fixture; unavailable GUNW state','aligned products → optional feature + QA, never silently required','python -m pytest tests/geo/test_crosscheck.py','T-COHERENCE, T-DISPLAY: baseline mismatch rejects; GIBS never analytical; schedule provisional','H36 go/no-go with M4; nothing new after H38','Huge downloads/cross-gap decorrelation; omit feature and disclose'),
('M2-01','Source register, grids and base geometry','Member 2','Member 1','MVP','H0–H12; 6 active h','M3-01 shared schema; source terms','ARCHITECTURE.md §2.1; DATA_AND_API_PLAN.md §3; DATASETS.md §7','HOTOSM/admin/WorldPop/GHSL/NASADEM preflight; stable H3/cadaster joins; licence register.','pipelines/geodata/ingest.py; pipelines/geodata/grid.py; data/manifests/sources.json; data/private/base_layers.gpkg','synthetic tiny buildings/roads/grid; licence-unverified fixture','licensed extracts → grid/crosswalk/source records/base layers','python -m pytest tests/geo/test_grid.py tests/geo/test_ingest.py','T-GEO, T-LICENCE: CRS/invalid geometry/admin boundaries/levels precedence','H2 IDs to all; H12 base grid/residents/facilities inputs M3','Unavailable licence/download; tiny synthetic bounded fixture, no raw redistribution'),
('M2-02','People, facilities, services and report model','Member 2','Member 1','MVP','H8–H24; 7 active h','M2-01; M1-02 H16 cells; M2-03 services','PROJECT_PLAN.md §§6.2–6.6/8; ARCHITECTURE.md §2.2','Mass-conserving baseline, scenario ranges, vulnerable groups, five severity parts, reported operating state, source-linked what-to-bring.','pipelines/geodata/people.py; facilities.py; services.py; report.py; data/private/area_values.parquet','AreaSummary and MetricValue fixtures owned for UI packaging by M4','cells + baseline + reports → MetricValue[] and AreaSummary','python -m pytest tests/unit/test_people.py tests/unit/test_services.py','T-PEOPLE, T-FACILITY, T-SERVICES: uncertainty, no overlap double count, unknown ≠ zero, hospital not inferred open','H12 baseline to M3; H24 joined real-data summary to M3/M4','Missing demographics/operating report → Unknown; no invented current displaced count'),
('M2-03','Hazard adapters, dedup and corroboration','Member 2','Member 1','MVP bounded sources','H8–H24; 6 active h','M2-01 source terms; M3-04 scheduler','ARCHITECTURE.md §2.2; PROJECT_PLAN.md §§5a/6.8b','FIRMS, Black Marble archive/NRT, IODA adapters; licensed ACLED/Insecurity context; source independence and alert review domain.','pipelines/alerts/{firms,lights,ioda,corroboration}.py; data/private/alerts.geojson','sanitized HTTP fixtures for success/timeout/rate limit; no keys','bounded observations → AlertDetail + freshness; callable adapters','python -m pytest tests/unit/test_alerts.py','T-ALERT, T-INDEPENDENCE: 1km/12h cluster, two clear nights, duplicate rehosts, cached timestamp','H16 callable jobs to M3; H24 alerts to M4','FIRMS key/ToS blocked; visibly synthetic or Cached with last-good date; no claim live tested'),
('M2-04','Private graph, alternatives and closures','Member 2','Member 1','MVP','H24–H32; 5 active h','M2-01 roads; M3-02 policy; M3-03 endpoint','PROJECT_PLAN.md §6.5; ARCHITECTURE.md §2.2; DATA_AND_API_PLAN.md §4','2–3 distinct in/out routes; seven facts; unknown road status; confirmed closure invalidation; no external routing.','pipelines/routing/graph.py; routes.py; closures.py; data/private/demo_graph.graphml','tiny synthetic graph with three options, bridge, unknown edge and disconnected case','authorized route intent + graph revision → RouteOption[]','python -m pytest tests/unit/test_routes.py','T-ROUTE: avoid confirmed closures, fewer paths explain, unknown heavy suitability, no network call','H32 callable and revision tests to M3; seven facts to M4','Disconnected/incomplete graph → fewer/no route with warning, never fabricated third option'),
('M2-05','Shelter scoring and capacity ranges','Member 2','Member 1','MVP buildings; open land lower priority','H16–H32; 4 active h','M2-01; M1-02; M2-02; M3-02','PROJECT_PLAN.md §6.7; DATA_AND_API_PLAN.md §3','Buildings first, configurable modes, uncertain floor-area estimate, access/hazard caveats, field-check requests; scoped open-land screen.','pipelines/shelter/candidates.py; capacity.py; data/private/shelter_candidates.parquet','redacted ShelterCandidate example and synthetic candidate geometries','authorized area + assumptions → ranked candidates + capacity range','python -m pytest tests/unit/test_shelter.py','T-SHELTER: modes, bounds, missing levels/GHSL, known hazard exclusion; never certify safety','H24 first list; H32 final callable M3/M4','Height and structural uncertainty; type default explicitly labelled or no capacity; cut open land before buildings'),
('M2-06','Movement and global backlog specification','Member 2','Member 3','Stretch movement; global after hackathon','No core allocation; max 1 h design; implementation after core','M2-02; licences; M3-02 privacy','PROJECT_PLAN.md §§5/6.8; ARCHITECTURE.md stretch','DTM/Meta coarse delayed trends; future watch list and selective processing; no individual/camp coordinates.','docs/backlog/movement_global.md; future pipelines/geodata/movement.py','unavailable/disabled trend fixture','permitted coarse reports → delayed trend, not live people','python -m pytest tests/unit/test_movement.py (after implementation)','T-MOVEMENT, T-BACKLOG: aggregation/delay, no individual payloads','H38 record deferred scope; later approved iteration','Licences, cadence, sample bias; stay disabled'),
('M3-01','Contract freeze, database and loaders','Member 3','Member 4','MVP','H0–H12; 7 active h','M1/M2 identifiers and fixtures','ARCHITECTURE.md Agree at hour2/§3.1; UI_DESIGN.md §2.1','Review OpenAPI, implement PostGIS migrations/schema and transactional manifest loaders; mock endpoints.','backend/app/schemas/; backend/migrations/; backend/app/loaders.py; backend/app/main.py','use docs/contracts JSON; M4 packages mock client fixtures','manifest + canonical row → validated DB + versioned API','python -m pytest tests/api/test_contracts.py tests/geo/test_database.py','T-CONTRACT, T-SQL: FK/check/CRS/idempotency/atomic rollback','H2 v0.1 freeze; H12 mock API to M4','Schema mismatch; contract PR first; do not silently coerce fields'),
('M3-02','Authentication, policy and protected storage','Member 3','Member 4','MVP invariant','H2–H16 plus H32–H38 audit; 8 active h','M3-01; source safety rules','ARCHITECTURE.md §3.3; PROJECT_PLAN.md §10; UI_DESIGN.md §6; PDF p2 §4','Sessions/CSRF, RBAC+area/object tags, release gate, public sanitization, protected tiles/files/export, redacted audit.','backend/app/auth/; backend/app/policy/; backend/app/api/layers.py; tests/security/','five demo roles and out-of-scope user, synthetic secrets only at runtime','session + resource + time → allow/filter/deny','python -m pytest tests/security','T-RBAC, T-LAYER, T-DELAY, T-CACHE, T-SAFETY: 401/403, Range, alternate path, logout and clock boundary','H12 role API; H24 protected data; H38 release blocker review','Auth/file bypass → no external demo link; localhost synthetic only'),
('M3-03','Domain API and evidence/brief integration','Member 3','Member 2','MVP','H8–H32; 8 active h','M3-01/02; M1-02; M2-02/03/04/05','ARCHITECTURE.md §§3.2/3.4; PROJECT_PLAN.md §8.1','All area/alerts/routes/shelters/trace/brief endpoints with bounded queries, evidence, errors and same export filters.','backend/app/api/{areas,alerts,routes,shelters,sources,briefs}.py; backend/app/services/','essential eight JSON contracts and collection wrappers','domain callables → role-filtered HTTP response','python -m pytest tests/api','T-CONTRACT, T-TRACE, T-BRIEF: examples, lineage, role-filtered exports, unavailable sources','H24 real-data API; H32 routes/shelters/sources UI handoff','Late domain inputs; fixtures remain explicit synthetic; do not invent server measurements'),
('M3-04','Orchestration, Compose, CI and recovery','Member 3','Member 1','MVP; sensitive offline/LLM later','H0–H38; 6 active h plus H40 backup','M2-03 adapters; M3-01/02','ARCHITECTURE.md §§3.1/3.4; PROJECT_PLAN.md §8 Orchestrator/Safety','One worker scheduler, retry/cached state, job leases, Docker, env template, CI, metrics and rollback; free tunnel only after checks.','worker/main.py; infra/compose.yaml; .env.example; .github/workflows/ci.yml; scripts/{preflight,load_demo,verify_demo}.py','no-network adapter fixture; failure injection; synthetic demo bundle','schedule + adapter results → atomic stored snapshot/status','docker compose -f infra/compose.yaml config; python -m pytest tests/unit/test_jobs.py','T-JOBS, T-DEVOPS: retry idempotence, cached failure, restore and no secret logs','H2 environment skeleton; H16 scheduler; H32 verified link if available; H40 backup','Docker/tunnel unavailable → localhost + recorded demo; no paid service; offline/LLM remain later'),
('M4-01','App foundation, design system and mock client','Member 4','Member 3','MVP','H0–H12; 7 active h','M3-01 H2 freeze; UI source','ARCHITECTURE.md Part4; UI_DESIGN.md §§1/4/5/6','Vite React MapLibre, token variables/themes, shared evidence/range/date controls, sign-in/public view, typed fixtures.','apps/web/src/{api,mocks,components,theme}; apps/web/src/screens/SignIn.tsx; PublicPreview.tsx','copy reviewed contracts, synthetic badges and all error states','OpenAPI/fixtures → accessible client shell','npm --prefix apps/web run test; npm --prefix apps/web run build','T-UI, T-CONTRACT: no secret in bundle, mock badge, accessible components','H2 client shapes; H12 sign-in and public preview','External design inaccessible → use written design, mark exact tokens VERIFY'),
('M4-02','Main map, timeline, feed and inspector','Member 4','Member 1','MVP','H8–H24; 7 active h','M4-01; M3-03; M1-02 layers','UI_DESIGN.md §§3.1/4; ARCHITECTURE.md §4.2','Main map, missing passes, HH/HV, swipe/swap, folding rails, alert feed, per-agent inspector/time series/validation states.','apps/web/src/screens/{ScreenMainMap,ScreenInspector}.tsx; components/{TimeSlider,LayerToggle,MapLegend,AlertCard}.tsx','Layer/AlertDetail fixtures with missing interval and denied tile','layer metadata + series → MapLibre presentation only','npm --prefix apps/web run test -- map timeline','T-UI, T-DISPLAY: no fabricated pass, denied source not loaded, only active legend','H16 map on fixtures; H24 real-data layers','COGs late → clearly synthetic layer; metadata never claimed as analysis'),
('M4-03','Decision screens, sources and print','Member 4','Member 3','MVP','H16–H32; 9 active h','M3-03; M2-02/04/05; M1-03','UI_DESIGN.md §§2/3.1; ARCHITECTURE.md §§4.2/4.3','Alert, summary, routes, shelters, Sources and A4 brief; source trace; review/field-check affordances; deny demo.','apps/web/src/screens/{ScreenAlertDetail,ScreenAreaSummary,ScreenAreaBrief,ScreenRoutes,ScreenShelters,ScreenSources}.tsx; print.css','all essential contract examples; role variants; no live sensitive coordinates','authorized APIs → people-first screens + role-filtered A4','npm --prefix apps/web run test -- screens print','T-BRIEF, T-TRACE, T-UI: seven route facts, warnings, footer sources, analyst shelter denial','H24 summary/alert; H32 route/shelter/source; H38 print','M2 workload → implement against fixtures early; never fake actual provenance'),
('M4-04','Responsive QA, demo and submission','Member 4','Member 3','MVP; PWA shell stretch','H32–H48; 7 active h plus coordinated rehearsal','all MVP tasks; M1-03 science report; M3-02 security','ARCHITECTURE.md §4.3/Timeline; UI_DESIGN.md §§1/5','Phone layouts, keyboard/contrast, mock-real audit, end-to-end story, video, citations, final release checklist.','apps/web/src/screens/ScreenMobile.tsx; tests/e2e/; docs/demo_runbook.md; submission text; video outside Git','offline/failure scenarios; local recorded backup','approved build + evidence → reproducible judge walkthrough','npm --prefix apps/web run test:e2e; npm --prefix apps/web run build','T-A11Y, T-E2E, T-SUBMIT: role denial, failure fallback, full trace, citations','H38 freeze; H40–44 video; H44–48 submission','No verified hosting → recorded/local demo; protected offline deferred'),
]
taskfiles={1:'MEMBER_1_RADAR_ML.md',2:'MEMBER_2_GEODATA_ALERTS.md',3:'MEMBER_3_BACKEND_SECURITY.md',4:'MEMBER_4_FRONTEND_DEMO.md'}
for member,filename in taskfiles.items():
    own=[t for t in tasks if t[2]==f'Member {member}']
    text=f'# Member {member} work package\n\n[Team allocation](../08_FOUR_MEMBER_TASK_ALLOCATION.md) · [Roadmap](../09_48_HOUR_DEVELOPMENT_ROADMAP.md) · [Contracts](../contracts/README.md)\n\nStatus: planned implementation, not completed work. File paths below are proposed outputs, not present application code. Effort means active work within the given window; allow breaks and integration buffer. All implementation details beyond cited source are ARCHITECT RECOMMENDATION.\n'
    for t in own:
        id,title,owner,reviewer,priority,effort,dep,trace,scope,outputs,stub,io,cmd,test,gate,fallback=t
        text+=f'\n## {id}: {title}\n\n'+table(['Field','Commitment'],[
            ('Source trace',trace),('Scope',scope),('Priority / phase',priority),('Accountable owner',owner),('One reviewer',reviewer),('Dependency',dep),('Expected files / outputs',outputs),('Required stub / mock',stub),('Effort and hackathon window',effort),('Input / output contract',io),('Local verification (planned)',f'`{cmd}`'),('Test cases',test),('Definition of Done',f'Expected artifacts committed in a small PR to dev; {reviewer} reviews tests and source/safety implications; contracts and lineage validated; fixture/real status declared; receiving task acknowledges handoff. Scientific failures stay visible and block unsupported claims.'),('Integration checkpoint',gate),('Blockers / fallback',fallback)])
        text+='\nHandoff checklist: include schema version, exact artifact paths, units/CRS/date, checksum/run ID, sensitivity and licence tags, known gaps, reproduction command, test result and receiving member acknowledgement. No credentials or raw sensitive files in PR.\n'
    write('tasks/'+filename,text)

doc(names[8],'Four-member ownership and handoffs',f'''
## Accountable roles

Source: ARCHITECTURE.md Parts 1–4; user requires exactly four members. No names invented. Exactly one member is accountable per task; reviewer is a different member. Domain ownership does not transfer when M3 exposes an API or M4 builds its presentation.

| Member | Primary responsibility | Task package | Feature branch from dev |
|---|---|---|---|
| Member 1 | Radar / remote sensing / ML | [M1 tasks](tasks/MEMBER_1_RADAR_ML.md) | feature/m1-radar-damage |
| Member 2 | Geodata / humanitarian analytics / alerts / local routes / shelters | [M2 tasks](tasks/MEMBER_2_GEODATA_ALERTS.md) | feature/m2-geodata-alerts |
| Member 3 | Backend / DB / safety / orchestration / DevOps | [M3 tasks](tasks/MEMBER_3_BACKEND_SECURITY.md) | feature/m3-backend-security |
| Member 4 | Frontend / UI fixtures / QA-demo / submission | [M4 tasks](tasks/MEMBER_4_FRONTEND_DEMO.md) | feature/m4-frontend-demo |

## Shared dependency matrix

{table(['Task','Owner','Reviewer','Dependency','Checkpoint'],[(t[0],t[2],t[3],t[6],t[14]) for t in tasks])}

## RACI

R/A = one accountable implementer; C = named cross-review or domain consultation; I = notified. Team-wide gates have one accountable gate owner, with each member responsible for their own input.

| Deliverable | Member 1 | Member 2 | Member 3 | Member 4 |
|---|---|---|---|---|
| Radar cells and scientific QA | R/A | C | I | C |
| Geodata, population, alerts, route/shelter algorithms | C | R/A | C | I |
| API/schema/auth/policy/protected storage | I | C | R/A | C |
| Job scheduling, retries, CI and deployment | C | C | R/A | I |
| UI/components/typed mock fixtures | C | I | C | R/A |
| H2 contract freeze | C | C | R/A | C |
| H24 real-data integration gate | C | C | R/A | C |
| H38 full rehearsal and feature freeze | C | C | C | R/A |
| Video/submission/citation assembly | C | C | C | R/A |

## Workload balance

M2 core tasks total about 28 active hours plus at most one hour backlog design. This is still the bottleneck. Start tiny bounded data and route/shelter fixtures early; no global watch list, movement pipeline or broad environmental datasets in core. M3 owns scheduler/leases/retries/loaders; M4 owns UI contract fixtures and screen state handling. M1 reviews M2 CRS, capacity and population joins. Support is explicit review/integration work; M2 retains algorithm accountability. M1 ~25 core active hours plus ≤4 optional; M3 ~29; M4 ~30. Remaining elapsed time is downloads, review, breaks, integration and contingency, not an assumption of 48 uninterrupted working hours.

## Team conventions

Freeze H3 IDs, row fields, units/CRS, dataset manifests, evidence enums, file naming and eight essential JSON contracts at H2. A later change starts with an API/schema PR and receiving-member acknowledgement. Use source/run IDs in filenames; UTC internal time; source precision retained; snake_case JSON fields; no bare scalar estimates; no secret fixtures. Small PRs at H2/H8/H16/H24/H32 rather than one giant member branch at H48. Every PR has one reviewer, source trace, tests, known limits and whether data is synthetic.

Contacts remain placeholders: Member 1 [name/contact pending], Member 2 [pending], Member 3 [pending], Member 4 [pending]. Handoffs fail if the receiver cannot reproduce the artifact or the manifest omits evidence, dates, units, sensitivity or schema version.
''')

gates=[
('H0–H2','Member 3','M1 manifests/account preflight; M2 source register/H3 IDs; M3 Compose/contracts; M4 app+fixture shell','Clean branch, available tools, source rights and rules review','T-DATA/T-LICENCE/T-CONTRACT','H2: version 0.1 row/API/file contract acknowledged by all four; otherwise block divergent feature work, continue fixtures'),
('H2–H8','Member 1','Radar crop/registration QA; M2 grid and baseline; M3 PostGIS/session; M4 mock main map','M1-01 and H2 contract','T-GEO/T-RADAR/T-SQL','Common valid before/after pixels and version metadata present; otherwise synthetic demo declared and real radar gate remains blocked'),
('H8–H16','Member 2','M1 first damage cells; M2 road graph/live adapter callables; M3 mock endpoints/scheduler; M4 time slider/feed','H8 data + contract','T-ML/T-ALERT/T-CONTRACT','H12 grid/facilities and mock auth; H16 M1→M2/M3 cells validated; failures retain Unknown and documented fallback'),
('H16–H24','Member 3','M1 COG/pass index; M2 people/shelter/alert joins; M3 real loads; M4 summary/alert detail','H16 artifact manifests','T-PEOPLE/T-FACILITY/T-SHELTER/T-TRACE','H24 real-data vertical slice from one valid NISAR pair through map. If absent, explicit reduced synthetic walkthrough, no real-data success claim'),
('H24–H32','Member 3','M1 model QA/optional cross-check; M2 route alternatives/closure revision; M3 protected endpoints; M4 routes/shelters/Sources','H24 slice, source permissions','T-ROUTE/T-RBAC/T-LAYER/T-ML','H32 exact-role denial and local routing pass; no external link if privacy gates fail'),
('H32–H38','Member 4','Security/fixture-real audit, responsive/print, freshness, full rehearsal','All MVP tasks','T-E2E/T-A11Y/T-BRIEF/T-CACHE','H38 feature freeze; privacy/provenance blockers prevent publication. Optional work only ships if already green'),
('H38–H44','Member 4','Fixes only; backup restore M3; model/source caveat review M1/M2; record video H40–44','Frozen build and rehearsed script','T-DEVOPS/T-E2E','Backup laptop or recorded demo works without external APIs; no new optional feature'),
('H44–H48','Member 4','Submission text/video, dataset citations, repository/security/accessibility checklist, release candidate','H44 backup and citations','T-SUBMIT/T-LICENCE/T-SAFETY','Tag only tested reviewed commit; unresolved validation/hosting disclosed to judges; team release decision recorded'),
]
doc(names[9],'48-hour development roadmap',f'''
## Milestones and go/no-go gates

Source: ARCHITECTURE.md Putting it together/Timeline, Parts 1–4 handoffs, de-scope order; user request §8. This is the future development weekend, not work already executed by this planning task. No radar download starts during planning.

{table(['Window','Accountable gate owner','Exact outputs by member','Dependency','Test gate','Go/no-go'],gates)}

## First two hours

H0–H0.5: M3 confirms clean clone/dev history and tooling, M1 metadata and Earthdata access, M2 rights/coverage and small source manifests, M4 written UI/reference accessibility. Recheck current challenge preparation rules; no assumption that pre-downloading is allowed. H0.5–H1: start A then B downloads only in actual development; M2 makes grid/schema fixture, M3 starts DB/session stub, M4 renders labelled synthetic base map. H1–H2: all four review area IDs, canonical rows, units, CRS, artifact names, eight mock JSON shapes and denial cases; M3 publishes contract v0.1, M4 consumes it. Unresolved data facts remain VERIFY and do not become implicit schema values.

## Critical path

```mermaid
flowchart LR
  A[Permitted A/B download] --> B[Crop registration version QA]
  B --> C[H16 radar cells]
  C --> D[Population and facility join]
  D --> E[H24 backend data integration]
  E --> F[Real map and summary]
  Contract[H2 frozen API contract] --> E
  Contract --> Mock[Frontend mock work]
  Mock --> F
```

The API contract itself freezes before radar work finishes. The later critical-path API step is loading real data into that agreed contract. Blocking M1→M2 delivery threatens population estimates and the map, so M2/M4 work against the same small fixture early.

## Resource budgets (estimates, not benchmarks)

Source radar sizes: A 7.7 GB + B 6.8 GB = 14.5 GB must-have; C ~15 GB optional. At 20 Mbit/s, payload-only 14.5 GB takes about 1.6 h; protocol/retries can lengthen it. ARCHITECT RECOMMENDATION: reserve 50 GB free for A/B, crops/temporary files/DB; 80–100 GB if tier C retained. Confirm actual size/free disk before download; skip tier C if budget fails. Crop and stream in windows; share only authorized cropped outputs. Target a laptop with 16 GB RAM and 4 CPU cores, one radar processing job at a time, limit tile conversion memory; no GPU requirement or unmeasured speed promise. Keep a 4–8 GB worker memory budget initially and record runtime/RSS on first crop. PostGIS + API + web share host; rates are bounded by demo AOI, not global scale.

## De-scope and contingency

Cut optional LLM first, then coherence, then responsive/print polish (retain usable field views and printable brief), then open-land shelters (keep buildings), then later passes after July (retain real before/after and honest gaps). Every cut updates feature status and acceptance report. Never remove NISAR demonstration, sign-in/roles, provenance, public delay/aggregation or safety. Loss of scientific data cannot be hidden by screenshots: demonstrate synthetic behavior with a visible label, record real-data MVP as blocked, and show the metadata/validation blocker.

Source outages: last-good timestamped Cached result; no previous result → Unknown/unavailable. No credentials: use no-network fixtures, do not report API success. Hosting fails: localhost and recorded backup. Security fails: no public link; do not waive checks to meet submission. Validation unavailable: no UNOSAT overlay, no accuracy claim; report independent scientific QA honestly.

Stretch and post-hackathon items are exhaustively assigned in [scope inventory](01_REQUIREMENTS_AND_SCOPE.md). No new stretch feature starts after H38, resolving the source's contradictory “stretch only after H38” line through D16.
''')

tests=[
('T-AGENTS','Member 3','tests/unit/test_domain_contracts.py','Twelve named deterministic interfaces, including disabled Movement fixture and Report/Safety','Each uses versioned trusted inputs and evidence-bearing outputs; no LLM-generated measurements'),
('T-DATA','Member 1','tests/geo/test_manifest.py','Metadata-only fixtures: same granule/version repeated, missing passes, footprint touch vs overlap, auth failure','Deterministic dedup; exact gaps; manifest/version/checksum required; no claim acquisition'),
('T-LICENCE','Member 2','tests/unit/test_source_policy.py + human source review','Unapproved ACLED/assessment terms, missing attribution/URL, Chinese-owned fixture','Block ingestion/publication; seven source references and source mark conflicts disclosed'),
('T-RADAR','Member 1','tests/geo/test_radar.py','Synthetic linear power, invalid nodata/zero, HH/HV mismatch, translated raster/version offset','Units correct; invalid Unknown; registration/drift gates fail; no silent interpolation'),
('T-GEO','Member 1','tests/geo/test_grid.py + raster QA','Wrong EPSG, invalid polygon, H3 r9→r8 parent, nodata, overlap/dimensions, GHSL coarse pixels','Correct joins/units; rejected invalid CRS; mask respected; sums conserved; area_id stable'),
('T-ML','Member 1','tests/unit/test_model.py + scientific report','Spatial train/hold-out blocks, 95/99/99.9 thresholds, Mahalanobis comparison, z fallback, top20 manual review','No train/hold-out leakage; measured false-alarm interval/enrichment; reasons; no assumed calibrated confidence'),
('T-COHERENCE','Member 1','tests/geo/test_crosscheck.py + expert review','Short versus cross-gap pair, phase alignment failure, seasonal decorrelation','Invalid feature excluded; no GUNW cross-gap fiction; report high technical risk'),
('T-VALIDATION','Member 1','tests/unit/test_assessment.py + licence/time/space review','Missing UNOSAT, mismatched report dates and polygons','No promised LB overlay or accuracy; UNDP/CNRS-L requires actual aligned authorized assessment'),
('T-PEOPLE','Member 2','tests/unit/test_people.py','Population conservation, overlap classes, null vulnerability, scenario weights and low/high','No double count; low≤high; pre-displacement label; missing not zero; date/source retained'),
('T-FACILITY','Member 2','tests/unit/test_facilities.py','OSM hospital with no radar change but no report; stale operating report','No inferred operating status; explicit Unknown or dated Reported'),
('T-SERVICES','Member 2','tests/unit/test_services.py','Night-light drop without report, unverified dependency edge','Possible power loss only; dependency uncertainty preserved; no logistics quantities'),
('T-ALERT','Member 2','tests/unit/test_alerts.py','1km/12h clustering boundaries; low-confidence/permanent fires; two clear nights <50% baseline; timeout/429','Dedup stable; baseline QA; cause Unknown; cached last-success displayed; failed poll not all clear'),
('T-INDEPENDENCE','Member 2','tests/unit/test_corroboration.py','Same report from two portals, GIBS and underlying product, independent reports with incompatible claim','No false upgrade; record source-family independence and scope of corroborated claim'),
('T-ROUTE','Member 2','tests/unit/test_routes.py','Tiny synthetic graph with three alternatives, closed bridge, unknown segment, disconnected nodes, new closure','Confirmed closures avoided; seven facts; fewer options explained; invalidation; external network forbidden'),
('T-SHELTER','Member 2','tests/unit/test_shelter.py','All space modes, OSM/GHSL/default precedence, missing geometry/levels, hazardous candidate','Building-first; correct capacity range; uncertainty shown; field-check caveat; no certification'),
('T-CONTRACT','Member 3','tests/api/test_contracts.py','Essential fixtures/schema and all endpoint status codes; client/server shared version','No shape drift; valid JSON; evidence required; generated client compiles'),
('T-SQL','Member 3','tests/geo/test_database.py','PostGIS transaction failure, duplicate run, invalid FK/low>high, region queries','Atomic rollback; idempotent load; GiST index used on bounded fixture query'),
('T-RBAC','Member 3','tests/security/test_roles.py','Anonymous/analyst/officer/coordinator/admin × route/shelter/brief; out-of-area objects','401 absent session; 403 forbidden role/area/object; analyst cannot extract shelter fields anywhere'),
('T-LAYER','Member 3','tests/security/test_private_layers.py','GET/HEAD/Range on COG/PMTiles/GeoJSON, guessed path, encoded traversal, alternate download','Same 401/403; no public static bypass, public artifact contains no r9/private metadata'),
('T-DELAY','Member 3','tests/security/test_publication.py','UTC clock 71h59m versus 72h; missing acquisition time; derivative and cached tiles','No early release; r8 plus suppression; other roles cannot bypass withheld strike-derived files'),
('T-CACHE','Member 3','tests/security/test_cache.py + browser storage inspection','Role downgrade/logout, PWA offline, shared proxy, stale route/revoked brief','Private no-store; caches cleared; no restricted SW/localStorage/source-map copy'),
('T-SAFETY','Member 3','tests/security/test_safety.py + protection review','Military/frontline tags, live tracking fields, public concentrations, logs and upstream URLs','Excluded/rejected; no coordinates/tokens in logs; no external routing/LLM leak; field-use warnings'),
('T-TRACE','Member 3','tests/api/test_trace.py','Value→run→granules/source, unknown licence, cyclic lineage, inaccessible parent','Full permitted trace or redaction; no fabricated source/date/version; model QA shown'),
('T-BRIEF','Member 4','tests/e2e/brief.spec.ts + A4 inspection','Analyst/coordinator exports; QR/path; null inputs; long sources','One usable black-white A4 page, footnotes, role filtering, no token/coordinates in QR'),
('T-UI','Member 4','apps/web/src/**/*.test.tsx','All screens/components, source wording, side rails, focus, mock badge, route attributes','Source design behavior; no fake passes or values; candidate/unknown language everywhere'),
('T-DISPLAY','Member 4','tests/e2e/layers.spec.ts','GIBS unavailable/BETA blank; polarization/date swap; >8 layers','Neutral fallback; no GIBS analytical substitution; missing passes dotted; active legend only'),
('T-A11Y','Member 4','tests/e2e/accessibility.spec.ts + manual keyboard','360/390/1280 px, 200% zoom, light/dark, keyboard/screen-reader paths','Focus and labels usable, contrast/shape cues, responsive field views, no map-only task'),
('T-JOBS','Member 3','tests/unit/test_jobs.py','Duplicate job, expired lease, interrupted fetch, closure revision','Idempotent retry; last-good retained; cached/error metadata; route/report invalidation'),
('T-DEVOPS','Member 3','scripts/verify_demo.py + restore rehearsal','Fresh clone, no-network fixtures, Compose health, backup laptop','Documented startup/test; no paid requirement; restore approved artifact/DB version'),
('T-MOVEMENT','Member 2','tests/unit/test_movement.py (future)','Coarse synthetic DTM/Meta, lag and restricted camps','Delayed aggregates only, unknown sample bias, no individual tracking'),
('T-BACKLOG','Member 4','Scope review at H38','Every F01–F28 and deferred dataset/agent','Each assigned phase/task; deferred items not falsely counted as MVP done'),
('T-LLM','Member 3','tests/security/test_llm_boundary.py (future)','Sensitive question, numeric invention, unsupported answer','No external restricted input; trusted numbers only; non-authoritative fixed questions'),
('T-E2E','Member 4','tests/e2e/demo.spec.ts','Fire→detail→summary→routes→coordinator shelters→analyst denied→Sources; offline variant','Full deterministic journey and server denials; science failures visible'),
('T-SUBMIT','Member 4','Human submission checklist','Video, citations, challenge tie, clean repo, actual test report','All claims match executed work; release/tag only after review; no operational locations'),
]
doc(names[10],'Testing and acceptance plan',f'''
## Two distinct verification levels

This planning deliverable is verified for file integrity, links, tables, source mapping, JSON/schema structure, ownership and Git diff. Application tests below are **planned, not executed**: the repository initially has no app or test harness. No claim of scientific accuracy, API access, deployment or field readiness follows from documentation validation.

All routine automated tests run on synthetic arrays, tiny synthetic graphs and scrubbed adapter responses without production credentials or war-zone coordinates. Source: ARCHITECTURE.md §1.4/3.5/4.4, PROJECT_PLAN.md §10, UI_DESIGN.md §§4–6. Extra engineering thresholds are ARCHITECT RECOMMENDATION.

{table(['Test ID','Owner','Planned location','Cases','Pass criterion'],tests)}

## Security fixture matrix and commands

M3 creates runtime-only sessions for each role and two area scopes. Test authenticated policy decisions at HTTP and object levels, plus actual byte/file serving. `GET /api/v1/shelters` anonymous → 401; analyst → 403; officer → 403; coordinator in wrong area → 403; coordinator in scope → authorized synthetic result. `POST /api/v1/routes` analyst → 403. Analyst `/briefs/{{id}}/print` must not reveal a coordinator's shelter section. Protected tiles/files receive 401/403 as appropriate including alternate download/Range/HEAD. Public response inspections scan entire body, not only visible UI.

Planned commands after implementation: `python -m pytest tests/unit tests/geo tests/api tests/security`; `npm --prefix apps/web run test`; `npm --prefix apps/web run test:e2e`; `npm --prefix apps/web run build`; `docker compose -f infra/compose.yaml config`. Member 3 supplies dependency locks and exact scripts. Never report these commands passed before they exist.

## Scientific gate interpretation

Quiet hold-out target “about 1%” at 99% threshold is a source expectation, not an achieved rate. Record sample size, numerator/denominator and uncertainty, spatial block split, residual calibration/season bias and 20 manual checks. Near-strike enrichment does not prove collapse or provide ground-truth accuracy. If verification fails, label outputs candidates with failed QA or withhold them; do not adjust thresholds on the hold-out set to manufacture success.

## Release blockers

Any secret/coordinate leak, public private-file bypass, missing 72 h gate, unauthorized role/object access, fabricated measurements or unsupported validation claim blocks external demonstration. Broken core NISAR processing blocks full real-data MVP acceptance. Honest synthetic backup is permitted with its limitations clearly stated. Cosmetic issues may be deferred only if access, source inspection, basic phone views and A4 remain usable. Record gate owner, actual command/result, artifact revision and unresolved risks.
''')

doc(names[11],'DevOps, deployment and Git workflow',r'''
## Actual planning Git setup

Original branch `docs/architecture-plan` at `022599111ea437b62bf297851e0109f08cde94d8`. Detected remote default `origin/main` at `e99348c0aec238b4d4252f02001560f6f18d1fc7`. Working tree initially clean. Fetch succeeded after sandbox network retry. Created `planning/civisar-full-architecture` from origin/main and fast-forwarded existing architecture commits to preserve the seventh source; default/original branches were not changed. Planning upstream to origin/main was removed. Final commit/branch/status verification is reported in the completion response and git log; this document does not invent a future commit hash.

After validating and committing docs, create `dev` at the plan commit only if still absent locally/remotely. Existing dev would require a reviewed ordinary PR/merge, never reset or overwrite. No feature branches are created until implementation starts. Remote push is left pending because no prior explicit push authorization is established; local commit/branches fulfill the safe fallback in the request. Exact optional push commands are below.

```mermaid
gitGraph
  commit id: "default e99348c"
  branch docs/architecture-plan
  checkout docs/architecture-plan
  commit id: "architecture 8e20508"
  commit id: "split 0225991"
  branch planning/civisar-full-architecture
  checkout planning/civisar-full-architecture
  commit id: "planning docs"
  branch dev
  checkout dev
  branch feature/m1-radar-damage
  branch feature/m2-geodata-alerts
  branch feature/m3-backend-security
  branch feature/m4-frontend-demo
```

Graph shows ancestry/target workflow, not a claim that feature branches already exist. Since new dev starts at the planning commit, an initial planning→dev PR would have no diff. Subsequent planning amendments use planning→dev PRs; feature branches originate from dev. Existing integration branches instead receive a real planning-docs PR. Reviewed dev later promotes to detected default main. Do not merge into main during this task.

## Commands (Windows Git is installed outside PATH)

```powershell
& 'C:\Program Files\Git\cmd\git.exe' status -sb
& 'C:\Program Files\Git\cmd\git.exe' branch -a
& 'C:\Program Files\Git\cmd\git.exe' log -5 --oneline
# Only after explicit remote-push authorization:
& 'C:\Program Files\Git\cmd\git.exe' push -u origin planning/civisar-full-architecture
& 'C:\Program Files\Git\cmd\git.exe' push -u origin dev
# At implementation start, with clean working tree:
& 'C:\Program Files\Git\cmd\git.exe' switch dev
& 'C:\Program Files\Git\cmd\git.exe' switch -c feature/m1-radar-damage
```

Members 2–4 use their exact feature branch names from [allocation](08_FOUR_MEMBER_TASK_ALLOCATION.md). macOS/Linux use `git` with the same arguments. If branch already exists, inspect/check it out without recreating. Dirty tree: preserve work; use a scoped commit by owner or isolated worktree after inspection, never destructive cleaning. On conflicts, review both sides with owners, resolve intentionally and rerun contracts/tests; use merge abort if resolution is uncertain, never force-push shared branches. No reset --hard, clean -fd, force push or branch deletion.

## PR/protection/release recommendations

ARCHITECT RECOMMENDATION: protect main/dev against direct pushes and force pushes; require one non-author review, successful CI, resolved comments and up-to-date merge checks. No protection was configured remotely here. Member 3 reviews any auth/layer/retention change; Member 1 reviews radar science; Member 2 reviews GIS/data semantics; Member 4 reviews UX/demo truthfulness. Small PRs include source/task IDs, input/output contract, actual validation, data sensitivity and rollback. Avoid mixing code/large binaries with documentation PRs.

CI proposed gates: source/reference integrity; Markdown/JSON/OpenAPI; Python formatting and meaningful tests; PostGIS integration; frontend typecheck/build/components; role/file/privacy tests; E2E and secret/dependency checks. Fork CI has no production credentials. Pin dependencies/containers with a documented update process after verification. Release candidate `v0.1.0-demo-rc1`, final `v0.1.0-demo` only after H48 review; tags not created in planning. Record full commit and approved dataset/run manifest in release notes.

## Local runtime and hosting

Planned Compose services: db (PostGIS), api, worker, web/proxy. Worker imports shared Python pipeline modules; no queue broker needed for single-host demo. Ignore `.env`, raw/cropped sensitive data, local DB volumes, recordings and private reports in future `.gitignore`; planning does not edit the existing root README or source references.

Environment template keys (blank values, no secrets): DATABASE_URL, SESSION_SECRET, EARTHDATA_TOKEN, FIRMS_MAP_KEY, ACLED_TOKEN, IOM_DTM_KEY, ALLOWED_ORIGIN, DATA_ROOT, DEMO_SYNTHETIC, COOKIE_SECURE. API keys never use VITE_ prefix. M3 creates `.env.example` and `.gitignore` in implementation, with local least-privilege passwords generated outside Git.

Free-only: laptop Compose first, optional Cloudflare Tunnel after free-tier/account/HTTPS and exposure checks. Tunnel is not a substitute for session authorization. No tunnel/deployment tested or created here. If verification fails, use localhost demonstration and recorded video. Cross-platform onboarding is in [15](15_TEAM_ONBOARDING.md); Windows WSL2/Linux containers and macOS/Linux Docker differences must be tested by team.

## Operations, observability and rollback

Health: API responds sanitized status, DB check private, source freshness/last-success surfaced without credentials. Metrics: job duration/failures, queue age, data age, invalidated routes, denied requests, disk/RAM. Logs use request/run IDs, never precise route endpoints, shelter coordinates, user secrets or raw source responses.

Back up a sanitized demo DB dump plus checksummed approved artifacts/config version to second laptop; exclude real secrets. Restore rehearsal at H40 loads previous schema-compatible snapshot and changes approved run pointers atomically. Application rollback uses reviewed previous image/commit; DB migration rollback must be tested or restore snapshot rather than destructive ad hoc SQL. Keep a recorded demo if network/source APIs fail. Sensitive real-data retention requires approved policy before any production use.
''')

risks=[
('R01','Radar download/disk exceeds weekend','High','Member 1','H0 throughput and actual manifests','A/B first, crop, no C until core green; synthetic fallback disclosed'),
('R02','Jan–Jun version/season confounding','High','Member 1','Stable controls and registration fail','Withhold claim, report Unknown/QA failure; not solved automatically by anomaly model'),
('R03','No aligned damage labels','High','Member 1','UNDP/CNRS-L unavailable or mismatched','Quiet hold-out/manual checks; no false accuracy/UNOSAT overlay'),
('R04','Cross-gap coherence invalid','High','Member 1','Pair phase/baseline/decorrelation checks fail','Exclude coherence; retain valid GCOV'),
('R05','M2 overloaded','High','Member 2','Miss H12/H16 handoff','M3 scheduling/loaders, M4 fixtures, M1 GIS review; postpone global/movement/open land'),
('R06','Sensitive file/brief/cache bypass','Critical','Member 3','Any RBAC/area/Range/export test fails','Block link/release; sanitize fixtures and fix policy before demo'),
('R07','Licences/API accounts unavailable','High','Member 2','Missing written permitted use or key','Disable source, Unknown or synthetic; never assume unrestricted HDX reuse'),
('R08','Population/height/road incompleteness','High','Member 2','Coverage/levels audit low; no operating reports','Ranges/default flags, no capacity/passability certainty'),
('R09','Source outages/rolling retention','Medium','Member 3','Timeout, stale API, NRT date missing','Archive joins, last-good Cached, timestamps; no fabricated current data'),
('R10','Public aggregation still reveals civilians','Critical','Member 3','Unique/high-risk cells or temporal differencing','Suppress/manual review; use synthetic public layer'),
('R11','Mock data mistaken for measured facts','High','Member 4','Fixture audit detects unlabeled values','Visible synthetic flags on maps/exports; per-value trace'),
('R12','Challenge rules/provenance miscount','High','Member 4','Official page inaccessible; six vs five marks','Keep VERIFY; capture actual rules before development/submission'),
('R13','Hosting/Windows GIS tooling fails','Medium','Member 3','Compose/GDAL/tippecanoe or tunnel preflight fails','Containerize verified tools, laptop/recording backup; no paid switch'),
('R14','Feature freeze violated','Medium','Member 4','Optional work proposed after H38','Fixes only, move enhancement to after hackathon'),
]
doc(names[12],'Risk register and decision log',f'''
## Decision authority

Source disagreements are retained in [source audit](00_SOURCE_AUDIT.md); proposals do not replace original files. APPROVED = explicit user constraint or recorded source decision; PROPOSED = recommended pending owner/leader review; VERIFY = fact/access needs evidence; BLOCKED = unavailable evidence prevents that feature, not the entire documentation task. Review decisions at H2 and H24; record approver/date and test evidence in later PRs.

{conflict_table}

## Risk register

{table(['ID','Risk','Impact','Owner','Trigger','Mitigation / contingency'],risks)}

## Proposed ADRs

[ADR 001](adr/001_MODULAR_MONOLITH_AND_CONTRACTS.md) fixes implementation boundaries; [ADR 002](adr/002_PUBLICATION_AND_LOCAL_ROUTING.md) covers privacy; [ADR 003](adr/003_RADAR_VALIDITY_AND_DATA_BASELINE.md) resolves scientific/data proposal boundaries. All retain PROPOSED status unless an explicit existing requirement is stated separately. No undocumented alternative stack or paid service is chosen.
''')
adrs=[
('001_MODULAR_MONOLITH_AND_CONTRACTS.md','Modular monolith and shared contracts','ARCHITECTURE.md Parts 1–4 and H2 agreements','Use one FastAPI API and worker sharing deterministic modules, PostGIS and private files; React/Vite/MapLibre. H2 OpenAPI and fixtures freeze before feature integration.','Minimizes deployment and schema drift for four members/48 h; worker isolates long radar jobs from HTTP.','Independent microservices would add orchestration and service-auth work; no working implementation requires a stack change.','Single host is a failure domain; mitigate through snapshots/recorded demo and bounded jobs. M3 owns service integration; M1/M2 own science. T-CONTRACT/T-JOBS/T-DEVOPS.'),
('002_PUBLICATION_AND_LOCAL_ROUTING.md','Private artifacts, publication and local routing','PROJECT_PLAN.md §10; UI_DESIGN.md §§5–7; PDF p2 §4; DATA_AND_API_PLAN.md §4','Central server role+area+object policy on endpoints/files; >=72 h strike-change delay; public r8 plus suppression; local graph/in-app turns; private export no-store.','Coordinates, reports and fine-grained artifacts can leak even if UI buttons are hidden.','External route service/phone handoff rejected by privacy requirement. Client-only guards and public object buckets rejected.','Requires guarded Range/tiles/brief routes and role-aware cache invalidation. Public shell PWA stretch; private offline post-hackathon. M3 policy, M2 algorithms, M4 presentation. T-RBAC/T-LAYER/T-CACHE.'),
('003_RADAR_VALIDITY_AND_DATA_BASELINE.md','Conditional science and proposed 15-source baseline','DATASETS.md §§1–6; DATA_AND_API_PLAN.md §§1–5; ARCHITECTURE.md §1; NASA_DATASET_ANALYSIS.md §§2/9','Recommend 15 families, retaining current 14 pending leader approval. Use BETA/PROVISIONAL/V1 GCOV with version QA; GSLC/GUNW only if scientifically valid and within tier budget.','Only BETA supplies before period in source snapshot; archives support time baselines; no valid ground truth is established.','Silently approving proposal, interpolating missing passes, treating imagery as analysis or assuming coherence correction are rejected.','All counts/dates remain 13 Nov source snapshot; verify scene access and aligned validation. No guaranteed damage proof or calibrated confidence. M1 science and M2 catalogue. T-RADAR/T-ML/T-VALIDATION.')]
for file,title,source_ref,decision,rationale,alternatives,consequences in adrs:
    write('adr/'+file,f'# ADR: {title}\n\nStatus: **PROPOSED — ARCHITECT RECOMMENDATION** (14 November 2026). Existing explicit safety/stack requirements remain binding; approval of added mechanics is pending.\n\n[Decision log](../12_RISK_REGISTER_AND_DECISION_LOG.md)\n\n## Source\n\n{source_ref}\n\n## Decision\n\n{decision}\n\n## Rationale\n\n{rationale}\n\n## Alternatives\n\n{alternatives}\n\n## Consequences and verification\n\n{consequences}\n')

doc(names[13],'Demo story, submission and citations','''
## Judge-facing story

Source: ARCHITECTURE.md §4.3 and PROJECT_PLAN.md §§2/5/6. Show humanitarian decisions grounded in NISAR surface change, with evidence and limits. Do not frame the product as validated navigation, military intelligence or current live satellite tracking. All sensitive route/shelter examples are synthetic/redacted. Every synthetic panel has a badge; actual science results are shown only after measured QA.

| Step / target time | Operator / owner | Show | Evidence of success |
|---|---|---|---|
| 0:00–0:30 | M4 narrator, logged out | Public-safe delayed r8 preview, challenge tie and sign-in | No exact shelter/critical-site/route data |
| 0:30–1:10 | Analyst, M1 science support | Jan BETA→Jun NISAR HH/HV change, missing acquisition interval, later pass strip | Actual dates/version/QA and candidate wording; synthetic fallback disclosed if needed |
| 1:10–1:50 | Officer | Fire alert→detail with 1/3 km synthetic rings | Fire detected, no cause, source/local+UTC time, cached/fresh state |
| 1:50–2:30 | Officer | Area summary people first, vulnerability/what-to-bring | Source-linked ranges, Unknown service limits, no invented quantities |
| 2:30–3:10 | Officer | Compare inbound/outbound A/B/C; inject synthetic confirmed closure | Seven facts, revision warning, recompute locally; no safe label |
| 3:10–3:40 | Coordinator | Ranked building shelter, space mode and capacity uncertainty | For checking, protection/ordnance banner, no public locations |
| 3:40–4:10 | Analyst, M3 security support | Direct shelter API attempt and protected file attempt | Actual 403; show scrubbed response, not only missing button |
| 4:10–4:50 | Analyst | Sources→trace value→model QA; print brief | Dataset/version/date/licence, measured tests/limits; A4 source footnotes |
| 4:50–5:00 | M4 | Honest limits and next steps | Not field validated; explicit availability and validation blockers |

Times are ARCHITECT RECOMMENDATION, not a known competition video limit. M4 verifies submission requirements and adjusts. Rehearse H32–H38; record H40–H44. No live deployment or submission is performed by this planning task.

## Backup and failure narrative

M3 prepares local sanitized demo bundle and second laptop; M4 records the approved journey. Simulate one API outage to demonstrate Cached + last-success instead of pretending live updates. If radar processing fails, show synthetic UI journey plus NISAR metadata and clearly state uncompleted scientific work. Do not imply browse imagery is computed damage. Security failure removes external link until fixed.

## Citation package

NISAR challenge citation: [Dancing with the SARs Resources tab](https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/?tab=resources), verification pending. Link official product/DAAC guidance and exact collection/granule record for real acquisitions. NISAR is direct Tab per source; OPERA/Black Marble/FIRMS/NASADEM Tab tool; GIBS Other via PDF. Do not repeat the inconsistent six-source provenance count without its caveat.

For every used dataset provide provider, product/level, acquisition range, processing version, spatial coverage/resolution, terms/attribution, source URL, accessed date, API and known limits. NASA and ESA/Copernicus attributions are separate where required. UNDP/CNRS-L availability and rights remain VERIFY. OSM attribution/ODbL, WorldPop/JRC product terms, ACLED/DTM/Meta/Insecurity Insight restrictions need resource-specific review. Never cite a source as acquired merely because it appears in the catalogue.

The [source audit](00_SOURCE_AUDIT.md) links the untouched references. The PDF directory is a provenance/access aid, not a scientific validation source. The [source link register](14B_SOURCE_LINK_REGISTER.md) inventories supplied URLs and check status.

## Submission checklist and release record

M4 owns text/video/repository links/citations and actual Space Apps form requirements; M1 signs science caveats, M2 confirms source rights and quantities, M3 signs security and hosting scope. Include exact reviewed commit, synthetic-versus-real declaration, measured model QA, source snapshot date, unavailable datasets and operational limitations. Tag reviewed dev only after final checks; do not imply branch protection, deployment, field validation or submission occurred during planning.
''')

doc(names[15],'Team onboarding','''
## Read first

Start with [scope](01_REQUIREMENTS_AND_SCOPE.md), [architecture](02_FULL_SYSTEM_ARCHITECTURE.md), your [task package](08_FOUR_MEMBER_TASK_ALLOCATION.md), [contracts](contracts/README.md) and [security](07_SECURITY_PRIVACY_AND_RBAC.md). Sources remain original and may conflict; decision status is in [source audit](00_SOURCE_AUDIT.md). Exactly four accountable members; names/contact handles pending assignment.

## Current repository versus target development setup

Current repository contains documentation and draft fixtures only. No package.json, Python project, Compose stack, API server or runnable app tests exist yet. The commands below are **target implementation instructions** for M3/M4 to make real, not completed setup or guaranteed executable commands today. Planning validation can run independently using the committed documentation validator.

Prerequisites to verify at H0: Git, Python compatible with pinned GIS wheels, Node compatible with chosen Vite version, Docker with Compose/PostGIS, adequate disk/network, GDAL and tippecanoe in reproducible containers. Pin actual versions after checking official compatibility and the team's machines; no unverified “latest” version promise. Windows: install Git on PATH or use `C:/Program Files/Git/cmd/git.exe`; use WSL2/Linux containers for GIS tools if native binaries differ. macOS/Linux: same Compose interfaces, shell path syntax adjusted. No paid infrastructure.

```text
git clone https://github.com/nasa-space-apps-nextfrontier-2026/dancing-with-the-sars.git
cd dancing-with-the-sars
git fetch origin
git switch dev
git switch -c feature/m3-backend-security
```

Remote branches must have been pushed before a fresh clone can switch to them. Until then use the local branches or an approved repository handoff; do not claim remote availability. Each member uses their feature branch from [allocation](08_FOUR_MEMBER_TASK_ALLOCATION.md). Preserve dirty work and inspect existing branch before creating.

## Planned startup after M3/M4 scaffold

1. Copy `.env.example` to ignored `.env` locally (`Copy-Item` PowerShell or `cp` POSIX); generate local credentials without committing them. Set DEMO_SYNTHETIC=true initially, server-only keys empty for no-network mode.
2. `docker compose -f infra/compose.yaml config` validates environment and ports. `docker compose -f infra/compose.yaml up --build` starts db/api/worker/web. Bind only loopback during development; confirm health before tunnel exposure.
3. `python scripts/load_demo.py --synthetic` loads small safe fixtures transactionally; `python scripts/verify_demo.py` checks contracts and role/file denial. M3 implements these entry points.
4. `python -m pytest tests/unit tests/geo tests/api tests/security`; `npm --prefix apps/web ci`; `npm --prefix apps/web run test`; `npm --prefix apps/web run build`; `npm --prefix apps/web run test:e2e`. M4 must provide package-lock and matching scripts; M3 provides Python lock/environment instructions.
5. Confirm login/role downgrade, missing passes, cached state, source trace and A4. Only then replace permitted fixtures with validated real artifacts. Do not hide a synthetic fallback behind a real-data label.

## Accounts and preflight checklist

Each member: individual Earthdata Login. M2: FIRMS MAP_KEY, ACLED permitted access, DTM key if stretch needed; inspect source licences. M3: optional Cloudflare account only if free tunnel is confirmed and security tests pass. M4: challenge Resources/rules and submission requirements. M1 checks bandwidth, disk, actual product specs/CMR and radiometric comparability. Challenge prep rules must be checked before development downloads begin. No credentials entered into PRs, chat fixtures or screenshots.

## Common integration issues

H3 numeric precision loss → strings. Metres computed in degrees → project before analysis. Different nodata conventions → manifest and validation. BETA/provisional version drift → scientific QA gate. Cadaster overlaps → fractional crosswalk not duplicate totals. Missing NRT history → archive join. Blank GIBS BETA → context fallback, not fabricated analytical pass. Browser PMTiles Range unauthorized → implement guarded range endpoint rather than public bucket. Host/container paths → DATA_ROOT mount and manifest-relative paths. Windows GIS build failure → verified container, not silent algorithm replacement.

## Handoff and support

Every handoff includes artifact/schema version, checksum, date/CRS/unit, licence/tag, tests and known gaps. Member 1 contact [pending]; Member 2 [pending]; Member 3 [pending]; Member 4 [pending]. Raise scientific uncertainty to M1, GIS/source semantics to M2, permissions/deployment to M3, UI/demo truthfulness to M4. A blocked source does not permit fake evidence. Recovery uses [DevOps rollback](11_DEVOPS_DEPLOYMENT_AND_GIT_WORKFLOW.md); no destructive Git recovery.
''')

# Trace every meaningful source paragraph, bullet and table row in addition to explicit deliverable rows.
req_headers=['Requirement ID','Requirement','Source file + section/page','Priority/phase','Design doc','Owning member/task ID','API/data/UI deliverable','Acceptance test','Status']
def design_link(n): return f'[{names[n]}]({names[n]})'
def plain(s):
    s=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1 (\2)',s)
    return s.replace('**','').replace('`','').replace('|',';').strip()
def classify(filename,heading,text):
    # Each category has a concrete design destination and acceptance suite, with defer/verify overlays below.
    h=heading.lower(); t=text.lower(); both=h+' '+t
    phase='MVP'; status='MAPPED / planned'; n=1; task='M3-01'; test='T-CONTRACT'; output='Reviewed scope/contract'
    if filename=='UI_DESIGN.md': n,task,test,output=6,'M4-02','T-UI','Screen/component behavior'
    elif filename in ['DATASETS.md','DATA_AND_API_PLAN.md','NASA_DATASET_ANALYSIS.md']: n,task,test,output=3,'M2-01','T-LICENCE','Source/version/terms manifest'
    elif filename=='ARCHITECTURE.md':
        if 'part 1' in h or re.match(r'1\.',heading): n,task,test,output=4,'M1-02','T-RADAR','Radar cells and QA'
        elif 'part 2' in h or re.match(r'2\.',heading): n,task,test,output=4,'M2-02','T-GEO','Area tables and domain functions'
        elif 'part 3' in h or re.match(r'3\.',heading): n,task,test,output=5,'M3-03','T-CONTRACT','API/policy/storage'
        elif 'part 4' in h or re.match(r'4\.',heading): n,task,test,output=6,'M4-03','T-UI','Screens and demo'
        elif 'timeline' in h or 'hour' in h: n,task,test,output=9,'M3-01','T-CONTRACT','Milestone and handoff'
    rules=[
      (r'coherence|gunw|gslc|tier c',4,'M1-04','T-COHERENCE','Conditional coherence QA'),
      (r'nisar|gcov|radar|polariz|backscatter|quiet|mahalanobis|isolation|99\.9|99%|95%',4,'M1-02','T-RADAR','Versioned radar cells/COGs/QA'),
      (r'unosat|undp|cnrs|validation|hold.out|top 20|strike enrichment',4,'M1-03','T-VALIDATION','Assessment availability / model QA'),
      (r'shelter|capacity|3\.5|4\.5|5\.5|30 m|45 m',4,'M2-05','T-SHELTER','Restricted candidate/capacity result'),
      (r'route|closure|navigation|road graph|bridges|heavy vehicle',4,'M2-04','T-ROUTE','Local route and closure revision'),
      (r'population|worldpop|people|residents|displaced|vulnerab|severity rank',4,'M2-02','T-PEOPLE','People ranges / severity parts'),
      (r'facilit|hospital|clinic|working|water|services lost|what to bring',4,'M2-02','T-FACILITY','Facility/services evidence and report model'),
      (r'fire|firms|black marble|night.light|ioda|internet|corrobor|acled|insecurity',4,'M2-03','T-ALERT','Timestamped observations/alerts and independence'),
      (r'ghsl|hotosm|overpass|nasadem|cadaster|h3|area grid',4,'M2-01','T-GEO','Grid/base geometry and uncertain height'),
      (r'gibs|worldview|display.only|display layer',3,'M4-01','T-DISPLAY','Display-only Layer and source attribution'),
      (r'source|licence|license|citation|cmr|api used|dataset record',3,'M2-01','T-LICENCE','SourceRecord and provenance register'),
      (r'api|postgis|database|endpoint|json|value row|geojson|pmtiles',5,'M3-01','T-CONTRACT','Schemas/loaders/HTTP contract'),
      (r'worker|timer|docker|cloudflare|backup|deploy|cached|retry',11,'M3-04','T-JOBS','Worker/freshness/recovery'),
      (r'screen|component|theme|ibm plex|colour|color|button|legend|inspector|time slider|swipe|phone|print|brief|offline|pwa',6,'M4-03','T-UI','UI/brief/field view'),
      (r'no military|front.line|72 hour|72 h|privacy|safety|authoris|authoriz|sign.in|logged|role|no live|never.*safe|sensitive|tracking|chinese',7,'M3-02','T-SAFETY','Server policy and publication filter'),
    ]
    # More specific terms in the statement override section defaults; later safety rules intentionally dominate.
    for pattern,dest,owner,accept,out in rules:
        if re.search(pattern,t): n,task,test,output=dest,owner,accept,out
    if re.search(r'movement|watch list|worldwide|global expansion|whole planet',both):
        phase='Stretch movement / after hackathon global'; n,task,test,output=1,'M2-06','T-MOVEMENT','Deferred aggregate movement/watch-list backlog';status='DELIBERATELY DEFERRED'
    if re.search(r'gemini|question box|llm',both):
        phase='After hackathon'; n,task,test,output=1,'M3-04','T-LLM','Deferred trusted-output explanation';status='DELIBERATELY DEFERRED'
    if 'stretch' in h or 'tier c' in h:
        phase='Stretch conditional before H38';status='DELIBERATELY DEFERRED'
    if filename=='NASA_DATASET_ANALYSIS.md' and (re.match(r'3\.(2|5|6|7|8|9|10|11)',heading) or heading.startswith('5.')):
        phase='Conditional / after hackathon; see exclusions';n=3;output='03A_DATASET_EXCLUSIONS.md decision';status='DELIBERATELY DEFERRED / source priority conflict'
    if re.search(r'dropped|not useful',h) or (filename=='DATASETS.md' and heading.startswith('6.')):
        phase='Excluded or explicitly conditional';n=3;task='M2-01';test='T-BACKLOG';output='Exclusion ledger';status='DELIBERATELY DEFERRED'
    if re.search(r'unverified|\(check\)|verify|still to do|none exist|none found|no.*coverage|13 nov|2026-11|granules|newest|latest',both): status+='; VERIFY snapshot/fact'
    if filename=='DATA_AND_API_PLAN.md': status+='; PROPOSED, not approved'
    if re.search(r'differences|to decide|main decision|changes to raise',h): status='CONFLICTING / decision log'
    return phase,n,task,test,output,status

trace=[]
for fid,title,phase,task,gate,test,io in features:
    trace.append((fid,title,'PROJECT_PLAN.md §§5–12; ARCHITECTURE.md MVP/Parts 1–4; exact source rows below',phase,design_link(1),task,io+'; '+gate,test,'PLANNED / not implemented'))
for i,(name,api,phase,task,src,accept) in enumerate(screens,1): trace.append((f'UI-S{i:02}',name,src,phase,design_link(6),task,api,accept,'MAPPED / planned'))
for i,(name,api,task,accept) in enumerate(components,1): trace.append((f'UI-C{i:02}',name,'UI_DESIGN.md §4 Components; §5 Visual and wording rules','MVP',design_link(6),task,api,accept,'MAPPED / planned'))
for i,e in enumerate(endpoints,1):
    method,path,role,param,response,task,domain,rate=e
    trace.append((f'API-{i:02}',method+' /api/v1'+path,'ARCHITECTURE.md §3.2 Endpoints; PROJECT_PLAN.md §8.1; user §6 (path mechanics recommended)','MVP',design_link(5),task,response+'; '+role+'; '+domain,'T-CONTRACT + T-RBAC; '+rate+' boundary','DRAFT contract, not server-tested'))
for x in datasets: trace.append((x[0],x[1],'DATASETS.md §§1–4; DATA_AND_API_PLAN.md §§2–3; NASA_DATASET_ANALYSIS.md §3 (exact rows below)','MVP/conditional per catalogue',design_link(3),x[-1],x[14]+' / '+x[15],'T-DATA + T-LICENCE','VERIFY; proposed additions not approved'))
agent_tasks={'Damage':'M1-02','Facility':'M2-02','Services':'M2-02','People':'M2-02','Shelter':'M2-05','Route':'M2-04','Movement':'M2-06','Alert':'M2-03','Corroboration':'M2-03','Orchestrator':'M3-04','Report':'M2-02','Safety':'M3-02'}
for i,(agent,task) in enumerate(agent_tasks.items(),1): trace.append((f'AG-{i:02}',agent+' deterministic function','PROJECT_PLAN.md §8 AI agents','Stretch' if agent=='Movement' else 'MVP',design_link(2),task,'Component contract in architecture','T-AGENTS: typed inputs/outputs; no invented numbers; domain test in task','MAPPED / planned'))
for tid,owner,path,cases,accept in tests: trace.append((tid,cases,'ARCHITECTURE.md §§1.4/3.5/4.4; PROJECT_PLAN.md §10; user §9','MVP unless future test',design_link(10),next(t[0] for t in tasks if t[2]==owner and (tid in t[13])) if any(t[2]==owner and tid in t[13] for t in tasks) else {'Member 1':'M1-03','Member 2':'M2-02','Member 3':'M3-02','Member 4':'M4-04'}[owner],path,accept,'PLANNED test, not executed'))
for c in conflicts: trace.append((c[0],c[1],c[2]+' versus '+c[3],'Decision gate',design_link(12),{'Member 1':'M1-01','Member 2':'M2-01','Member 3':'M3-02','Member 4':'M4-04'}[c[7]],c[5],c[8],c[6]))
outputs=['Data map layers','Agent result layers','Area tables','Agent result records','Alerts','Area summary','Print / offline brief','Route options','Shelter candidates','Sources and citations']
for i,label in enumerate(outputs,1): trace.append((f'OUT-{i:02}',label,'UI_DESIGN.md §2 What CIVISAR outputs, row '+str(i),'MVP; restricted offline deferred',design_link(6),['M1-02','M3-03','M2-02','M3-03','M2-03','M2-02','M4-03','M2-04','M2-05','M3-03'][i-1],label+' contract/presentation','T-CONTRACT + role filtering + source trace','MAPPED / planned'))

pdfnotes=[
('p1 §1 item 1','NASA Open Data Portal is a metadata catalogue; files may live elsewhere','M2-01','Source link register','T-LICENCE'),
('p1 §1 item 2','NASA API Portal services have individual authentication and rate limits','M3-04','Adapter preflight','T-JOBS'),
('p1 §1 item 3','Earthdata Search discovers observations by keyword/time/geography','M1-01','CMR search manifest','T-DATA'),
('p1 §1 item 4','Worldview is visual context','M4-01','Display-only background','T-DISPLAY'),
('p1 §1 item 5','Exoplanet Archive is irrelevant to Earth observation case','M2-01','Excluded portal','T-BACKLOG'),
('p1 §1 item 6','NASA Open is innovation/open-science information','M2-01','Information-only portal','T-BACKLOG'),
('p1 §2 item 1','ASF Vertex discovers SAR/NISAR scenes','M1-01','Scene manifest','T-DATA'),
('p1 §2 item 2','ASF Search API documentation for programmatic SAR discovery','M1-01','Search adapter','T-DATA'),
('p2 §2 item 3','Earthdata Login authenticates protected downloads','M1-01','Server credential preflight','T-DATA'),
('p2 §2 item 4','GIBS imagery services for web maps/GIS','M4-01','Context Layer','T-DISPLAY'),
('p2 §2 item 5','EONET is natural-event metadata/context','M2-01','Excluded from war-event alerts','T-BACKLOG'),
('p2 §3 priority 1','First ASF Vertex and Search API for SAR discovery','M1-01','Priority-1 scene manifest','T-DATA'),
('p2 §3 priority 2','Second Earthdata Search for collections/product metadata','M1-01','Priority-2 source record','T-DATA'),
('p2 §3 priority 3','Third Worldview/GIBS; check sensor/date/resolution','M4-01','Display metadata','T-DISPLAY'),
('p2 §3 priority 4','Fourth Open Data Portal records/host links','M2-01','Source link register','T-LICENCE'),
('p2 §3 priority 5','Fifth relevant NASA APIs; not every API has SAR imagery','M3-04','No generic API assumption','T-DATA'),
('p2 §4 note 1','Check each service current key/authentication/rate-limit rules','M3-04','Adapter preflight and backoff','T-JOBS'),
('p2 §4 note 2','GIBS/Worldview visualization does not substitute for NISAR analysis','M1-02','Scientific raster lineage separate from display','T-DISPLAY'),
('p2 §4 note 3','Use NISAR product documentation and SAR access workflow','M1-01','Product/version validation','T-RADAR'),
('p2 §4 note 4','Record dataset name, level, acquisition date, version, coverage, terms, URL','M2-01','SourceRecord and granule manifest','T-TRACE'),
('p2 §4 note 5','Do not publish sensitive shelters or identifiable civilian population concentrations','M3-02','Public filter/suppression and protected files','T-SAFETY'),
('p2 footer','Prepared 13 November 2026; source snapshot provenance','M2-01','Dated audit','T-LICENCE')]
for i,(loc,req,task,out,test) in enumerate(pdfnotes,1): trace.append((f'PDF-{i:02}',req,'NASA_Open_Data_Links_Earth_Impact_Intelligence.pdf '+loc,'Constraint / context',design_link(0),task,out,test,'MAPPED; factual access VERIFY'))

atomic=[]; section_rows=[]; linkrows=[]; atom_index={}; section_count=collections.Counter()
for fi,filename in enumerate([x for x in hashes if x.endswith('.md')],1):
    lines=(D/filename).read_text(encoding='utf-8').splitlines(); heading='Document introduction'; code=False; tablehead=None
    sections=collections.OrderedDict()
    for li,line in enumerate(lines,1):
        st=line.strip()
        if st.startswith('```'): code=not code; continue
        if not st: continue
        if st.startswith('#'):
            heading=re.sub(r'^#+\s*','',st); sections.setdefault(heading,[]); tablehead=None; continue
        if code or re.fullmatch(r'[-\s]+',st): continue
        if st.startswith('|'):
            if re.fullmatch(r'[|:\-\s]+',st): continue
            if li<len(lines) and re.fullmatch(r'[|:\-\s]+',lines[li].strip()):
                tablehead=plain(st); continue
        phase,n,task,test,out,status=classify(filename,heading,st)
        req=plain(st)
        if tablehead and st.startswith('|'): req='Table row: '+req
        rid=f'SRC-{fi:02}-{li:03}'
        row=(rid,req,f'[{filename}]({filename}) — {heading} (line {li})',phase,design_link(n),task,out,test,status)
        atomic.append(row);sections.setdefault(heading,[]).append(row);atom_index.setdefault(filename,[]).append(li)
        for url in re.findall(r'https?://[^\s<>\)\]|]+',st): linkrows.append((filename,heading,url.rstrip('.,;'),'Read in supplied source; live reachability not tested except audit-listed attempts'))
    for section,rows in sections.items():
        if not rows: state='Fully mapped by child sections (heading only)'
        elif any('CONFLICT' in r[-1] for r in rows): state='Conflicting; decision log'
        elif any('VERIFY' in r[-1] for r in rows): state='Unverified facts retained; implementation mapping present'
        elif all('DEFERRED' in r[-1] for r in rows): state='Deliberately deferred'
        else: state='Fully mapped as design obligations; implementation pending'
        section_rows.append((filename,section,len(rows),state,', '.join(r[0] for r in rows)))
        section_count[filename]+=len(rows)

# PDF embedded URLs are independently inventoried, not guessed.
from pypdf import PdfReader
pdfname='NASA_Open_Data_Links_Earth_Impact_Intelligence.pdf'
for pi,page in enumerate(PdfReader(D/pdfname).pages,1):
    for a in page.get('/Annots',[]):
        url=a.get_object().get('/A',{}).get('/URI')
        if url: linkrows.append((pdfname,f'page {pi}',str(url),'Read and visually inspected; live URL not tested'))
section_rows += [(pdfname,'p1 §1 / §2',8,'Fully mapped: directory and access roles','PDF-01–PDF-08'),(pdfname,'p2 §2 continued / §3 / §4 / footer',14,'Fully mapped: priorities and practical notes; access rules VERIFY','PDF-09–PDF-22')]

doc(names[14],'Requirements traceability matrix',f'''
## Coverage gate and interpretation

This is the explicit deliverable matrix plus a lossless inventory of substantive Markdown source statements. One source bullet/table row can contain several subclauses; its entire text is retained below rather than silently shortened. Named screens/components/agents, APIs, dataset families, outputs, tests, conflicts and PDF notes also have individual rows. Original file headings and source line numbers identify context precisely. Rows marked VERIFY preserve reported facts; mapped does not mean implemented, approved or scientifically validated. No “100% implemented/verified” claim is made.

Source header labels and table separator formatting are not requirements; their context is retained through headings and complete data rows. The source's malformed repeated Agent table header is a formatting exception, not an additional agent. The architecture's ASCII dependency arrow is represented by the Mermaid DAG and H16/H24 handoffs. Remote mockup exact visual tokens, upstream links/rules, dataset metadata and actual access remain unverified. The PDF's referenced original slide was not supplied. No mandatory reference file is missing.

## Coverage summary

{table(['Source','Substantive source rows','Coverage state / exceptions'],[(f,section_count[f],'Mapped by section below; facts/proposals retain VERIFY/PROPOSED; exclusions deliberately deferred') for f in section_count]+[(pdfname,len(pdfnotes),'Both pages visually inspected; every portal, priority and practical note individually mapped')])}

Detailed file-and-heading summary: [source section coverage](14A_SOURCE_SECTION_COVERAGE.md). Link audit: [source URL register](14B_SOURCE_LINK_REGISTER.md). Every source row is a design obligation or explicit exclusion; human scientific/rights review is still required. Exact source claims are not fresh confirmations.

## Explicit deliverable, API, safety and PDF rows

{table(req_headers,trace)}

## Source-by-source exhaustive statement ledger

{table(req_headers,atomic)}
''')
doc('14A_SOURCE_SECTION_COVERAGE.md','Coverage by source file and heading',table(['Source file','Exact heading/page','Mapped statement count','State','Requirement IDs'],section_rows)+'\n\nNo mandatory source is missing. Fully mapped means a design/deferral/test destination exists, not that facts, code, licences or scientific claims are verified. Proposals and source conflicts remain visible in the master matrix and decision log.')
doc('14B_SOURCE_LINK_REGISTER.md','Source URL register',table(['Source file','Section/page','URL','Check status'],list(dict.fromkeys(linkrows)))+'\n\nExternal UI mockup, Space Apps Resources tab and ASF NISAR documentation attempts were inaccessible through the browsing tool. No blanket link reachability or official-rule verification claim is made. Local Markdown links in newly authored documents are checked separately by the planning validator.')

# A small independent planner validator is committed so the documentation gates can be rerun.
write('contracts/planning_manifest.json',json.dumps({'reference_sha256':hashes,'required_documents':names,'task_ids':[x[0] for x in tasks],'screens':[x[0] for x in screens],'components':[x[0] for x in components],'agents':list(agent_tasks),'endpoint_count':len(endpoints),'trace_ids':[x[0] for x in trace+atomic],'source_statement_lines':atom_index,'scope':'Planning only; schemas/fixtures draft; no real data or app tests executed'},indent=2))
write('README.md','''# CIVISAR implementation blueprint

Prepared 14 November 2026 from seven unchanged source references. This is a planning-only deliverable: no app, radar acquisition, live-data validation or deployment has been performed. Scientific observations are the source authors' **13 November 2026 snapshot**. Recommendations remain PROPOSED; missing scientific evidence stays VERIFY/BLOCKED.

Start with the source audit, scope, architecture and your member task file. Freeze shared contracts at hour 2. Safety, role enforcement and provenance are release blockers.

## Planning documents

'''+''.join(f'- [{name}]({name})\n' for name in names)+'''
## Supporting artifacts

- [Dataset exclusions](03A_DATASET_EXCLUSIONS.md)
- [Source section coverage](14A_SOURCE_SECTION_COVERAGE.md)
- [Source URL register](14B_SOURCE_LINK_REGISTER.md)
- [Member 1: radar/ML](tasks/MEMBER_1_RADAR_ML.md)
- [Member 2: geodata/alerts](tasks/MEMBER_2_GEODATA_ALERTS.md)
- [Member 3: backend/security](tasks/MEMBER_3_BACKEND_SECURITY.md)
- [Member 4: frontend/demo](tasks/MEMBER_4_FRONTEND_DEMO.md)
- [Contract inventory and eight synthetic JSON examples](contracts/README.md)
- [Draft OpenAPI](contracts/openapi.yaml)
- [Planning manifest](contracts/planning_manifest.json)
- [Rerunnable documentation validator](contracts/validate_planning.py)
- [ADR 001: modular monolith](adr/001_MODULAR_MONOLITH_AND_CONTRACTS.md)
- [ADR 002: publication and local routing](adr/002_PUBLICATION_AND_LOCAL_ROUTING.md)
- [ADR 003: scientific/data baseline](adr/003_RADAR_VALIDITY_AND_DATA_BASELINE.md)

## Untouched source references

'''+''.join(f'- [{f}]({f})\n' for f in hashes)+'''
## Actual validation

See [planning verification](16_PLANNING_VERIFICATION.md) for executed checks and limits. [Application acceptance](10_TESTING_AND_ACCEPTANCE_PLAN.md) contains future tests and does not imply they already ran. [Git workflow](11_DEVOPS_DEPLOYMENT_AND_GIT_WORKFLOW.md) distinguishes local branch setup from optional remote publication.
''')
write('16_PLANNING_VERIFICATION.md','''# Planning verification record

[Index](README.md)

Pending final validator run. This record will be replaced with actual results before commit. No application, scientific-data, hosting or field-safety test has been run in this planning-only repository.
''')
created.append('contracts/validate_planning.py')
(ROOT.parent/'planning-work/created-files.json').write_text(json.dumps(sorted(set(created)),indent=2),encoding='utf-8')
print(json.dumps({'created_files':len(set(created)),'tasks':len(tasks),'endpoints':len(endpoints),'explicit_trace_rows':len(trace),'source_statement_rows':len(atomic),'source_sections':len(section_rows)},indent=2))
