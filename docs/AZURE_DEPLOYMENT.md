# Azure public demo deployment

The public, labelled sample-data frontend uses Azure App Service, Linux Free F1, in Central India. This does not deploy FastAPI, PostGIS, the scheduler or radar processing. The Sources catalogue API remains unavailable until a backend is separately configured. Do not publish local datasets or server environment files.

## Hosting

- Subscription: Azure for Students.
- App: `rescueforce-demo`.
- Resource group: `rescueforce-demo_group-bf42`.
- Domain: `https://rescueforce-demo-f7dpg9fzfaashefk.centralindia-01.azurewebsites.net`.
- Plan: Free F1, Linux, Node 22 LTS; paid monitoring add-ons are not enabled.
- Deployment branch: `feature/m4-azure-deployment`, reviewed through a PR into `dev`. Never push to `main`.

Build with Node 24: `npm ci` and `npm run build` in `frontend/`. The deployment artifact contains only `frontend/dist/`, `frontend/server.mjs`, and the runtime manifest `infrastructure/azure/package.json`. Start with `npm start`. The dependency-free Node host serves `/` and `/map`, keeps missing APIs/assets as errors, and does not expose repository files. GitHub deployment uses a federated Azure identity rather than a stored Azure password.

Azure Static Web Apps cannot currently be created in this student subscription: its allowed regions are Korea Central, UAE North, Central India, India South Central and Malaysia West, with no overlap with Static Web Apps regional options. `frontend/public/staticwebapp.config.json` remains available for a future Static Web Apps deployment if region eligibility changes; it has no effect on the Node host.

An optional `VITE_CESIUM_ION_TOKEN` is browser-visible. Use only a Cesium token intended for public clients, restricted to the deployed domain. Never put NASA, database or server credentials in Vite variables. Without a token, the documented flat-ground map mode remains available.

After deployment, check `/`, direct navigation and refresh at `/map`, sample-data loading, the Sample data badge and the Sources panel's unavailable state. Free F1 has daily compute limits and cold starts. Review the runtime version before support expires. Keep the student spending limit; do not upgrade to a paid plan as part of this demo deployment.
