import csv
import gzip
from datetime import date, timedelta

from worker.services.evaluate_nightlights import agreement, evaluate, load


def write(path, rows):
    with gzip.open(path, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "satellite", "cell", "mean_radiance", "n_pixels", "n_clear"])
        w.writerows(rows)


def series_rows(cell, values, n_pix=4, n_clear=4, sat="NOAA-20"):
    start = date(2026, 7, 1)
    return [((start + timedelta(days=i)).isoformat(), sat, cell, v, n_pix, n_clear)
            for i, v in enumerate(values)]


def test_quiet_cell_is_never_flagged_and_dark_cell_is_flagged(tmp_path):
    path = tmp_path / "h.csv.gz"
    quiet = series_rows("quiet", [10.0] * 100)
    dark = series_rows("dark", [10.0] * 98 + [2.0, 2.0])
    write(path, quiet + dark)
    result = evaluate(load(str(path)))["NOAA-20"]
    assert result["cells"] == 2
    assert result["latest_counts"] == {"no_change": 1, "possible_power_loss": 1}
    assert result["latest_flagged"][0]["cell"] == "dark"
    assert 0 < result["holdout_false_alarm_rate"] < 0.05   # only the final window of the dark cell


def test_cloudy_nights_make_cells_unknown(tmp_path):
    path = tmp_path / "h.csv.gz"
    write(path, series_rows("cloudy", [10.0] * 100, n_clear=0))
    result = evaluate(load(str(path)))["NOAA-20"]
    assert result["latest_counts"] == {"unknown": 1}
    assert result["holdout_false_alarm_rate"] is None


def test_agreement_needs_both_satellites_to_flag_the_same_date(tmp_path):
    path = tmp_path / "h.csv.gz"
    both = series_rows("c1", [10.0] * 98 + [2.0, 2.0], sat="NOAA-20") +         series_rows("c1", [10.0] * 98 + [2.0, 2.0], sat="NOAA-21")
    one = series_rows("c2", [10.0] * 98 + [2.0, 2.0], sat="NOAA-20") +         series_rows("c2", [10.0] * 100, sat="NOAA-21")
    write(path, both + one)
    result = agreement(load(str(path)))
    assert result["both_flag"] >= 1
    assert result["single_satellite_flags"] > 2 * result["both_flag"] - 1
    assert result["both_flag_rate"] < result["single_satellite_flag_rate"]
