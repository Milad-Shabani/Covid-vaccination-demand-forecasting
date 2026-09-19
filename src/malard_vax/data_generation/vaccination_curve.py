"""
Synthesizes the daily vaccination-throughput series described in the
project brief:

    * Day 1 (1 Khordad 1400 / 22 May 2021): ~500 doses/day network-wide,
      split across Sinopharm and AstraZeneca (the vaccines available
      through COVAX / early imports at that point).
    * Ramp-up through summer/autumn 1400 as import volumes increase
      and the domestically produced COVIran Barekat vaccine enters
      distribution, reaching a network peak of ~3,500 doses/day
      around Aban-Azar 1400 (Oct-Nov 2021) - consistent with Iran's
      historically documented push to accelerate coverage once the
      Delta wave subsided and before the Omicron wave arrived.
    * A secondary high-throughput plateau in Dey-Bahman 1400
      (Dec 2021-Feb 2022) driven by the booster-dose campaign that
      accompanied the Omicron wave.
    * A steady decline through spring 1401 as first/second-dose
      coverage saturates, returning to ~600 doses/day network-wide by
      the final days of the study window (Khordad 1401 / Jun 2022).

The curve is built from a handful of interpretable control points
(piecewise-linear "target" trend), then perturbed with weekly
seasonality (Fridays are the Iranian weekend - most centers run
reduced hours), autocorrelated noise, and occasional supply-shortage
dip days, before being split across the five delivery centers and
three vaccine products.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from malard_vax.data_generation.calendar_utils import CalendarDay, build_calendar
from malard_vax.data_generation.centers import VACCINE_TYPES, delivery_centers

# (day_index, target_total_daily_doses) control points over the 396-day window.
# Day 0 = 1 Khordad 1400, Day 395 = 31 Khordad 1401.
_CONTROL_POINTS = [
    (0, 500),      # 1 Khordad 1400 - slow start
    (40, 650),     # early Tir - still supply constrained
    (70, 1400),    # early Mordad - Delta wave urgency + import push begins
    (100, 2600),   # early Shahrivar - imports ramp (post Aug 2021 policy shift)
    (140, 3300),   # mid Mehr - Barekat domestic supply comes online
    (175, 3500),   # early Aban - network peak, first/second-dose catch-up campaign
    (210, 3100),   # early Azar - sustained high demand
    (230, 2400),   # early Dey - post first/second-dose peak, pre-booster lull
    (255, 3200),   # early Bahman - booster campaign rides the Omicron wave
    (280, 3350),   # early Esfand - booster campaign continues
    (305, 2500),   # early Farvardin 1401 - Nowruz holidays + declining demand
    (330, 1500),   # early Ordibehesht - coverage saturating
    (365, 900),    # early Khordad 1401 - low routine demand
    (395, 600),    # last day of window
]


def _target_trend(n_days: int) -> np.ndarray:
    xp = [p[0] for p in _CONTROL_POINTS]
    fp = [p[1] for p in _CONTROL_POINTS]
    x = np.arange(n_days)
    return np.interp(x, xp, fp)


DOSE_NUMBERS = ["1st Dose", "2nd Dose", "Booster"]


def _vaccine_mix_shares(day_index: int, n_days: int) -> dict[str, float]:
    """
    Time-varying vaccine product mix.

    Early in the window, imported Sinopharm/AstraZeneca dominate.
    COVIran Barekat's share grows steadily as domestic production
    scales up through autumn/winter 1400, becoming the majority
    product by spring 1401 - reflecting Iran's real, publicly reported
    push toward domestic vaccine self-sufficiency during this period.
    """
    t = day_index / (n_days - 1)
    barekat_share = np.clip(0.05 + 0.75 * t, 0.05, 0.80)
    remaining = 1.0 - barekat_share
    sinopharm_share = remaining * 0.55
    astrazeneca_share = remaining * 0.45
    return {
        "COVIran Barekat": barekat_share,
        "Sinopharm": sinopharm_share,
        "AstraZeneca": astrazeneca_share,
    }


def _dose_number_target_shares(day_index: int, n_days: int) -> dict[str, float]:
    """Desired dose-sequence mix before pool constraints are applied (see
    `_allocate_dose_numbers` for how this is reconciled with the running
    count of who has actually received a prior dose)."""
    t = day_index / (n_days - 1)
    first_share = np.clip(0.85 * np.exp(-3.2 * t) + 0.03, 0.03, 0.85)
    booster_share = np.clip(1.0 / (1.0 + np.exp(-11 * (t - 0.62))), 0.0, 0.85) * 0.85
    second_share = np.clip(1.0 - first_share - booster_share, 0.03, 1.0)
    total = first_share + second_share + booster_share
    return {
        "1st Dose": first_share / total,
        "2nd Dose": second_share / total,
        "Booster": booster_share / total,
    }


def _allocate_dose_numbers(daily_totals: np.ndarray) -> pd.DataFrame:
    """
    Network-level, day-by-day allocation of each day's total doses across
    1st/2nd/Booster that respects a simple two-dose-then-booster pool
    constraint: you cannot give more 2nd doses on a day than there are
    people who have had a 1st dose but not yet a 2nd, and likewise for
    boosters against the fully-vaccinated (2nd-dose-complete) pool. Any
    desired 2nd/Booster demand that the pool can't support is reallocated
    to 1st doses that day, so the daily network total is unchanged
    (preserving the campaign-shape curve tested elsewhere).
    """
    n_days = len(daily_totals)
    cum_first = cum_second = cum_booster = 0.0
    rows = np.zeros((n_days, 3))  # columns: 1st, 2nd, Booster

    for i, total in enumerate(daily_totals):
        shares = _dose_number_target_shares(i, n_days)
        desired_first = total * shares["1st Dose"]
        desired_second = total * shares["2nd Dose"]
        desired_booster = total * shares["Booster"]

        pool_for_second = max(cum_first - cum_second, 0.0)
        pool_for_booster = max(cum_second - cum_booster, 0.0)

        actual_second = min(desired_second, pool_for_second)
        actual_booster = min(desired_booster, pool_for_booster)
        leftover = (desired_second - actual_second) + (desired_booster - actual_booster)
        actual_first = desired_first + leftover  # absorb unmet 2nd/booster demand as new 1st doses

        rows[i] = [actual_first, actual_second, actual_booster]
        cum_first += actual_first
        cum_second += actual_second
        cum_booster += actual_booster

    return pd.DataFrame(rows, columns=DOSE_NUMBERS)


def generate_daily_vaccinations(
    seed: int = 42,
    shortage_day_probability: float = 0.02,
) -> pd.DataFrame:
    """
    Returns a long-format dataframe:
    date, jalali_date, center_id, center_name, vaccine_type, dose_number,
    doses_administered - plus network-level supply-center columns
    (doses_received, doses_distributed, stock_level) attached separately
    via `generate_supply_center_log`.
    """
    rng = np.random.default_rng(seed)
    calendar: list[CalendarDay] = build_calendar()
    n_days = len(calendar)

    trend = _target_trend(n_days)

    centers = delivery_centers()
    capacity_weights = centers["relative_capacity"].to_numpy()
    capacity_weights = capacity_weights / capacity_weights.sum()

    # --- Pass 1: network-level daily total + weekday/noise/shortage factors ---
    daily_totals = np.zeros(n_days)
    noise_state = 1.0
    for i, day in enumerate(calendar):
        weekday = day.gregorian.weekday()
        weekly_factor = 0.35 if weekday == 4 else (0.85 if weekday == 3 else 1.0)
        noise_state = 0.9 * noise_state + 0.1 * rng.normal(1.0, 0.10)
        day_factor = max(noise_state, 0.15)
        is_shortage_day = rng.random() < shortage_day_probability
        shortage_factor = rng.uniform(0.1, 0.35) if is_shortage_day else 1.0
        daily_totals[i] = max(trend[i] * weekly_factor * day_factor * shortage_factor, 0)

    # --- Pass 2: pool-constrained network-level dose-number split ---
    dose_split = _allocate_dose_numbers(daily_totals)

    rows = []
    for i, day in enumerate(calendar):
        total_target = daily_totals[i]

        # Split across centers with a little idiosyncratic noise per center.
        center_noise = rng.normal(1.0, 0.08, size=len(centers))
        center_shares = np.clip(capacity_weights * center_noise, 0, None)
        center_shares = center_shares / center_shares.sum()
        center_doses = np.round(total_target * center_shares).astype(int)

        mix = _vaccine_mix_shares(i, n_days)
        day_dose_shares = {
            d: (dose_split.iloc[i][d] / total_target if total_target > 0 else 1.0 / len(DOSE_NUMBERS))
            for d in DOSE_NUMBERS
        }

        for center_row, center_total in zip(centers.itertuples(index=False), center_doses):
            if center_total <= 0:
                for vtype in VACCINE_TYPES:
                    for dnum in DOSE_NUMBERS:
                        rows.append(_row(day, center_row, vtype, dnum, 0))
                continue
            vtype_noise = rng.dirichlet(
                alpha=[max(mix[v] * 40, 0.5) for v in VACCINE_TYPES]
            )
            vtype_doses = _largest_remainder_round(center_total, vtype_noise)
            for vtype, dose in zip(VACCINE_TYPES, vtype_doses):
                if dose <= 0:
                    for dnum in DOSE_NUMBERS:
                        rows.append(_row(day, center_row, vtype, dnum, 0))
                    continue
                dnum_shares = np.array([day_dose_shares[d] for d in DOSE_NUMBERS])
                dnum_shares = dnum_shares / dnum_shares.sum()
                dnum_doses = _largest_remainder_round(dose, dnum_shares)
                for dnum, d_dose in zip(DOSE_NUMBERS, dnum_doses):
                    rows.append(_row(day, center_row, vtype, dnum, d_dose))

    return pd.DataFrame(rows)


def _row(day: CalendarDay, center_row, vaccine_type: str, dose_number: str, doses: int) -> dict:
    return {
        "date": day.gregorian.isoformat(),
        "jalali_date": day.jalali,
        "center_id": center_row.center_id,
        "center_name": center_row.center_name,
        "locality": center_row.locality,
        "vaccine_type": vaccine_type,
        "dose_number": dose_number,
        "doses_administered": int(doses),
    }


def _largest_remainder_round(total: int, shares: np.ndarray) -> np.ndarray:
    """Round shares of `total` to integers that still sum to `total`."""
    raw = shares * total
    floors = np.floor(raw).astype(int)
    remainder = total - floors.sum()
    if remainder > 0:
        order = np.argsort(-(raw - floors))
        for idx in order[:remainder]:
            floors[idx] += 1
    return floors


def generate_supply_center_log(daily_vax_df: pd.DataFrame, seed: int = 7) -> pd.DataFrame:
    """
    Derives a plausible daily log for the central supply/cold-chain
    center: shipments received from the national program a few days
    ahead of demand, running stock, and doses distributed onward to
    the five delivery centers (which, in steady state, tracks total
    doses administered with a short lag).
    """
    rng = np.random.default_rng(seed)
    daily_totals = (
        daily_vax_df.groupby("date")["doses_administered"].sum().sort_index()
    )
    dates = daily_totals.index.tolist()
    demand = daily_totals.to_numpy(dtype=float)

    # Shipments arrive in lumpy batches every ~5-9 days, sized to cover
    # upcoming demand plus a safety buffer - a common cold-chain pattern
    # for a mid-sized district site.
    rows = []
    stock = float(demand[:7].mean() * 5) if len(demand) >= 7 else 2000.0
    i = 0
    n = len(dates)
    while i < n:
        batch_len = int(rng.integers(5, 10))
        window = demand[i : i + batch_len]
        upcoming_need = window.sum() if len(window) else demand[-1] * batch_len
        shipment = max(upcoming_need * rng.uniform(1.05, 1.25), 500)
        stock += shipment
        for offset in range(len(window)):
            idx = i + offset
            distributed = demand[idx]
            stock = max(stock - distributed, 0)
            rows.append(
                {
                    "date": dates[idx],
                    "doses_received": round(shipment) if offset == 0 else 0,
                    "doses_distributed": round(distributed),
                    "closing_stock": round(stock),
                }
            )
        i += batch_len

    return pd.DataFrame(rows)
