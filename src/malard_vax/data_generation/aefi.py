"""
Synthetic Adverse Events Following Immunization (AEFI) log.

Rates are illustrative, loosely consistent with published ranges for
COVID-19 vaccine reactogenicity (mild/local reactions common,
moderate systemic reactions uncommon, serious events rare) - not
drawn from any real pharmacovigilance registry for Malard County or
Iran. See docs/data_dictionary.md for the honesty note.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SEVERITY_RATES_PER_1000_DOSES = {
    "Mild (local reaction)": 18.0,
    "Moderate (systemic, self-resolving)": 3.5,
    "Serious (medically attended)": 0.12,
}

SYMPTOMS_BY_SEVERITY = {
    "Mild (local reaction)": ["Injection-site pain", "Redness/swelling", "Mild fatigue"],
    "Moderate (systemic, self-resolving)": ["Fever", "Chills", "Headache", "Myalgia"],
    "Serious (medically attended)": ["Allergic reaction", "Severe fever", "Syncope"],
}


def generate_aefi_log(daily_vax_df: pd.DataFrame, seed: int = 55) -> pd.DataFrame:
    """
    One row per AEFI report, sampled probabilistically from the
    (date, center, vaccine_type, dose_number, doses_administered)
    rows of the vaccination dataset.
    """
    rng = np.random.default_rng(seed)
    rows = []
    report_id = 1

    grouped = (
        daily_vax_df.groupby(["date", "center_id", "center_name", "vaccine_type", "dose_number"])
        ["doses_administered"].sum().reset_index()
    )
    grouped = grouped[grouped["doses_administered"] > 0]

    for _, row in grouped.iterrows():
        for severity, rate_per_1000 in SEVERITY_RATES_PER_1000_DOSES.items():
            expected = row["doses_administered"] * (rate_per_1000 / 1000.0)
            n_events = rng.poisson(expected)
            for _ in range(n_events):
                symptom = rng.choice(SYMPTOMS_BY_SEVERITY[severity])
                rows.append({
                    "report_id": f"AEFI-{report_id:05d}",
                    "date": row["date"],
                    "center_id": row["center_id"],
                    "center_name": row["center_name"],
                    "vaccine_type": row["vaccine_type"],
                    "dose_number": row["dose_number"],
                    "severity": severity,
                    "reported_symptom": symptom,
                })
                report_id += 1

    return pd.DataFrame(rows)
