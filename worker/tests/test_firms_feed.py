import pytest

from worker.services.fires import FirePoint
from worker.services.firms_feed import current_events, feed_url, parse_points

HEADER = "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,confidence,version,bright_ti5,frp,daynight"
ROWS = [
    HEADER,
    "33.30,35.40,340.1,0.4,0.4,2026-11-12,0930,N20,n,2.0NRT,290.0,3.2,D",   # inside the box
    "33.304,35.404,345.1,0.4,0.4,2026-11-12,1010,N20,h,2.0NRT,291.0,5.0,D",   # inside, 40 min later
    "34.50,35.40,330.1,0.4,0.4,2026-11-12,0930,N20,n,2.0NRT,290.0,1.0,D",   # outside (north)
    "33.30,37.00,330.1,0.4,0.4,2026-11-12,0930,N20,n,2.0NRT,290.0,1.0,D",   # outside (east)
]


def test_urls_cover_both_satellites_and_reject_unknown_feeds():
    assert feed_url("NOAA-20", "7d").endswith("noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_7d.csv")
    assert feed_url("NOAA-21", "24h").endswith("noaa-21-viirs-c2/csv/J2_VIIRS_C2_Global_24h.csv")
    with pytest.raises(ValueError):
        feed_url("S-NPP", "24h")


def test_parse_keeps_only_points_inside_the_box_with_utc_times():
    pts = parse_points(ROWS, "NOAA-20")
    assert len(pts) == 2
    assert pts[0].time == "2026-11-12T09:30:00+00:00" and pts[0].confidence == "n"


def test_current_events_groups_nearby_points_from_the_latest_day():
    def fake(sat, window, bbox):
        return parse_points(ROWS, sat, bbox) if sat == "NOAA-20" else []

    events, info = current_events(fetch=fake)
    assert len(events) == 1 and events[0].kind == "fire_detected" and events[0].points == 2
    assert info["latest_day"] == "2026-11-12" and info["points"] == 2


def test_no_points_gives_no_events_and_a_note():
    def nothing(sat, window, bbox):
        return []

    events, info = current_events(fetch=nothing)
    assert events == [] and info["points"] == 0
    assert isinstance(FirePoint(0, 0, "2026-01-01T00:00:00+00:00", "n", "NOAA-20"), FirePoint)
