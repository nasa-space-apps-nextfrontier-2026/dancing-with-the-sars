from worker.services.nightlights import Night, assess, baseline


def nights(values, clear=True, start=1):
    return [Night(f"2026-09-{start + i:02d}", v, clear) for i, v in enumerate(values)]


def test_flat_series_is_no_change():
    result = assess(nights([10.0] * 60), nights([9.5, 10.2], start=1))
    assert result.status == "no_change"


def test_two_clear_dark_nights_flag_possible_power_loss():
    result = assess(nights([10.0] * 60), nights([2.0, 2.0]))
    assert result.status == "possible_power_loss"
    assert result.confidence == "high" and result.ratio < 0.5


def test_one_clear_night_is_unknown_not_a_guess():
    recent = nights([2.0, 2.0])
    recent[0] = Night(recent[0].date, 2.0, False)
    result = assess(nights([10.0] * 60), recent)
    assert result.status == "unknown" and "clear recent" in result.reason


def test_too_few_baseline_nights_is_unknown():
    result = assess(nights([10.0] * 10), nights([1.0, 1.0]))
    assert result.status == "unknown" and result.baseline_nights == 10


def test_dark_baseline_is_unknown():
    assert assess(nights([0.1] * 60), nights([0.0, 0.0])).status == "unknown"


def test_cloudy_and_missing_nights_do_not_count_in_baseline():
    history = nights([10.0] * 40) + [Night("x", None, True), Night("y", 99.0, False)]
    value, used = baseline(history)
    assert value == 10.0 and used == 40


def test_three_nights_one_dip_is_not_flagged():
    assert assess(nights([10.0] * 60), nights([2.0, 9.0])).status == "no_change"
