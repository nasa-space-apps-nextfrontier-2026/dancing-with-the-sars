# Instructions for coding agents (Codex, Claude Code, others)

- Work on branch `dev`; make `feature/<task-id>-<name>` branches from it. Never push to `main`.
- **Frontend work: read `frontend/README.md`, `docs/26_3D_MAP_UI_AND_FRONTEND.md` and open `docs/design/civisar-3d-map-mockup.html` first.** The 3D map mockup is the UI source of truth (the old light prototype is archived in `docs/design/archive/`).
- Safety rules: never label anything "safe"; use evidence labels Observed / Reported / Corroborated / Unknown; no live vehicle or phone tracking; no sign-in in the public app (decided 15 Nov 2026), which shows labelled sample data.
- Contracts live only in `docs/contracts/`. No large data or secrets in Git.
- Commits use the human author's name, no AI co-author line.
