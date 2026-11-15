"""U-02 height ranges on synthetic fixtures (doc 25: priority order, floors = height / 3, low not
above high, every building has a source). Values are made up for the test."""

import math

import pytest

shapely = pytest.importorskip("shapely")
pyproj = pytest.importorskip("pyproj")
pytest.importorskip("h3")

import pandas as pd

from pipelines.buildings import base, heights

TO_LL = pyproj.Transformer.from_crs(base.METRIC_CRS, "EPSG:4326", always_xy=True)
TO_M = pyproj.Transformer.from_crs("EPSG:4326", base.METRIC_CRS, always_xy=True)
X0, Y0 = TO_M.transform(35.5, 33.3)


def rect(dx, dy, w=20, h=20):
    pts = [(X0 + dx, Y0 + dy), (X0 + dx + w, Y0 + dy), (X0 + dx + w, Y0 + dy + h), (X0 + dx, Y0 + dy + h)]
    return shapely.Polygon([TO_LL.transform(x, y) for x, y in pts])


def ll(dx, dy):
    return TO_LL.transform(X0 + dx, Y0 + dy)


def test_priority_order():
    assert heights.height_range(3, 12.0, "residential")[2] == "osm"       # OSM tag wins
    assert heights.height_range(None, 12.0, "residential")[2] == "ghsl"
    assert heights.height_range(float("nan"), float("nan"), "hospital") == (6.0, 24.0, "default")
    assert heights.height_range(0, None, "unknown")[2] == "default"       # 0 levels is not a height


def test_ranges_and_floors():
    lo, hi, _ = heights.height_range(4, None, "residential")
    assert (lo, hi) == pytest.approx((10.8, 13.2))
    assert heights.floors(lo, hi, 4) == (4, 4)                               # OSM levels as tagged
    assert heights.floors(13.5, 16.5, 5) == (5, 5) and heights.floors(6.0, 9.0, 2.5) == (2, 3)
    assert heights.floors(13.5, 16.5) == (5, 6)                              # halves round up
    assert heights.height_range(None, 2.5, "unknown") == (3.0, 7.0, "ghsl")  # GHSL floor: not resolved
    lo, hi, _ = heights.height_range(None, 4.0, "unknown")
    assert lo == 3.0 and hi == 8.5                                           # never below one storey
    for lv, gh, use in [(1, None, "x"), (None, 30.0, "school"), (None, None, "power"), (2.5, 3.0, "other")]:
        lo, hi, _ = heights.height_range(lv, gh, use)
        fl, fh = heights.floors(lo, hi)
        assert 3.0 <= lo <= hi and 1 <= fl <= fh
        assert fl == max(1, math.floor(lo / 3 + 0.5)) and fh == max(fl, math.floor(hi / 3 + 0.5))


def test_small_neighbour_takes_nearby_ghsl_value():
    rows = pd.DataFrame([
        {"id": "way/1", "building": "house", "building_levels": None, "geom": shapely.to_wkb(rect(0, 0))},
        {"id": "way/9", "building": "shed", "building_levels": None, "geom": shapely.to_wkb(rect(23, 0, 4, 4))},
        {"id": "way/8", "building": "shed", "building_levels": None, "geom": shapely.to_wkb(rect(60, 0, 4, 4))},
    ])
    b, _ = base.build(rows)
    obat = pd.DataFrame([{"lon": ll(10, 10)[0], "lat": ll(10, 10)[1], "height": 7.0, "use": 1, "epoch": 3,
                          "area": 400}])
    out = heights.build(b, obat).set_index("building_id")
    assert out.loc["way/1", "ghsl_match"] == "footprint"
    assert out.loc["way/9", "ghsl_match"] == "nearby" and out.loc["way/9", "ghsl_height_m"] == 7.0
    assert out.loc["way/8", "height_source"] == "default"  # 46 m away: too far


def test_matching_inside_nearest_and_too_far():
    rows = pd.DataFrame([
        {"id": "way/1", "building": "house", "building_levels": None, "geom": shapely.to_wkb(rect(0, 0))},
        {"id": "way/2", "building": "yes", "building_levels": None, "geom": shapely.to_wkb(rect(100, 0))},
        {"id": "way/3", "building": "yes", "building_levels": None, "geom": shapely.to_wkb(rect(200, 0))},
        {"id": "way/4", "building": "yes", "building_levels": "5", "geom": shapely.to_wkb(rect(300, 0))},
    ])
    b, _ = base.build(rows)
    obat = pd.DataFrame([
        # two footprints inside way/1: area-weighted mean = (6*100 + 12*300) / 400 = 10.5
        {"lon": ll(5, 5)[0], "lat": ll(5, 5)[1], "height": 6.0, "use": 1, "epoch": 2, "area": 100},
        {"lon": ll(15, 15)[0], "lat": ll(15, 15)[1], "height": 12.0, "use": 1, "epoch": 2, "area": 300},
        # 5 m outside way/2: nearest within 10 m
        {"lon": ll(125, 10)[0], "lat": ll(125, 10)[1], "height": 9.0, "use": 2, "epoch": 4, "area": 50},
        # 40 m from way/3: too far, no match
        {"lon": ll(260, 10)[0], "lat": ll(260, 10)[1], "height": 20.0, "use": 2, "epoch": 5, "area": 50},
        # inside way/4, but its OSM levels win
        {"lon": ll(310, 10)[0], "lat": ll(310, 10)[1], "height": 3.0, "use": 1, "epoch": 1, "area": 80},
    ])
    out = heights.build(b, obat).set_index("building_id")
    assert out.loc["way/1", "ghsl_height_m"] == pytest.approx(10.5)
    assert out.loc["way/1", "ghsl_matches"] == 2 and out.loc["way/1", "use_ghsl"] == "residential"
    assert out.loc["way/2", "ghsl_height_m"] == pytest.approx(9.0) and out.loc["way/2", "built_epoch"] == "2000_2010"
    assert math.isnan(out.loc["way/3", "ghsl_height_m"]) and out.loc["way/3", "height_source"] == "default"
    assert out.loc["way/1", "ghsl_match"] == "footprint" and out.loc["way/3", "ghsl_match"] == "none"
    assert out.loc["way/4", "height_source"] == "osm" and out.loc["way/4", "floors_low"] == 5
    assert out["height_source"].notna().all()
    assert (out["height_low_m"] <= out["height_high_m"]).all()
