"""
Daily appointment-booking log per center.

Splits each day's actual doses administered into the pre-booked
("appointment") and walk-in channels, and derives how many appointments
must have been *scheduled* in advance to net out to the observed
appointment-channel doses after accounting for no-shows.

Unlike the lagged/rolling features already used by the forecasting
models, `appointments_scheduled` is a genuinely forward-looking signal
in a real clinic scheduling system (appointments are booked days ahead
of the visit date) - see the "possible extensions" note in the README
about giving XGBoost real forward-looking exogenous features instead of
only lagged history of the target itself.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def generate_appointments_log(daily_vax_df: pd.DataFrame, seed: int = 63) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    daily_center = (
        daily_vax_df.groupby(["date", "center_id", "center_name"])["doses_administered"]
        .sum()
        .reset_index()
    )
    n = len(daily_center)
    dates = pd.to_datetime(daily_center["date"])
    day_index = (dates - dates.min()).dt.days.to_numpy()
    n_days = max(day_index.max(), 1)

    # Appointment-booking systems matured over the campaign: walk-in-heavy
    # at launch, increasingly appointment-driven as centers scaled up.
    appointment_share = np.clip(0.35 + 0.45 * (day_index / n_days) + rng.normal(0, 0.05, n), 0.2, 0.92)
    weekday = dates.dt.weekday.to_numpy()
    # No-show rates run a little higher right before the weekend (Thursday).
    base_noshow = np.where(weekday == 3, 0.16, 0.11)
    no_show_rate = np.clip(base_noshow + rng.normal(0, 0.03, n), 0.03, 0.35)

    doses = daily_center["doses_administered"].to_numpy()
    doses_via_appointment = np.round(doses * appointment_share).astype(int)
    doses_via_walkin = doses - doses_via_appointment

    appointments_scheduled = np.round(doses_via_appointment / np.clip(1 - no_show_rate, 1e-6, None)).astype(int)
    no_shows = np.clip(appointments_scheduled - doses_via_appointment, 0, None)

    out = daily_center.copy()
    out["appointments_scheduled"] = appointments_scheduled
    out["doses_via_appointment"] = doses_via_appointment
    out["doses_via_walkin"] = doses_via_walkin
    out["no_shows"] = no_shows
    out["no_show_rate"] = np.round(no_shows / np.clip(appointments_scheduled, 1, None), 4)
    return out.rename(columns={"doses_administered": "total_doses_administered"})
