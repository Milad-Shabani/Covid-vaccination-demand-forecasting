import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from malard_vax.models import evaluate


def test_mae_perfect_prediction_is_zero():
    y = np.array([10, 20, 30])
    assert evaluate.mae(y, y) == 0


def test_rmse_known_value():
    y_true = np.array([0, 0, 0, 0])
    y_pred = np.array([1, 1, 1, 1])
    assert evaluate.rmse(y_true, y_pred) == 1.0


def test_mape_known_value():
    y_true = np.array([100.0])
    y_pred = np.array([110.0])
    assert round(evaluate.mape(y_true, y_pred), 2) == 10.0


def test_r_squared_perfect_fit():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert evaluate.r_squared(y, y) == 1.0


def test_summarize_returns_expected_keys():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.1, 1.9, 3.2])
    result = evaluate.summarize(y_true, y_pred, "test-model")
    assert set(result.keys()) == {"model", "MAE", "RMSE", "MAPE_%", "sMAPE_%", "R2"}
    assert result["model"] == "test-model"
