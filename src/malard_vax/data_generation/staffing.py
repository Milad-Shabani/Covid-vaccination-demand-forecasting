"""
Daily staffing log per vaccination center: vaccinators on duty and the
resulting theoretical daily capacity (doses per staffed vaccinator per
day is held roughly constant per center, so capacity utilization =
doses administered / theoretical capacity - a real operational KPI
health-network managers track for workforce planning).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from malard_vax.data_generation.calendar_utils import build_calendar
from malard_vax.data_generation.centers import delivery_centers

# Baseline vaccinators per center at "normal" staffing, roughly proportional
# to relative_capacity, and each vaccinator can administer ~120 doses/day
# in a well-run clinic session.
DOSES_PER_VACCINATOR_PER_DAY = 150
BASE_STAFF_BY_CAPACITY = 5.5  # baseline staff count for relative_capacity == 1.0


def generate_staffing_log(seed: int = 17) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    calendar = build_calendar()
    centers = delivery_centers()

    rows = []
    for _, center in centers.iterrows():
        base_staff = max(round(BASE_STAFF_BY_CAPACITY * center["relative_capacity"]), 2)
        # Slow staffing ramp-up over the first ~10 weeks as the campaign scales.
        for i, day in enumerate(calendar):
            weekday = day.gregorian.weekday()
            ramp = min(1.0, 0.4 + i / 70)
            weekend_reduction = 0.4 if weekday == 4 else (0.75 if weekday == 3 else 1.0)
            absence_shock = 1.0 if rng.random() > 0.05 else rng.uniform(0.5, 0.85)
            staff_on_duty = max(
                round(base_staff * ramp * weekend_reduction * absence_shock), 1
            )
            rows.append({
                "date": day.gregorian.isoformat(),
                "center_id": center["center_id"],
                "center_name": center["center_name"],
                "vaccinators_on_duty": int(staff_on_duty),
                "theoretical_capacity_doses": int(staff_on_duty * DOSES_PER_VACCINATOR_PER_DAY),
            })
    return pd.DataFrame(rows)
