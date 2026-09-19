"""
Gradient-boosted trees (XGBoost) forecaster for the daily total-doses
series, using the engineered calendar/lag/rolling feature set from
`malard_vax.features.build_features`.

Two forecasting regimes are supported:

* Backtest evaluation: for each day in the held-out test window we
  use the *true* history up to (but not including) that day to build
  lag/rolling features - a standard one-step-ahead evaluation that
  answers "how good is the model when it always has fresh history?".
* Future (recursive/multi-step) forecasting: beyond the end of the
  observed dataset there is no true history, so predictions are fed
  back in as if they were observations to compute next-day lag
  features. This is what a real "predict the next N days" deployment
  would have to do, and it is reported separately because error
  compounds over the horizon.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import xgboost as xgb

from malard_vax.features.build_features import (
    FEATURE_COLUMNS,
    TARGET_COL,
    add_calendar_features,
    add_lag_and_rolling_features,
)

DEFAULT_PARAMS = dict(
    n_estimators=400,
    max_depth=4,
    learning_rate=0.03,
    subsample=0.85,
    colsample_bytree=0.85,
    reg_lambda=1.5,
    random_state=42,
    objective="reg:squarederror",
)


@dataclass
class XGBTrainResult:
    model: xgb.XGBRegressor
    feature_importances: pd.Series


def train_xgboost(train_df: pd.DataFrame, params: dict | None = None) -> XGBTrainResult:
    params = {**DEFAULT_PARAMS, **(params or {})}
    model = xgb.XGBRegressor(**params)
    clean = train_df.dropna(subset=FEATURE_COLUMNS)
    X = clean[FEATURE_COLUMNS]
    y = clean[TARGET_COL]
    model.fit(X, y)
    importances = pd.Series(model.feature_importances_, index=FEATURE_COLUMNS).sort_values(ascending=False)
    return XGBTrainResult(model=model, feature_importances=importances)


def predict_one_step_ahead(model: xgb.XGBRegressor, feature_df: pd.DataFrame) -> np.ndarray:
    """Backtest-style prediction: features already contain true-history lags."""
    X = feature_df[FEATURE_COLUMNS]
    preds = model.predict(X)
    return np.clip(preds, 0, None)


def recursive_future_forecast(
    model: xgb.XGBRegressor,
    history_df: pd.DataFrame,
    n_future: int,
    future_case_assumption: str = "seasonal_decay",
) -> pd.DataFrame:
    """
    Roll the model forward day-by-day beyond the observed dataset.

    `history_df` must be the *raw* (pre-feature-engineering) daily
    dataset (date, total_doses_administered, new_confirmed_cases, ...)
    covering the full observed period. Future `new_confirmed_cases`
    values (needed as a feature) are not known, so we carry forward a
    damped version of the recent 14-day average case count - a
    reasonable, clearly-documented assumption rather than an oracle.
    """
    working = history_df.copy()
    last_date = working["date"].max()
    recent_case_level = working["new_confirmed_cases"].tail(14).mean()

    future_rows = []
    for step in range(1, n_future + 1):
        next_date = last_date + pd.Timedelta(days=step)
        if future_case_assumption == "seasonal_decay":
            assumed_cases = max(recent_case_level * (0.985 ** step), 1.0)
        else:
            assumed_cases = recent_case_level

        new_row = {
            "date": next_date,
            TARGET_COL: np.nan,
            "new_confirmed_cases": assumed_cases,
            "cumulative_confirmed_cases": working["cumulative_confirmed_cases"].iloc[-1] + assumed_cases,
            "cases_per_100k_7d_avg": working["cases_per_100k_7d_avg"].iloc[-1],
            "doses_received": 0,
            "doses_distributed": 0,
            "closing_stock": working["closing_stock"].iloc[-1] if "closing_stock" in working else np.nan,
        }
        working = pd.concat([working, pd.DataFrame([new_row])], ignore_index=True)

        featured = add_calendar_features(working)
        featured = add_lag_and_rolling_features(featured)
        last_feature_row = featured.iloc[[-1]][FEATURE_COLUMNS]

        pred = float(model.predict(last_feature_row)[0])
        pred = max(pred, 0)
        working.loc[working.index[-1], TARGET_COL] = pred

        future_rows.append({"date": next_date, "predicted_doses": pred, "assumed_new_cases": assumed_cases})

    return pd.DataFrame(future_rows)
