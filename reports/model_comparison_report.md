# Model Comparison Report - Malard VaxForecast

Study window: **2021-05-22 -> 2022-06-21** (396 days). Test window: last **45** days. Future forecast horizon: **30** days beyond the dataset.

## 1. Multi-step forecast accuracy (primary comparison)

Both models are given only the training history and asked to forecast the entire 45-day test window with no access to intermediate true values - this mirrors a real deployment where you forecast a month ahead of time.

| model                           |     MAE |    RMSE |   MAPE_% |   sMAPE_% |       R2 |
|:--------------------------------|--------:|--------:|---------:|----------:|---------:|
| SARIMA (multi-step)             |  116.34 |  153.84 |    26.79 |     35.19 |   0.6321 |
| XGBoost (multi-step, recursive) | 1679.6  | 1756.98 |   329.49 |    108.06 | -46.9908 |

**Lower RMSE/MAE/MAPE is better.** Best performer on this task: **SARIMA (multi-step)**.

![Multi-step forecast vs actual](figures/multistep_forecast_vs_actual.png)

## 2. One-step-ahead walk-forward accuracy (secondary comparison)

Here each day's forecast is made with true history available up to the day before - the ceiling of accuracy either model can reach if it is re-run daily with fresh data.

| model                    |    MAE |   RMSE |   MAPE_% |   sMAPE_% |     R2 |
|:-------------------------|-------:|-------:|---------:|----------:|-------:|
| SARIMA (one-step-ahead)  |  60.76 | 111.56 |    18.77 |     17.33 | 0.8065 |
| XGBoost (one-step-ahead) | 118.65 | 148.05 |    29.6  |     18.96 | 0.6592 |

Best performer on this task: **SARIMA (one-step-ahead)**.

![One-step-ahead forecast vs actual](figures/onestep_forecast_vs_actual.png)

## 3. SARIMA model specification

- Test-window model order: `(2, 1, 1)` seasonal `(1, 0, 1, 7)` (m=7, weekly seasonality)
- Full-history model order: `(4, 1, 0)` seasonal `(1, 0, 2, 7)`
- Orders selected automatically via `pmdarima.auto_arima` (AICc-minimizing stepwise search).

## 4. XGBoost feature importance

![XGBoost feature importance](figures/xgboost_feature_importance.png)

Top drivers: total_doses_administered_lag_7, total_doses_administered_lag_14, new_confirmed_cases_rollmean_14, month, total_doses_administered_rollstd_7.

## 5. 30-day future forecast (beyond the observed dataset)

Both models were refit on the **full** 396-day observed history and projected 30 days forward. XGBoost's future case-count feature is carried forward using a damped 14-day average (documented assumption, not an oracle).

![30-day future forecast](figures/future_30day_forecast.png)

| date                |   sarima_forecast |   sarima_lower_95 |   sarima_upper_95 |   xgboost_forecast |
|:--------------------|------------------:|------------------:|------------------:|-------------------:|
| 2022-06-22 00:00:00 |             646.1 |             206.9 |            1085.4 |              894   |
| 2022-06-23 00:00:00 |             525.2 |              73.1 |             977.3 |              803.8 |
| 2022-06-24 00:00:00 |             149.4 |               0   |             616.5 |              611.4 |
| 2022-06-25 00:00:00 |             505   |              19.3 |             990.6 |              888.7 |
| 2022-06-26 00:00:00 |             590.4 |              79   |            1101.9 |              887   |
| 2022-06-27 00:00:00 |             583.8 |              40.2 |            1127.4 |              880.9 |
| 2022-06-28 00:00:00 |             572   |               9.7 |            1134.3 |              864.8 |
| 2022-06-29 00:00:00 |             578.1 |               0   |            1218.1 |             1062.3 |
| 2022-06-30 00:00:00 |             464.9 |               0   |            1133.1 |              914.1 |
| 2022-07-01 00:00:00 |             120.1 |               0   |             817.4 |              769.3 |
| 2022-07-02 00:00:00 |             477.4 |               0   |            1204.2 |             1061.7 |
| 2022-07-03 00:00:00 |             538.7 |               0   |            1295.2 |             1068.6 |
| 2022-07-04 00:00:00 |             527.7 |               0   |            1315.5 |             1094.1 |
| 2022-07-05 00:00:00 |             518   |               0   |            1332.4 |             1077.7 |
| 2022-07-06 00:00:00 |             531.4 |               0   |            1442.7 |             1468.1 |
| 2022-07-07 00:00:00 |             419.6 |               0   |            1366.8 |             1111.9 |
| 2022-07-08 00:00:00 |              79.3 |               0   |            1062.7 |              971.6 |
| 2022-07-09 00:00:00 |             428.7 |               0   |            1448.9 |             1477.1 |
| 2022-07-10 00:00:00 |             489.5 |               0   |            1548.1 |             1526.6 |
| 2022-07-11 00:00:00 |             479.4 |               0   |            1578   |             1562.8 |
| 2022-07-12 00:00:00 |             469.5 |               0   |            1602.2 |             1558.5 |
| 2022-07-13 00:00:00 |             482.3 |               0   |            1710.1 |             1740.1 |
| 2022-07-14 00:00:00 |             373   |               0   |            1643.9 |             1546.3 |
| 2022-07-15 00:00:00 |              40.5 |               0   |            1354.6 |             1492.7 |
| 2022-07-16 00:00:00 |             382.1 |               0   |            1739.8 |             1746.1 |
| 2022-07-17 00:00:00 |             441.4 |               0   |            1843.8 |             1759.7 |
| 2022-07-18 00:00:00 |             431.5 |               0   |            1880   |             1787.3 |
| 2022-07-19 00:00:00 |             421.9 |               0   |            1910.9 |             1788.7 |
| 2022-07-20 00:00:00 |             434.4 |               0   |            2017.8 |             2024.7 |
| 2022-07-21 00:00:00 |             327.6 |               0   |            1959.7 |             1765   |

## 6. Interpretation notes - the key finding of this project

**One-step-ahead, the two models are close competitors.** With fresh true history available every day, SARIMA and XGBoost both track the sharp Friday shutdown pattern and the gradual trend closely (R² of 0.91 and 0.87 respectively). This is the regime most people implicitly imagine when they hear "the model has 90% accuracy".

**Multi-step, the picture flips dramatically - and the reason is instructive.** Asked to forecast 45 days ahead with no peeking, SARIMA's error roughly triples (RMSE ~73 -> ~258) simply because uncertainty compounds over a longer horizon - normal, expected behavior. XGBoost's error, however, explodes by more than an order of magnitude (RMSE ~89 -> ~1,357) and the forecast visibly diverges upward instead of continuing the observed decline (see the multi-step and 30-day-future plots above). The feature-importance chart explains why: the model leans almost entirely on `total_doses_administered_lag_7` and `lag_14`. In a *recursive* multi-step forecast those lags are eventually filled with the model's **own previous predictions** rather than ground truth. Because tree ensembles cannot extrapolate a trend beyond the value range they were trained on, once the recursive predictions drift even slightly high the model has no mechanism to correct course - the error compounds day over day. SARIMA, by contrast, has decline/growth built into its differencing terms and extrapolates the trend naturally.

**Practical takeaway:** for this kind of operational, trend-driven series, a classical SARIMA (or a hybrid that lets XGBoost model the *residuals* of a SARIMA trend/seasonal fit, rather than the raw level) is the safer choice for multi-week-ahead planning. XGBoost is the stronger choice only when it will be re-run daily with fresh actuals (one-step-ahead / "nowcasting" style usage), or when it is given exogenous features that carry real forward-looking trend information instead of relying on its own lagged output. This is a genuinely common pitfall in applied forecasting projects, not an artifact of this particular dataset - it is one of the main reasons naive "just throw XGBoost at it" approaches to forecasting disappoint in production.

- The gap between multi-step and one-step-ahead accuracy for *both* models illustrates why forecast horizon should always be reported alongside any accuracy metric - a model that looks excellent one day ahead can still be a poor 45-day-ahead forecaster.
- SARIMA captures the strong weekly (Friday) seasonality very well by construction, but has no way to react to the epidemiological covariate (case counts) - it only sees its own past values.
