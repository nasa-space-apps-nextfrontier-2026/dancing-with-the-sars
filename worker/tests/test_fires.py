from worker.services.fires import FirePoint, cluster, fire_events, keep, permanent_spots


def pt(lat, lon, time, conf="high", sat="NOAA-20"):
    return FirePoint(lat, lon, time, conf, sat)


def test_low_confidence_points_are_dropped():
    assert keep([pt(33.3, 35.4, "2026-11-12T10:00:00Z", "low")], set()) == []


def test_nearby_points_within_hours_form_one_event_from_two_satellites():
    pts = [pt(33.300, 35.400, "2026-11-12T10:00:00Z", "nominal", "NOAA-20"),
           pt(33.304, 35.402, "2026-11-12T14:30:00Z", "high", "NOAA-21")]
    events = cluster(pts)
    assert len(events) == 1
    event = events[0]
    assert event.kind == "fire_detected" and event.points == 2
    assert event.satellites == ("NOAA-20", "NOAA-21") and event.confidence == "high"


def test_far_apart_or_far_in_time_are_separate_events():
    far_place = [pt(33.30, 35.40, "2026-11-12T10:00:00Z"), pt(33.40, 35.40, "2026-11-12T10:30:00Z")]
    far_time = [pt(33.30, 35.40, "2026-11-12T01:00:00Z"), pt(33.30, 35.40, "2026-11-13T01:00:00Z")]
    assert len(cluster(far_place)) == 2 and len(cluster(far_time)) == 2


def test_a_bridging_point_merges_two_groups():
    pts = [pt(33.300, 35.400, "2026-11-12T10:00:00Z"), pt(33.316, 35.400, "2026-11-12T10:10:00Z"),
           pt(33.308, 35.400, "2026-11-12T10:20:00Z")]
    assert len(cluster(pts)) == 1


def test_permanent_hot_spot_is_removed_but_a_new_fire_next_to_it_stays():
    baseline = [pt(33.3000, 35.4000, f"2026-10-{d:02d}T10:00:00Z") for d in range(1, 8)]
    today = [pt(33.3000, 35.4000, "2026-11-12T10:00:00Z"), pt(33.3200, 35.4200, "2026-11-12T10:00:00Z")]
    assert len(permanent_spots(baseline)) == 1
    events = fire_events(today, baseline)
    assert len(events) == 1 and abs(events[0].lat - 33.32) < 0.001


def test_no_event_text_claims_a_cause():
    event = cluster([pt(33.3, 35.4, "2026-11-12T10:00:00Z")])[0]
    assert event.kind == "fire_detected"
    assert not hasattr(event, "cause")
