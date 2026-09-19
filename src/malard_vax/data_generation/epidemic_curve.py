"""
Models daily confirmed COVID-19 cases for the Malard County catchment
area across the study window.

Methodology and honesty note
-----------------------------
A machine-readable, county-level, daily case count series for Malard
specifically is not publicly available for this period. Rather than
inventing arbitrary numbers, this generator builds a curve *anchored
to the documented national epidemic timeline for Iran*:

  * Fifth wave (Delta variant): began around July 2021, peaked in
    mid-to-late August 2021 (Iran recorded >50,000 cases/day
    nationally on 17 Aug 2021 and >700 deaths/day by 24 Aug 2021),
    receding through September-October 2021.
  * Sixth wave (Omicron variant): began in late December 2021
    (first Omicron case confirmed 19 Dec 2021), accelerated sharply
    through January 2022 (national daily cases rose from ~700/day in
    early January to >9,000/day by 26 January 2022) and peaked in
    February 2022 before declining through March 2022.

Sources: PMC11803630 (Dispersal dynamics of SARS-CoV-2 in Iran);
Al Jazeera, "COVID: Iran sees 'red' again as Omicron cases jump"
(26 Jan 2022); PMC9509792 (Consecutive Waves of COVID-19 in Iran).

The national timeline is used only to *time and shape* two epidemic
bumps (via skewed Gaussian kernels); case magnitudes are scaled down
to a plausible county population (~350,000, in line with published
Iranian census figures for Malard County) using an illustrative
attack-rate assumption. Treat the resulting series as a realistic
teaching/demo dataset, not an official statistic.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from malard_vax.data_generation.calendar_utils import CalendarDay, build_calendar

MALARD_APPROX_POPULATION = 350_000


def _gaussian_bump(x: np.ndarray, center: float, width: float, height: float) -> np.ndarray:
    return height * np.exp(-0.5 * ((x - center) / width) ** 2)


def generate_daily_cases(seed: int = 123) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    calendar: list[CalendarDay] = build_calendar()
    n_days = len(calendar)
    x = np.arange(n_days)

    # Day-index anchors (day 0 = 22 May 2021):
    #   Delta peak ~ mid-August 2021  -> ~day 85
    #   Omicron peak ~ mid-February 2022 -> ~day 270
    delta_bump = _gaussian_bump(x, center=85, width=22, height=145)
    omicron_bump = _gaussian_bump(x, center=272, width=18, height=210)
    # A mild residual bump in late spring 1401 (BA.2-driven upticks were
    # observed in several countries around Apr-May 2022).
    spring_bump = _gaussian_bump(x, center=350, width=15, height=35)

    baseline = 4.0 + 2.5 * np.sin(2 * np.pi * x / 365.0 + np.pi)  # mild seasonal baseline
    expected = np.clip(baseline + delta_bump + omicron_bump + spring_bump, 0.5, None)

    # Weekday reporting effect: fewer tests processed/reported on Fridays.
    weekday_factor = np.array([1.0, 1.0, 1.0, 0.95, 0.9, 0.55, 0.85])  # Mon..Sun
    weekdays = np.array([d.gregorian.weekday() for d in calendar])
    expected = expected * weekday_factor[weekdays]

    new_cases = rng.poisson(lam=expected)

    df = pd.DataFrame(
        {
            "date": [d.gregorian.isoformat() for d in calendar],
            "jalali_date": [d.jalali for d in calendar],
            "new_confirmed_cases": new_cases,
        }
    )
    df["cumulative_confirmed_cases"] = df["new_confirmed_cases"].cumsum()
    df["cases_per_100k_7d_avg"] = (
        df["new_confirmed_cases"].rolling(7, min_periods=1).mean() / MALARD_APPROX_POPULATION * 100_000
    )
    return df
