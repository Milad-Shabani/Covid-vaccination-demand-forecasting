# Methodology

## 1. Data generation

The synthetic dataset is built from a small number of interpretable
control points rather than pure random noise, so that it reproduces
the operational pattern described in the project brief:

- **Vaccination throughput** (`vaccination_curve.py`): a piecewise-linear
  target trend (500 -> 3,500 -> 600 doses/day) is perturbed with
  (a) weekly seasonality - Friday is the Iranian weekend, so throughput
  drops sharply; Thursday is a shorter working day - (b) AR(1)-style
  autocorrelated noise so nearby days move together, and (c) occasional
  low-probability "shortage days". The network total is then split
  across the five delivery centers proportional to a fixed relative
  capacity (with idiosyncratic daily noise per center), and across the
  three vaccine products using a time-varying mix that shifts toward
  the domestically produced COVIran Barekat vaccine over the course of
  the window - mirroring Iran's real, published push for vaccine
  self-sufficiency during this period.

- **Case counts** (`epidemic_curve.py`): rather than inventing an
  arbitrary curve, two Gaussian bumps are placed at day-indices that
  correspond to the *documented* national epidemic wave peaks for Iran
  (Delta wave, mid-August 2021; Omicron wave, mid-February 2022), then
  scaled to a plausible county population and perturbed with Poisson
  noise and a weekday reporting effect. See `docs/data_dictionary.md`
  for sources.

Both generators are seeded (`numpy.random.default_rng(seed)`), so the
dataset is exactly reproducible from `scripts/generate_sample_data.py`.

## 2. Feature engineering

`src/malard_vax/features/build_features.py` aggregates the per-center
data to a network-level daily series and builds:

- Calendar features: day-of-week, weekend/short-day flags, month,
  ISO week, and cyclical (sine/cosine) encodings of weekday and
  day-of-year.
- Lag features of the target at 1, 2, 3, 7, and 14 days.
- Rolling mean/std of the target over 7/14/28-day windows.
- 1-day and 7-day differences of the target.
- The case-count series itself, its 7-day lag, and its 14-day rolling
  mean, as an epidemiological covariate.

## 3. Modeling

Two forecasting approaches are compared, deliberately evaluated under
**two different task definitions** because they tell very different
stories (see the generated `reports/model_comparison_report.md` for
full results and discussion):

- **SARIMA** (`pmdarima.auto_arima`, seasonal period = 7): a classical
  statistical baseline that models the target purely from its own
  past values and residual structure. Orders are chosen automatically
  by AICc-minimizing stepwise search rather than hand-picked, so the
  result is reproducible from data alone.
- **XGBoost** (`xgboost.XGBRegressor`): a gradient-boosted tree
  ensemble trained on the engineered feature set above.

### Task 1 - Multi-step ("no peeking") forecast
Both models are fit on the training portion only and asked to
forecast the entire held-out test window (default: 45 days) without
seeing any true values in between. For XGBoost this means a
**recursive** forecast: each day's prediction is fed back in to
compute the next day's lag/rolling features, since no ground truth is
available. This is the realistic task for "plan procurement for the
next month."

### Task 2 - One-step-ahead walk-forward forecast
Each day's forecast is made using true history up to (but not
including) that day - i.e. the model is conceptually "re-run every
morning with yesterday's real number in hand." This measures each
model's best-case accuracy and is useful for near-term
("nowcasting") operational decisions.

### Task 3 - Future forecast beyond the observed dataset
Both models are refit on the full observed history and asked to
project 30 days past the end of the dataset. XGBoost's future
case-count feature (which it cannot observe) is filled in with a
damped extrapolation of the recent 14-day average - a documented
assumption, not an oracle peek at the future.

## 4. Evaluation metrics

MAE, RMSE, MAPE, sMAPE, and R² are reported for every task/model
combination (`src/malard_vax/models/evaluate.py`). MAPE uses a floor
of 1.0 on the denominator to avoid division blow-ups on near-zero
actual values (which occur on Fridays).

## 5. Key finding

The two task definitions produce a striking split: SARIMA and XGBoost
are close competitors one-step-ahead, but XGBoost's recursive
multi-step forecast diverges sharply because it depends heavily on
lagged values of its own target, and tree ensembles cannot extrapolate
a trend beyond the value range seen in training. See section 6 of
`reports/model_comparison_report.md` for the full discussion and its
practical implications for model selection in production forecasting
systems.

## 6. Operational analytics extensions (this update)

Beyond throughput forecasting, five additional data sources feed a
broader operations picture (see `docs/data_dictionary.md` for full
schemas):

- **Dose-sequence coverage**: `vaccination_curve.py::_allocate_dose_numbers`
  splits each day's total doses across 1st/2nd/Booster using a
  **pool-constrained sequential allocator** - target shares shift over
  time (mostly 1st doses at launch, 2nd-dose catch-up around the Aban
  peak, booster-dominated from the Dey/Esfand campaign onward), but any
  day's desired 2nd-dose or booster volume is capped by how many people
  are actually eligible so far (i.e., have had a prior dose but not the
  next one yet); unmet demand is reallocated to 1st doses so the daily
  network total is unchanged. This guarantees cumulative 2nd-dose
  coverage never exceeds cumulative 1st-dose coverage, and booster
  coverage never exceeds 2nd-dose coverage - checked directly in
  `tests/test_new_data_sources.py`.
- **Coverage %**: `src/malard_vax/analytics/operational_kpis.py` divides
  cumulative doses of each dose_number by the eligible population from
  `population_by_locality_age.csv` - a standard simplification when only
  aggregate dose counts (not a person-level registry) are available.
- **AEFI, wastage, staffing, and appointments** are generated
  independently (each with its own seed) from the vaccination and
  staffing series and summarized into rate/utilization KPIs. Staffing
  capacity (vaccinators x 150 doses/day) was calibrated so average
  utilization sits in a realistic ~55-70% band rather than saturating
  at or above 100%.
- **Appointments as a forward-looking feature**: `appointments_scheduled`
  is booked in advance of the visit date, unlike every other feature in
  `build_features.py` (which are lagged/rolling views of the past). It
  is not yet wired into the XGBoost feature set - see "Possible
  extensions" in the README for how it could reduce the multi-step
  recursive-forecast error documented in Section 5.

