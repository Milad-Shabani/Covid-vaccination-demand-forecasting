"""Common forecast-accuracy metrics used to compare ARIMA vs XGBoost."""
from __future__ import annotations

import numpy as np
import pandas as pd


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: np.ndarray, y_pred: np.ndarray, epsilon: float = 1.0) -> float:
    """Mean Absolute Percentage Error. `epsilon` guards against near-zero actuals."""
    denom = np.clip(np.abs(y_true), epsilon, None)
    return float(np.mean(np.abs((y_true - y_pred) / denom)) * 100)


def smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = (np.abs(y_true) + np.abs(y_pred)).clip(min=1e-6)
    return float(np.mean(2 * np.abs(y_pred - y_true) / denom) * 100)


def r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return float("nan")
    return float(1 - ss_res / ss_tot)


def summarize(y_true: np.ndarray, y_pred: np.ndarray, model_name: str) -> dict:
    return {
        "model": model_name,
        "MAE": round(mae(y_true, y_pred), 2),
        "RMSE": round(rmse(y_true, y_pred), 2),
        "MAPE_%": round(mape(y_true, y_pred), 2),
        "sMAPE_%": round(smape(y_true, y_pred), 2),
        "R2": round(r_squared(y_true, y_pred), 4),
    }


def metrics_table(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows).set_index("model")
