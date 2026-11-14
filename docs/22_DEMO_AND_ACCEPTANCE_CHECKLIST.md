# Demo and acceptance checklist

Status board for either [24h or 48h scenario](20_24H_AND_48H_HACKATHON_ROADMAP.md). Check boxes mean **verified evidence attached**, not planned work. A owns release decision; B/C independently check their science. The challenge duration and current official rules still need confirmation.

## Core challenge and science

- [ ] Record the official challenge rules/Resources page and permitted preparation window; cite the checked source and date.
- [ ] Show NISAR as the core surface-change source, with actual granule IDs, acquisition dates, track/frame, polarization and processing version when real data is used.
- [ ] Show interactive MapLibre selection, before/after/change comparison and time slider **only for actual available passes**; mark gaps and disabled controls.
- [ ] Explain HH/HV and candidate change without claiming confirmed destruction; distinguish GIBS context from analytical radar output.
- [ ] B signs registration, valid footprint and BETA/PROVISIONAL version QA; C signs spatial hold-out, independent controls, top-cell review and limitations. If absent, mark real-data demonstration blocked.
- [ ] Separate synthetic examples from observed, reported, corroborated and Unknown evidence on every map, card, print and recording frame.

## Application, security and humanitarian use

- [ ] Select an area and obtain its summary and source from the API, with typed responses, loading/error/unknown states and source dates.
- [ ] Verify session restoration/logout and server-side anonymous, analyst, officer and coordinator denials. A hidden UI control is not a security test.
- [ ] Verify no real sensitive civilian site, route, dispatch origin, identifiable concentration or unreviewed r9 cell leaks via API, tile, file, trace, export or cache.
- [ ] Verify any real strike-related change is held at least 72 hours and public derivatives receive r8 aggregation **and** suppression/review.
- [ ] Use “Fire detected” without inferred cause, “Possible power loss”, “candidate damage”, “no reported closure” and “candidate for checking” where applicable.
- [ ] Show humanitarian value through an evidence-aware area summary. Do not invent population, service or supply quantities.
- [ ] Test keyboard navigation, map-equivalent area control, focus visibility, light/dark contrast, mobile field views if included and print output if included.

## Sources, demo, submission and recovery

- [ ] Sources page lists every used dataset with provider, product level, acquisition date, processing version, licence/terms, URL, accessed date and limitations.
- [ ] Reconcile actual NASA Resources-tab attribution and dataset licences; do not repeat the unverified five/six count as fact.
- [ ] Run planning validator, contract tests, backend tests, frontend tests/lint/build, secret scan and any available DB/Compose smoke check; record failures and blocked checks.
- [ ] Rehearse a short primary story: problem → NISAR dates → comparison/polarization → area → evidence/uncertainty → source → role denial → limitations.
- [ ] Record a longer backup walkthrough and a local/offline fallback before the feature freeze; verify video playback and captions/legibility.
- [ ] Confirm submission fields, citations, repository link and video requirements against current official rules. Record who submits and the deadline in local time.
- [ ] Keep a sanitized backup of the approved demo state and reproduce restoration; never include secrets or restricted real locations.
- [ ] Record explicit go/no-go decision with A/B/C acknowledgements. A scientific or privacy failure blocks a real-data/public claim, even if the UI works.

**Current state:** checklist open. The first synthetic vertical slice is a development milestone, not a complete NISAR MVP or an approved field-use product.
