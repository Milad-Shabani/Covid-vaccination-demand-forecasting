"""
SARIMA baseline for the daily total-doses series.

We let `pmdarima.auto_arima` search the (p,d,q)(P,D,Q)_7 space (weekly
seasonality is the dominant, visually obvious pattern - centers run
near-zero on Fridays). auto_arima selects orders by AICc so the
search is reproducible and doesn't require manual ACF/PACF reading,
while still being a genuine statistical time-series model (not a
black box) - useful as the classical baseline against which the
gradient-boosted model is judged.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pmdarima as pm


def fit_arima(train_series: pd.Series, seasonal_period: int = 7) -> pm.arima.ARIMA:
    return pm.auto_arima(
        train_series,
        seasonal=True,
        m=seasonal_period,
        stepwise=True,
        suppress_warnings=True,
        error_action="ignore",
        max_p=4, max_q=4, max_P=2, max_Q=2,
        trace=False,
    )


def forecast(model: pm.arima.ARIMA, n_periods: int) -> tuple[np.ndarray, np.ndarray]:
    preds, conf_int = model.predict(n_periods=n_periods, return_conf_int=True)
    return np.clip(np.asarray(preds), 0, None), np.asarray(conf_int)
