# Keys and settings (U-07)

Names, owners and expiry dates only. **Never put a value here, in Git, in a PR, in chat or in a screenshot.** Real values live in your local `.env` (ignored by Git) and in the deploy secret store (GitHub Actions secrets or the server's environment). Task: [doc 25](../25_NEW_PLAN_TASKS.md) U-07. Last updated 14 November 2026 by Udula.

## Secrets

| Name in `.env` | What it is for | Owner | Expires | Needed? |
|---|---|---|---|---|
| `EARTHDATA_TOKEN` | Download NASA data (NISAR, Black Marble) | Each person, own free Earthdata Login | About 60 days after it is made. Thanoban's ends about 13 January 2027. Udula downloads with an Earthdata login in `.netrc`, not a token | Only to download again |
| `FIRMS_MAP_KEY` | FIRMS history API for the permanent-hot-spot rule | Thanoban | No fixed expiry known | Optional: the 7-day public files need no key |
| `UCDP_ACCESS_TOKEN` | UCDP conflict events API | Whoever registers (Udula or Thanoban) | Not made yet | Optional: the UCDP CSV download works without it |
| `COPERNICUS_USER`, `COPERNICUS_PASSWORD` | Sentinel-2 colour texture for the 3D view | Whoever uses it | Not made yet | Optional |
| `ACLED_TOKEN` | ACLED events: context only, never for models or tests (ACLED terms) | Not assigned | Not made | No |
| `IOM_DTM_KEY` | IOM displacement data | Not assigned | Not made | No |
| `CIVISAR_DEMO_USERS_JSON` | Demo accounts (password hashes, roles, area scopes) | Rashiru for deploy; each person locally (`python -m scripts.create_demo_user`) | Never shared | Yes |
| `DATABASE_URL` | Database connection | Rashiru for deploy; local default in `.env.example` | Never shared | Yes |
| `SESSION_SECRET` | Reserved for signed sessions; the demo keeps sessions in memory and does not read it yet | Rashiru | Not made | Not yet |

## Settings (not secret)

| Name | Meaning | Default |
|---|---|---|
| `DEMO_SYNTHETIC` | `true` serves the synthetic fixtures; `false` serves real data | `true` |
| `PUBLISHED_DIR` | Where the API reads published agent and ML files | `data/published` |
| `PUBLIC_RELEASE_APPROVED` | Whether the public map may show data. Stays `false` until a person approves a release | `false` |
| `ALLOWED_ORIGIN`, `COOKIE_SECURE` | Browser origin and cookie flag | local values in `.env.example` |
| `DATA_ROOT`, `CIVISAR_DB_PORT`, `NIGHTLIGHT_HISTORY`, `FIRE_RELEASE_DELAY_HOURS` | Backend real-data mode (branch `feature/m3-01-backend-foundation`, see doc 31) | `data`, `5432`, empty, `0` |

## Rules

1. A new key **name** goes into `.env.example` with an empty value, in a PR.
2. When a key is made, rotated or close to expiry, tell Rashiru the **name and expiry date**, never the value, so the deploy store is updated. Update this table.
3. A key pasted anywhere public is leaked: make a new one at once and revoke the old one.
4. `python -m scripts.check_secrets` must pass before every push.
