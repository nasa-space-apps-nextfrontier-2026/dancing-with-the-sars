import random

from worker.evaluation.strike_tests import Cell, Event, is_near, strike_enrichment


def make_cells(n_near, n_far, p_near, p_far, seed=1):
    rng = random.Random(seed)
    cells = []
    for i in range(n_near):      # about 0.5 km from the event
        cells.append(Cell(f"n{i}", 33.300 + rng.uniform(-0.004, 0.004), 35.400, f"D{i % 3}", rng.random() < p_near))
    for i in range(n_far):       # about 20 km away
        cells.append(Cell(f"f{i}", 33.500 + rng.uniform(-0.004, 0.004), 35.400, f"D{i % 3}", rng.random() < p_far))
    return cells


EVENTS = [Event(33.300, 35.400)]


def test_enrichment_found_when_near_cells_are_flagged_more_often():
    result = strike_enrichment(make_cells(200, 200, 0.6, 0.1), EVENTS)
    assert result["status"] == "ok"
    assert result["near_flagged_share"] > result["far_flagged_share"] + 0.3
    assert result["relative_rate"] > 3 and result["same_district_median_difference"] > 0.3


def test_no_enrichment_when_flags_are_random():
    result = strike_enrichment(make_cells(300, 300, 0.2, 0.2, seed=7), EVENTS)
    assert abs(result["difference"]) < 0.1


def test_too_few_cells_is_insufficient_not_a_number():
    result = strike_enrichment(make_cells(10, 200, 0.9, 0.1), EVENTS)
    assert result["status"] == "insufficient" and "near_flagged_share" not in result
    assert "never confirmed" in result["limits"]


def test_is_near_uses_distance_in_km():
    cell = Cell("x", 33.31, 35.40, "D", False)   # about 1.1 km
    assert is_near(cell, EVENTS, 2.0) and not is_near(cell, EVENTS, 1.0)
