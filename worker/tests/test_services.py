from worker.services.cmr import DEMO_BBOX, build_query, manifest, parse_response, search

SAMPLE = {"feed": {"entry": [
    {"id": "G1", "title": "VJ146A2_NRT.A2026316.h21v05", "time_start": "2026-11-12T00:00:00.000Z",
     "time_end": "2026-11-12T23:59:59.000Z",
     "links": [{"rel": "http://esipfed.org/ns/fedsearch/1.1/data#", "href": "https://example.org/a.h5"}]},
    {"id": "G2", "title": "VJ146A2_NRT.A2026315.h21v05", "time_start": "2026-11-11T00:00:00.000Z",
     "time_end": "2026-11-11T23:59:59.000Z", "links": []},
]}}


def test_query_has_demo_box_and_product():
    url = build_query("VJ146A2_NRT")
    assert "short_name=VJ146A2_NRT" in url
    assert "bounding_box=35.0%2C33.0%2C36.0%2C33.6" in url
    assert DEMO_BBOX == (35.0, 33.0, 36.0, 33.6)


def test_parse_keeps_missing_download_link_as_none():
    rows = parse_response("VJ146A2_NRT", SAMPLE)
    assert [r.granule_id for r in rows] == ["G1", "G2"]
    assert rows[0].download_url == "https://example.org/a.h5"
    assert rows[1].download_url is None


def test_search_stops_when_page_is_short_and_manifest_counts():
    rows = search("VJ146A2_NRT", fetch=lambda url: SAMPLE)
    info = manifest(rows)
    assert info["counts"] == {"VJ146A2_NRT": 2}
    assert info["newest"]["VJ146A2_NRT"] == "2026-11-12"


def test_start_and_end_dates_become_a_temporal_range():
    url = build_query("VJ146A2", start="2026-07-01", end="2026-11-14")
    assert "temporal=2026-07-01T00%3A00%3A00Z%2C2026-11-14T23%3A59%3A59Z" in url
    assert "temporal=%2C" not in build_query("VJ146A2", end=None)
    assert "temporal" not in build_query("VJ146A2")
