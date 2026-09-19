"""
Jalali (Solar Hijri) <-> Gregorian calendar helpers.

The project brief specifies the study window in the Iranian civil
calendar: from the 1st of Khordad 1400 through the last day of
Khordad 1401. This module resolves that into a concrete list of
Gregorian dates (used internally throughout the pipeline) while
keeping the Jalali date available as a display/reporting column,
since that is how end users of a Malard Health Network system would
actually think about the calendar.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import jdatetime

# Study window, inclusive, expressed in the Solar Hijri (Jalali) calendar.
START_JALALI = jdatetime.date(1400, 3, 1)   # 1 Khordad 1400
END_JALALI = jdatetime.date(1401, 3, 31)    # last day of Khordad 1401


@dataclass(frozen=True)
class CalendarDay:
    gregorian: date
    jalali: str          # e.g. "1400-03-01"
    jalali_year: int
    jalali_month: int
    jalali_month_name: str
    jalali_day: int


_JALALI_MONTH_NAMES = [
    "Farvardin", "Ordibehesht", "Khordad", "Tir", "Mordad", "Shahrivar",
    "Mehr", "Aban", "Azar", "Dey", "Bahman", "Esfand",
]


def build_calendar(start: jdatetime.date = START_JALALI, end: jdatetime.date = END_JALALI) -> list[CalendarDay]:
    """Return one CalendarDay per day in [start, end], inclusive."""
    days: list[CalendarDay] = []
    current = start
    while current <= end:
        g = current.togregorian()
        days.append(
            CalendarDay(
                gregorian=g,
                jalali=f"{current.year:04d}-{current.month:02d}-{current.day:02d}",
                jalali_year=current.year,
                jalali_month=current.month,
                jalali_month_name=_JALALI_MONTH_NAMES[current.month - 1],
                jalali_day=current.day,
            )
        )
        current = current + jdatetime.timedelta(days=1)
    return days


def study_window_gregorian() -> tuple[date, date]:
    days = build_calendar()
    return days[0].gregorian, days[-1].gregorian


if __name__ == "__main__":
    days = build_calendar()
    print(f"Study window: {days[0].jalali} ({days[0].gregorian}) -> {days[-1].jalali} ({days[-1].gregorian})")
    print(f"Total days: {len(days)}")
