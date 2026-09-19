"""
Daily vaccine wastage log per center - a standard cold-chain/immunization
KPI (open-vial wastage from multi-dose vials, plus occasional expired-stock
wastage). Rates are illustrative, loosely consistent with WHO-reported
typical open-vial wastage ranges for multi-dose COVID-19 vaccine
presentations (commonly cited in the 5-15% range depending on vial size
and clinic throughput) - not an official record for this or any real site.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Multi-dose vials waste more at low daily throughput (fewer people to use
# up an opened vial before end of day) - modeled as a wastage rate that
# falls as daily center throughput rises, within a realistic band.
BASE_WASTAGE_RATE = 0.09
MIN_WASTAGE_RATE = 0.03
MAX_WASTAGE_RATE = 0.22


def generate_wastage_log(daily_vax_df: pd.DataFrame, seed: int = 91) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    daily_center = (
        daily_vax_df.groupby(["date", "center_id", "center_name"])["doses_administered"]
        .sum()
        .reset_index()
        .rename(columns={"doses_administered": "doses_administered_ok"})
    )

    throughput_pctile = daily_center.groupby("center_id")["doses_administered_ok"].rank(pct=True)
    wastage_rate = np.clip(
        BASE_WASTAGE_RATE - 0.06 * throughput_pctile + rng.normal(0, 0.02, len(daily_center)),
        MIN_WASTAGE_RATE, MAX_WASTAGE_RATE,
    )
    # Occasional expired-stock write-off events (independent of daily throughput).
    expiry_event = rng.random(len(daily_center)) < 0.015
    expired_doses = np.where(expiry_event, rng.integers(5, 40, len(daily_center)), 0)

    doses_ok = daily_center["doses_administered_ok"].to_numpy()
    open_vial_wasted = np.round(doses_ok * wastage_rate / np.clip(1 - wastage_rate, 1e-6, None)).astype(int)

    out = daily_center.copy()
    out["open_vial_doses_wasted"] = open_vial_wasted
    out["expired_doses_wasted"] = expired_doses
    out["total_doses_wasted"] = out["open_vial_doses_wasted"] + out["expired_doses_wasted"]
    out["doses_drawn_from_vials"] = out["doses_administered_ok"] + out["total_doses_wasted"]
    out["wastage_rate"] = np.round(out["total_doses_wasted"] / out["doses_drawn_from_vials"].clip(lower=1), 4)
    return out.drop(columns=["doses_administered_ok"])
