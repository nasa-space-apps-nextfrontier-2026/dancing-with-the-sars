# Dataset records for Thanoban's models (M1-04)

The per-dataset record required by [DATASETS.md](../DATASETS.md) section 7 and [13](../13_DEMO_STORY_SUBMISSION_AND_CITATIONS.md), for the data used by the night-light and fire models. Facts below were checked on 14 November 2026 unless marked **VERIFY**.

## Black Marble daily night lights (NOAA-20 and NOAA-21)

| Field | Record |
|---|---|
| Dataset name | VIIRS/NOAA-20 and NOAA-21 Black Marble Nighttime Lights, daily, gap-filled and BRDF-corrected |
| Product short names | `VJ146A2` (NOAA-20, archive), `VJ246A2` (NOAA-21, archive), `VJ146A2_NRT` and `VJ246A2_NRT` (near real time) |
| Level | Level 3 gridded, daily |
| Provider | NASA (LAADS DAAC for the archive; LANCE for near real time) |
| CMR concept IDs | VJ146A2 `C3370789118-LAADS`; NRT `C4193331158-LANCEMODIS` (NOAA-20) and `C4249684820-LANCEMODIS` (NOAA-21) |
| Processing version | 002 (from file names such as `VJ146A2_NRT.A2026316.h21v05.002...`) |
| Spatial coverage used | Tile `h21v05` (30–40 E, 30–40 N), cropped to the demo box 35.0–36.0 E, 33.0–33.6 N |
| Resolution | 2400 x 2400 pixels per 10 degree tile, 15 arc-seconds (about 450 m) |
| Fields used | `DNB_BRDF-Corrected_NTL`, `Mandatory_Quality_Flag`, `QF_Cloud_Mask` (bits 6–7 for cloud detection) |
| Dates used | Last 120 days up to 12 Nov 2026 (archive newest 28 Oct for NOAA-20 and 4 Nov for NOAA-21; near real time from 6 Nov) |
| Access | CMR search; download with an Earthdata Login token; the NRT service needs the Earthdata application "LANCE" authorised |
| Date accessed | 14 Nov 2026 |
| Terms and citation | NASA open data. Exact citation text and any attribution requirement: **VERIFY** on the LAADS DAAC and LANCE product pages before the submission |
| Known limits | About 450 m pixels, so no building-level power certainty; clouds and moonlight affect radiance; the archive lags 1 to 2 weeks and near real time keeps about 7 days, leaving a gap for NOAA-20 (29 Oct to 5 Nov); about 70% of cells are `unknown` (sea, dark land or too few clear nights); the 6 Nov near-real-time files returned 404 |
| Used by | `worker/services/nightlights.py`, `power_loss.py`, `blackmarble_history.py` |

## FIRMS VIIRS 375 m active fire (NOAA-20 and NOAA-21)

| Field | Record |
|---|---|
| Dataset name | FIRMS VIIRS 375 m active fire detections (collection 2) |
| Provider | NASA LANCE / FIRMS |
| Files used | `noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_7d.csv` and `noaa-21-viirs-c2/csv/J2_VIIRS_C2_Global_7d.csv` under `https://firms.modaps.eosdis.nasa.gov/data/active_fire/` (24 h and 48 h variants exist); public, no map key |
| Fields used | latitude, longitude, acquisition date and time (UTC), confidence (low, nominal, high), satellite |
| Spatial coverage used | Global files streamed and filtered to the demo box |
| Resolution | 375 m |
| Date accessed | 14 Nov 2026 (about 390,000 global rows per 7-day file; 2 detections in the demo box) |
| Terms and citation | NASA open data. Exact citation text: **VERIFY** on the FIRMS site before the submission |
| Known limits | A detection is a heat signal, not proof of a strike or its cause; 7 days is too short to find permanent hot spots (needs 5 or more days) so a longer baseline needs the FIRMS history API and a free map key; Suomi NPP is not used (its delivery stopped on 2 Nov 2026) |
| Used by | `worker/services/fires.py`, `firms_feed.py` |

## Event data for the strike tests (not used yet)

| Field | Record |
|---|---|
| Source chosen | UCDP Georeferenced Event Dataset (GED) |
| Why not ACLED | ACLED's terms bar using its data to train or test ML models, and a free ACLED account has no API access |
| Access | UCDP API needs a free access token ("API token required"); or a CSV download filtered to Lebanon |
| Status | Not downloaded. Terms and citation: **VERIFY** when the data is obtained |
