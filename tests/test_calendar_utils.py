import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from datetime import date

from malard_vax.data_generation.calendar_utils import build_calendar, study_window_gregorian


def test_study_window_length_is_396_days():
    days = build_calendar()
    assert len(days) == 396


def test_first_day_matches_1_khordad_1400():
    days = build_calendar()
    assert days[0].jalali == "1400-03-01"
    assert days[0].gregorian == date(2021, 5, 22)


def test_last_day_matches_end_of_khordad_1401():
    days = build_calendar()
    assert days[-1].jalali == "1401-03-31"
    assert days[-1].gregorian == date(2022, 6, 21)


def test_days_are_strictly_increasing_and_contiguous():
    days = build_calendar()
    for prev, cur in zip(days, days[1:]):
        assert (cur.gregorian - prev.gregorian).days == 1


def test_study_window_gregorian_matches_first_and_last():
    days = build_calendar()
    start, end = study_window_gregorian()
    assert start == days[0].gregorian
    assert end == days[-1].gregorian
