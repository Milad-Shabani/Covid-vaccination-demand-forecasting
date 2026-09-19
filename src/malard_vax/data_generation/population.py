"""
Eligible-population reference table used to convert cumulative doses
into coverage percentages by locality and age band.

Population figures are illustrative, scaled from the ~350,000
Malard County population estimate already used in
`epidemic_curve.py`, split across the five center localities in
proportion to each center's `relative_capacity` (a reasonable proxy
for catchment size), and further split across three broad eligibility
age bands using a generic Iranian age-structure approximation. These
are NOT official census figures - see docs/data_dictionary.md.
"""
from __future__ import annotations

import pandas as pd

from malard_vax.data_generation.centers import delivery_centers
from malard_vax.data_generation.epidemic_curve import MALARD_APPROX_POPULATION

# Generic age-structure shares (illustrative, approximating national census patterns).
AGE_BAND_SHARES = {
    "12-17": 0.09,
    "18-59": 0.66,
    "60+": 0.14,
    # remaining ~11% is under-12 / not yet vaccine-eligible for most of the window
}


def population_by_locality_age() -> pd.DataFrame:
    centers = delivery_centers()[["center_id", "locality", "relative_capacity"]].copy()
    centers["pop_share"] = centers["relative_capacity"] / centers["relative_capacity"].sum()
    centers["locality_population"] = (centers["pop_share"] * MALARD_APPROX_POPULATION).round().astype(int)

    rows = []
    for _, row in centers.iterrows():
        for age_band, share in AGE_BAND_SHARES.items():
            rows.append({
                "center_id": row["center_id"],
                "locality": row["locality"],
                "age_band": age_band,
                "eligible_population": int(round(row["locality_population"] * share)),
            })
    return pd.DataFrame(rows)
