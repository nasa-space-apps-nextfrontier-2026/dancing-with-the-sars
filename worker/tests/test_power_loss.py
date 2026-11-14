from worker.services.nightlights import Night
from worker.services.power_loss import combine, power_loss_events


def nights(values, start=1, clear=True):
    return [Night(f"2026-10-{start + i:02d}", v, clear) for i, v in enumerate(values)]


def pair(recent_values, history_len=60):
    return nights([10.0] * history_len), nights(recent_values, start=history_len % 28 + 1)


def test_both_satellites_flag_gives_corroborated_possible_power_loss():
    result = combine("c1", {"NOAA-20": pair([2.0, 2.0]), "NOAA-21": pair([2.0, 2.0])})
    assert result.status == "possible_power_loss" and result.corroborated
    assert result.confidence == "high" and result.satellites_flagged == ("NOAA-20", "NOAA-21")
    assert result.label == "Observed"


def test_one_satellite_flag_is_low_confidence_and_not_corroborated():
    result = combine("c1", {"NOAA-20": pair([2.0, 2.0]), "NOAA-21": pair([9.5, 10.0])})
    assert result.status == "possible_power_loss" and not result.corroborated
    assert result.confidence == "low" and result.satellites_flagged == ("NOAA-20",)


def test_a_flag_next_to_an_unknown_satellite_stays_low():
    unknown = (nights([10.0] * 5), nights([2.0, 2.0], start=6))     # too few baseline nights
    result = combine("c1", {"NOAA-20": pair([2.0, 2.0]), "NOAA-21": unknown})
    assert result.confidence == "low" and not result.corroborated


def test_no_flag_is_no_change_and_nothing_assessable_is_unknown():
    assert combine("c1", {"NOAA-20": pair([9.0, 10.0])}).status == "no_change"
    unknown = (nights([10.0] * 5), nights([2.0, 2.0], start=6))
    result = combine("c1", {"NOAA-20": unknown, "NOAA-21": unknown})
    assert result.status == "unknown" and any("baseline" in r for r in result.reasons)


def test_events_have_the_alert_fields_and_skip_quiet_cells():
    series = {}
    for sat in ("NOAA-20", "NOAA-21"):
        series[(sat, "dark")] = nights([10.0] * 60 + [2.0, 2.0])
        series[(sat, "quiet")] = nights([10.0] * 62)
    events = power_loss_events(series)
    assert [e["area"] for e in events] == ["dark"]
    event = events[0]
    assert event["corroborated"] and event["label"] == "Observed" and event["confidence"] == "high"
    assert {"time", "source", "satellites", "reasons"} <= set(event)
    assert "blackout" not in str(event).lower()
