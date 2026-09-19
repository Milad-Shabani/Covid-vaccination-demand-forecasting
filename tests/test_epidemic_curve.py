import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from malard_vax.data_generation.epidemic_curve import generate_daily_cases


def test_columns_and_length():
    df = generate_daily_cases(seed=1)
    assert len(df) == 396
    assert {"date", "new_confirmed_cases", "cumulative_confirmed_cases"}.issubset(df.columns)


def test_cases_are_non_negative():
    df = generate_daily_cases(seed=1)
    assert (df["new_confirmed_cases"] >= 0).all()


def test_cumulative_is_monotonic_non_decreasing():
    df = generate_daily_cases(seed=1)
    assert (df["cumulative_confirmed_cases"].diff().dropna() >= 0).all()


def test_delta_wave_peak_falls_in_expected_window():
    """
    National fifth-wave (Delta) peak is documented as mid-to-late Aug 2021.
    Day 0 = 2021-05-22, so mid-August 2021 is around day ~85.
    """
    df = generate_daily_cases(seed=1)
    df["date"] = pd.to_datetime(df["date"])
    window = df[(df["date"] >= "2021-07-15") & (df["date"] <= "2021-09-30")]
    peak_day = window.loc[window["new_confirmed_cases"].idxmax(), "date"]
    assert pd.Timestamp("2021-08-01") <= peak_day <= pd.Timestamp("2021-09-15")


def test_omicron_wave_peak_falls_in_expected_window():
    df = generate_daily_cases(seed=1)
    df["date"] = pd.to_datetime(df["date"])
    window = df[(df["date"] >= "2022-01-01") & (df["date"] <= "2022-03-15")]
    peak_day = window.loc[window["new_confirmed_cases"].idxmax(), "date"]
    assert pd.Timestamp("2022-01-15") <= peak_day <= pd.Timestamp("2022-03-01")
