"""U-01 building table on a small synthetic fixture (doc 25: area right, unique ids, every building
has a cell). Shapes here are made up for the test, not real buildings."""

import pytest

shapely = pytest.importorskip("shapely")
pyproj = pytest.importorskip("pyproj")
h3 = pytest.importorskip("h3")

import pandas as pd

from pipelines.buildings import base

TO_LL = pyproj.Transformer.from_crs(base.METRIC_CRS, "EPSG:4326", always_xy=True)
TO_M = pyproj.Transformer.from_crs("EPSG:4326", base.METRIC_CRS, always_xy=True)
X0, Y0 = TO_M.transform(35.5, 33.3)  # inside the demo box


def rect(dx, dy, w, h):
    pts = [(X0 + dx, Y0 + dy), (X0 + dx + w, Y0 + dy), (X0 + dx + w, Y0 + dy + h), (X0 + dx, Y0 + dy + h)]
    return shapely.Polygon([TO_LL.transform(x, y) for x, y in pts])


def table(rows):
    return pd.DataFrame([{"id": i, "building": tag, "building_levels": lv, "geom": shapely.to_wkb(g)}
                         for i, tag, lv, g in rows])


def fixture():
    bowtie = shapely.Polygon([TO_LL.transform(X0 + 100 + x, Y0 + y) for x, y in
                              ((0, 0), (10, 10), (10, 0), (0, 10))])
    return table([
        ("way/1", "house", "2", rect(0, 0, 20, 10)),            # 200 m2
        ("way/2", "yes", None, rect(50, 0, 10, 10)),            # untyped
        ("way/2", "yes", None, rect(50, 0, 10, 10)),            # duplicate id
        ("way/3", "hospital", "4.5", rect(0, 50, 30, 30)),
        ("way/4", "ruins", "junk", rect(80, 80, 5, 5)),
        ("node/5", "school", None, shapely.Point(35.5, 33.3)),  # no outline
        ("way/6", "house", None, shapely.Polygon([(10.0, 10.0), (10.001, 10.0), (10.001, 10.001)])),  # far away
        ("way/7", "garage", None, bowtie),                      # self-crossing outline
    ])


def test_area_is_metric_and_right():
    rows, _ = base.build(fixture())
    house = rows.set_index("building_id").loc["way/1"]
    assert house["footprint_m2"] == pytest.approx(200, rel=0.01)


def test_ids_unique_and_every_building_has_cells():
    rows, counts = base.build(fixture())
    assert rows["building_id"].is_unique
    assert counts["dropped_duplicate_ids"] == 1
    assert all(h3.get_resolution(c) == 9 for c in rows["h3_r9"])
    assert all(h3.cell_to_parent(a, 8) == b for a, b in zip(rows["h3_r9"], rows["h3_r8"], strict=True))


def test_points_outside_and_broken_shapes_handled():
    rows, counts = base.build(fixture())
    ids = set(rows["building_id"])
    assert "node/5" not in ids and counts["dropped_points_or_lines"] == 1
    assert "way/6" not in ids and counts["dropped_outside_box"] == 1
    assert counts["repaired_outlines"] == 1  # the bow tie is repaired, not silently kept broken
    assert counts["buildings"] == len(rows) == 5


def test_use_mapping_is_honest():
    rows = base.build(fixture())[0].set_index("building_id")
    assert rows.loc["way/1", "use"] == "residential"
    assert rows.loc["way/2", "use"] == "unknown"  # building=yes is not assumed residential
    assert rows.loc["way/3", "use"] == "hospital" and rows.loc["way/3", "facility_flag"]
    assert rows.loc["way/4", "use"] == "unknown" and rows.loc["way/4", "osm_condition_tag"] == "ruins"
    assert rows.loc["way/7", "use"] == "other"
    assert base.use_of(None) == "unknown"


def test_levels_parse():
    assert base.parse_levels("2") == 2 and base.parse_levels("4,5") == 4.5
    assert base.parse_levels("junk") is None and base.parse_levels("-1") is None
    assert base.parse_levels(None) is None
