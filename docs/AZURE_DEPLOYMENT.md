# Azure public demo deployment

Deploy the public, labelled sample-data frontend to Azure Static Web Apps using the Free plan. This does not deploy the FastAPI backend, PostGIS database, scheduler or radar processing. The Sources catalogue API remains unavailable until a backend is separately configured. Do not publish local datasets or server environment files.

Use these deployment settings:

- Repository: `nasa-space-apps-nextfrontier-2026/dancing-with-the-sars`
- Branch: the reviewed branch containing the Azure configuration; merge via a PR into `dev`, never push to `main`.
- App location: `frontend`
- API location: leave empty
- Output location: `dist`
- Build: `npm ci` followed by `npm run build`, using Node 24.
- Plan: Free.

`frontend/public/staticwebapp.config.json` is copied by Vite to the deployment output. Its fallback supports opening and refreshing `/map` directly, while missing APIs and static assets keep their error responses.

An optional `VITE_CESIUM_ION_TOKEN` is a browser-visible build setting. Use only a Cesium token intended for public clients, restricted to the deployed domain. Never place NASA, database or server credentials in Vite variables. Without a Cesium token, the documented flat-ground map mode remains available.

After deployment, check `/`, direct navigation and refresh at `/map`, sample-data loading, the Sample data badge and the Sources panel's unavailable state. Verify the actual subscription offer and credit balance separately; a generic Azure subscription name does not establish student-credit eligibility. Keep the student spending limit and do not upgrade to a paid plan as part of this demo deployment.
