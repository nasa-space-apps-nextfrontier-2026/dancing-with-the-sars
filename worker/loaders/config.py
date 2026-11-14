"""Configuration for the Lebanon administrative boundaries loader"""

from pathlib import Path

# --- Demo box (south Lebanon), WGS84, from the NISAR south-lebanon-demo AOI ---
DEMO_AOI = "south-lebanon-demo"
DEMO_BBOX_WGS84 = (35.0, 33.0, 36.0, 33.6)  # west, south, east, north

# --- HDX source: OCHA COD-AB Lebanon subnational administrative boundaries ---
HDX_BASE_URL = "https://data.humdata.org"
HDX_DATASET_NAME = "Lebanon - Subnational Administrative Boundaries"
HDX_DATASET_ID = "569beba7-bad7-4951-a19d-468a035461cd"
HDX_GEOJSON_RESOURCE_ID = "81ca0135-b5c9-46e0-a546-f0bdd6d7fd42"
SOURCE_URL = (
    f"{HDX_BASE_URL}/dataset/{HDX_DATASET_ID}/resource/"
    f"{HDX_GEOJSON_RESOURCE_ID}/download/lbn_admin_boundaries.geojson.zip"
)
LICENCE = "Creative Commons Attribution for Intergovernmental Organisations (CC BY-IGO)"
LICENCE_URL = f"{HDX_BASE_URL}/dataset/{HDX_DATASET_ID}"

# --- Paths (raw download is local-only and never committed) ---
ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "lbn_admin"
LOCAL_DIR = DATA_DIR / "local"
MANIFESTS_DIR = DATA_DIR / "manifests"
BOUNDARIES_GEOJSON = LOCAL_DIR / "boundaries.geojson"
BOUNDARIES_MANIFEST = MANIFESTS_DIR / "boundaries.json"

ADMIN1_FILENAME = "lbn_admin1.geojson"
ADMIN2_FILENAME = "lbn_admin2.geojson"

# --- K-02 grid ---
GRID_CSV_GZ = LOCAL_DIR / "grid_r9.csv.gz"
GRID_MANIFEST = MANIFESTS_DIR / "grid.json"

# --- Output ---
MAX_OUTPUT_BYTES = 1_000_000  # simplify geometry until the GeoJSON is under 1 MB
