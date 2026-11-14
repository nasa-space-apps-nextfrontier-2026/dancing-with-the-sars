# CIVISAR frontend: build guide (for Rashiru and his coding tools)

**Read this first, then build.** The UI is already designed. Do not invent screens, colours or wording.

1. **Open `docs/design/civisar-prototype.html` in a browser.** It is the UI source of truth: tokens, components, screens, light and dark themes. Read its HTML and CSS directly.
2. Read `docs/UI_DESIGN.md` (screens, outputs, wording rules, the build rules) and `docs/06_FRONTEND_DESIGN_AND_SCREEN_PLAN.md` (screen plan).
3. The API is the draft in `docs/contracts/openapi.yaml`. Use mock data from `docs/contracts/` fixtures until the real endpoints exist.

## Build rules
- Copy the prototype's CSS variables (`:root` and `[data-theme="dark"]`) into `src/styles.css`. No new colours.
- One React component per prototype component or screen, in `src/components/`, with the same labels and wording.
- Evidence labels are exactly Observed, Reported, Corroborated, Unknown. Never write "safe". Show ranges, not single numbers. "Possible power loss", not "blackout". "Fire detected", never a cause.
- Keep the "illustrative data" badge wherever mock data shows.
- Login is required: build the sign-in screen and the logged-out view (public-safe map only).
- No vehicle, convoy or phone tracking anywhere.
- Do not edit the prototype in a feature PR. Change it only through a `docs/` PR.
- Branch `feature/m4-<name>` from `dev`, PR into `dev` (see `docs/17_TEAM_ASSIGNMENT_AND_BRANCHES.md`).

## Order
Tokens and theme, app shell, main map and time slider, alert feed and inspector, then summary, routes, shelters, sources, sign-in, print and phone layout (cut first if short on time).
