"""
Static metadata for the six sites in the network: five vaccination
centers that administer doses to the public, plus one central supply
& cold-chain site that receives shipments from the national EPI
program and distributes them onward to the five centers.

Center names below are illustrative (this is a synthetic demo
dataset, not a disclosure of real facility operations) but are
modeled after real localities inside Malard County, Tehran Province,
to keep the scenario grounded.
"""
from __future__ import annotations

import pandas as pd

VACCINE_TYPES = ["Sinopharm", "AstraZeneca", "COVIran Barekat"]

CENTERS = [
    {
        "center_id": "MLD-01",
        "center_name": "Malard Central Health Center",
        "center_type": "vaccination_center",
        "locality": "Malard",
        "relative_capacity": 1.15,  # largest urban center, above-average throughput
    },
    {
        "center_id": "MLD-02",
        "center_name": "Sabashahr Health Center",
        "center_type": "vaccination_center",
        "locality": "Sabashahr",
        "relative_capacity": 1.00,
    },
    {
        "center_id": "MLD-03",
        "center_name": "Vahedieh Health Center",
        "center_type": "vaccination_center",
        "locality": "Vahedieh",
        "relative_capacity": 0.85,
    },
    {
        "center_id": "MLD-04",
        "center_name": "Sadeghieh-e Malard Vaccination Center",
        "center_type": "vaccination_center",
        "locality": "Sadeghieh",
        "relative_capacity": 0.80,
    },
    {
        "center_id": "MLD-05",
        "center_name": "Chelab Rural Vaccination Center",
        "center_type": "vaccination_center",
        "locality": "Chelab",
        "relative_capacity": 0.60,  # smaller, rural catchment
    },
    {
        "center_id": "MLD-SUP",
        "center_name": "Malard District Vaccine Supply & Cold Chain Center",
        "center_type": "supply_center",
        "locality": "Malard",
        "relative_capacity": None,
    },
]


def centers_dataframe() -> pd.DataFrame:
    return pd.DataFrame(CENTERS)


def delivery_centers() -> pd.DataFrame:
    """The five sites that actually administer doses to the public."""
    df = centers_dataframe()
    return df[df["center_type"] == "vaccination_center"].reset_index(drop=True)


def supply_center() -> dict:
    return next(c for c in CENTERS if c["center_type"] == "supply_center")
