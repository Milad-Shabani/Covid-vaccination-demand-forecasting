# Data Dictionary

## Provenance summary

| Dataset | Nature | Basis |
|---|---|---|
| `vaccination_centers.csv` | Synthetic | Illustrative network of 5 delivery centers + 1 supply center, modeled after real localities in Malard County |
| `daily_vaccinations.csv` | Synthetic | Throughput curve shape (500 -> 3,500 -> 600 doses/day) specified by the project brief; day-to-day values simulated with weekly seasonality, autocorrelated noise, and shortage-day events |
| `supply_center_log.csv` | Derived | Computed from `daily_vaccinations.csv` assuming a lumpy shipment/cold-chain-stock pattern typical of a mid-sized district site |
| `daily_covid_cases.csv` | Modeled | Two epidemic bumps timed to match Iran's **documented, published** national epidemic wave timeline (see below), scaled to a plausible county population |

**None of this data should be cited as an official record.** It is a
teaching/demo dataset built for a public data-engineering & data-science
portfolio project.

### Epidemic curve calibration sources

- Fifth wave (Delta): began ~July 2021, national daily cases exceeded
  50,000 on 17 Aug 2021, deaths exceeded 700/day by 24 Aug 2021.
  ("Consecutive Waves of COVID-19 in Iran: Various Dimensions and
  Probable Causes", PMC9509792)
- Sixth wave (Omicron): first Omicron case confirmed in Iran on
  19 Dec 2021; national daily cases rose from ~700/day in early
  January 2022 to >9,000/day by 26 Jan 2022, continuing to climb into
  February 2022. (Al Jazeera, "COVID: Iran sees 'red' again as Omicron
  cases jump", 26 Jan 2022; PMC11803630)

The generator (`src/malard_vax/data_generation/epidemic_curve.py`)
places two Gaussian-shaped bumps at day-indices corresponding to these
documented peaks (mid-August 2021 and mid-February 2022), scaled to an
estimated Malard County population of ~350,000.

---

## `vaccination_centers.csv`

| Column | Type | Description |
|---|---|---|
| `center_id` | string | Unique site code (`MLD-01`...`MLD-05`, `MLD-SUP`) |
| `center_name` | string | Display name |
| `center_type` | string | `vaccination_center` or `supply_center` |
| `locality` | string | Town/area within Malard County |
| `relative_capacity` | float | Relative throughput weight used by the generator (null for the supply center) |

## `daily_vaccinations.csv`

One row per (date, center, vaccine type).

| Column | Type | Description |
|---|---|---|
| `date` | date (ISO) | Gregorian calendar date |
| `jalali_date` | string | Solar Hijri (Jalali) date, `YYYY-MM-DD` |
| `center_id` / `center_name` / `locality` | string | Joins to `vaccination_centers.csv` |
| `vaccine_type` | string | `Sinopharm`, `AstraZeneca`, or `COVIran Barekat` |
| `doses_administered` | int | Doses given that day at that center for that product |

## `supply_center_log.csv`

| Column | Type | Description |
|---|---|---|
| `date` | date | Gregorian date |
| `doses_received` | int | Doses received from the national program that day (0 on non-shipment days) |
| `doses_distributed` | int | Doses sent out to the five delivery centers (equals the network total administered that day) |
| `closing_stock` | int | End-of-day stock at the supply/cold-chain center |

## `daily_covid_cases.csv`

| Column | Type | Description |
|---|---|---|
| `date` / `jalali_date` | date/string | Calendar date |
| `new_confirmed_cases` | int | Modeled new confirmed cases that day |
| `cumulative_confirmed_cases` | int | Running total |
| `cases_per_100k_7d_avg` | float | 7-day average incidence per 100,000 population |

## Derived modeling dataset (`data/processed/daily_master_features.parquet`)

One row per calendar day (network-level), produced by
`src/malard_vax/features/build_features.py`: the vaccination total
joined with the case series and supply log, plus calendar features
(day-of-week, cyclical encodings, holiday-adjacent flags), and
lag/rolling-window features of the target and of case counts. See
that module's `FEATURE_COLUMNS` for the exact feature set used by the
XGBoost model.

---

## New in this update: operational data sources

Five additional synthetic tables were added to broaden the analytics
beyond throughput forecasting into coverage, safety, supply-chain, and
workforce/scheduling operations. All follow the same honesty convention
as the original tables: synthetic, seeded, and clearly labeled below.

### `population_by_locality_age.csv`

| Column | Type | Description |
|---|---|---|
| `center_id` / `locality` | string | Joins to `vaccination_centers.csv` |
| `age_band` | string | `12-17`, `18-59`, or `60+` |
| `eligible_population` | int | Illustrative eligible population, split from the ~350,000 county estimate by each center's `relative_capacity` and a generic national age-structure approximation. **Not a census figure.** |

### `daily_vaccinations.csv` (extended)

Now includes a **`dose_number`** column: `1st Dose`, `2nd Dose`, or
`Booster`. Allocation is pool-constrained day-by-day (see
`vaccination_curve.py::_allocate_dose_numbers`) so that cumulative 2nd
doses can never exceed cumulative 1st doses, and cumulative boosters
can never exceed cumulative 2nd doses - i.e. the coverage curves are
internally consistent, unlike a naive independent-shares split.

### `aefi_reports.csv`

One row per synthetic Adverse Event Following Immunization report.

| Column | Type | Description |
|---|---|---|
| `report_id` | string | Unique report ID |
| `date` / `center_id` / `vaccine_type` / `dose_number` | — | Context of the associated dose |
| `severity` | string | `Mild (local reaction)`, `Moderate (systemic, self-resolving)`, `Serious (medically attended)` |
| `reported_symptom` | string | Illustrative symptom for that severity band |

Rates (~18/1000 mild, ~3.5/1000 moderate, ~0.12/1000 serious) are
illustrative, loosely consistent with published COVID-19 vaccine
reactogenicity ranges - **not drawn from any real pharmacovigilance
registry.**

### `vaccine_wastage_log.csv`

| Column | Type | Description |
|---|---|---|
| `date` / `center_id` | — | — |
| `open_vial_doses_wasted` | int | Multi-dose-vial wastage, higher on low-throughput days |
| `expired_doses_wasted` | int | Occasional cold-chain expiry write-offs |
| `total_doses_wasted` | int | Sum of the above |
| `doses_drawn_from_vials` | int | Doses administered + doses wasted (the denominator for wastage rate) |
| `wastage_rate` | float | `total_doses_wasted / doses_drawn_from_vials` |

### `center_staffing_log.csv`

| Column | Type | Description |
|---|---|---|
| `date` / `center_id` | — | — |
| `vaccinators_on_duty` | int | Staff count that day (ramps up early in the campaign, dips on weekends/absences) |
| `theoretical_capacity_doses` | int | `vaccinators_on_duty x 150` doses/day |

### `appointments_log.csv`

| Column | Type | Description |
|---|---|---|
| `date` / `center_id` | — | — |
| `appointments_scheduled` | int | Appointments booked in advance for that day - a genuinely **forward-looking** signal, unlike lagged history of the target |
| `doses_via_appointment` / `doses_via_walkin` | int | Split of that day's actual doses by channel |
| `no_shows` / `no_show_rate` | int / float | Booked-but-not-attended appointments |

### Derived KPI tables (`data/processed/`)

Computed by `src/malard_vax/analytics/operational_kpis.py`:
`coverage_by_dose.csv`, `coverage_by_locality.csv`,
`wastage_summary.csv`, `staffing_utilization_summary.csv`,
`aefi_rate_summary.csv`, `appointment_performance_monthly.csv`.
