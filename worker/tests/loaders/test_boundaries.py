from pathlib import Path

import geopandas as gpd

from worker.loaders.boundaries import KEEP_COLUMNS, load_boundaries

FIXTURE = Path(__file__).with_name("fixture_boundaries.geojson")


def test_load_boundaries_clips_to_demo_box():
    gdf = load_boundaries(FIXTURE, write_outputs=False)
    assert list(gdf.columns) == KEEP_COLUMNS
    assert len(gdf) == 2
    assert set(gdf["admin_id"]) == {"G1", "D1"}
    assert gdf.crs is not None


def test_every_district_has_a_parent():
    gdf = load_boundaries(FIXTURE, write_outputs=False)
    districts = gdf[gdf["level"] == 2]
    assert len(districts) == 1
    assert districts["parent_id"].notna().all()
    assert (districts["parent_id"] == "G1").all()


def test_no_empty_geometry():
    gdf = load_boundaries(FIXTURE, write_outputs=False)
    assert gdf.geometry.notna().all()
    assert (~gdf.geometry.is_empty).all()
    assert gdf["name_en"].notna().all()
    assert gdf["admin_id"].notna().all()
