"""
Builds the network-level daily modeling dataset used by both the
ARIMA and XGBoost forecasters: one row per day, with the forecast
target (`total_doses_administered`) plus calendar, epidemiological,
and lagged/rolling features.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

TARGET_COL = "total_doses_administered"


def load_master_dataset(raw_dir: Path) -> pd.DataFrame:
    vax = pd.read_csv(raw_dir / "daily_vaccinations.csv", parse_dates=["date"])
    cases = pd.read_csv(raw_dir / "daily_covid_cases.csv", parse_dates=["date"])
    supply = pd.read_csv(raw_dir / "supply_center_log.csv", parse_dates=["date"])

    daily_vax = (
        vax.groupby("date", as_index=False)["doses_administered"]
        .sum()
        .rename(columns={"doses_administered": TARGET_COL})
    )

    df = daily_vax.merge(cases, on="date", how="left").merge(supply, on="date", how="left")
    df = df.sort_values("date").reset_index(drop=True)
    return df


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["day_index"] = np.arange(len(df))
    df["day_of_week"] = df["date"].dt.dayofweek  # Monday=0
    df["is_weekend"] = (df["day_of_week"] == 4).astype(int)  # Friday
    df["is_short_day"] = (df["day_of_week"] == 3).astype(int)  # Thursday
    df["month"] = df["date"].dt.month
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    for k in range(1, 4):
        df[f"dow_sin_{k}"] = np.sin(2 * np.pi * k * df["day_of_week"] / 7)
        df[f"dow_cos_{k}"] = np.cos(2 * np.pi * k * df["day_of_week"] / 7)
    df["annual_sin"] = np.sin(2 * np.pi * df["day_index"] / 365.25)
    df["annual_cos"] = np.cos(2 * np.pi * df["day_index"] / 365.25)
    return df


def add_lag_and_rolling_features(df: pd.DataFrame, target_col: str = TARGET_COL) -> pd.DataFrame:
    df = df.copy()
    for lag in [1, 2, 3, 7, 14]:
        df[f"{target_col}_lag_{lag}"] = df[target_col].shift(lag)
    for window in [7, 14, 28]:
        df[f"{target_col}_rollmean_{window}"] = (
            df[target_col].shift(1).rolling(window, min_periods=1).mean()
        )
        df[f"{target_col}_rollstd_{window}"] = (
            df[target_col].shift(1).rolling(window, min_periods=2).std()
        )
    df[f"{target_col}_diff_1"] = df[target_col].diff(1)
    df[f"{target_col}_diff_7"] = df[target_col].diff(7)

    # Epidemiological signal, lagged (cases reported today reflect
    # infections from days prior; also cases can proxy demand shifts
    # for booster doses a few weeks later).
    df["new_confirmed_cases_lag_7"] = df["new_confirmed_cases"].shift(7)
    df["new_confirmed_cases_rollmean_14"] = (
        df["new_confirmed_cases"].shift(1).rolling(14, min_periods=1).mean()
    )
    return df


def build_feature_dataset(raw_dir: Path) -> pd.DataFrame:
    df = load_master_dataset(raw_dir)
    df = add_calendar_features(df)
    df = add_lag_and_rolling_features(df)
    return df


FEATURE_COLUMNS = [
    "day_index",
    "day_of_week",
    "is_weekend",
    "is_short_day",
    "month",
    "week_of_year",
    "dow_sin_1", "dow_cos_1", "dow_sin_2", "dow_cos_2", "dow_sin_3", "dow_cos_3",
    "annual_sin", "annual_cos",
    f"{TARGET_COL}_lag_1", f"{TARGET_COL}_lag_2", f"{TARGET_COL}_lag_3",
    f"{TARGET_COL}_lag_7", f"{TARGET_COL}_lag_14",
    f"{TARGET_COL}_rollmean_7", f"{TARGET_COL}_rollmean_14", f"{TARGET_COL}_rollmean_28",
    f"{TARGET_COL}_rollstd_7", f"{TARGET_COL}_rollstd_14", f"{TARGET_COL}_rollstd_28",
    f"{TARGET_COL}_diff_1", f"{TARGET_COL}_diff_7",
    "new_confirmed_cases", "new_confirmed_cases_lag_7", "new_confirmed_cases_rollmean_14",
]
