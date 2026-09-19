"""
Generate the full synthetic raw dataset for the Malard VaxForecast
project: center metadata, daily per-center/per-vaccine doses, the
supply-center log, and the modeled daily case-count series.

Usage:
    python scripts/generate_sample_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from malard_vax.data_generation.centers import centers_dataframe  # noqa: E402
from malard_vax.data_generation.epidemic_curve import generate_daily_cases  # noqa: E402
from malard_vax.data_generation.vaccination_curve import (  # noqa: E402
    generate_daily_vaccinations,
    generate_supply_center_log,
)
from malard_vax.data_generation.population import population_by_locality_age  # noqa: E402
from malard_vax.data_generation.aefi import generate_aefi_log  # noqa: E402
from malard_vax.data_generation.wastage import generate_wastage_log  # noqa: E402
from malard_vax.data_generation.staffing import generate_staffing_log  # noqa: E402
from malard_vax.data_generation.appointments import generate_appointments_log  # noqa: E402
from malard_vax.analytics.operational_kpis import build_all as build_operational_kpis  # noqa: E402

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating center metadata...")
    centers_dataframe().to_csv(RAW_DIR / "vaccination_centers.csv", index=False)

    print("Generating eligible-population reference table...")
    population = population_by_locality_age()
    population.to_csv(RAW_DIR / "population_by_locality_age.csv", index=False)
    print(f"  -> {len(population):,} rows")

    print("Generating daily per-center / per-vaccine / per-dose-number records...")
    daily_vax = generate_daily_vaccinations()
    daily_vax.to_csv(RAW_DIR / "daily_vaccinations.csv", index=False)
    print(f"  -> {len(daily_vax):,} rows")

    print("Deriving supply-center shipment/stock log...")
    supply_log = generate_supply_center_log(daily_vax)
    supply_log.to_csv(RAW_DIR / "supply_center_log.csv", index=False)
    print(f"  -> {len(supply_log):,} rows")

    print("Generating modeled daily confirmed-case series...")
    cases = generate_daily_cases()
    cases.to_csv(RAW_DIR / "daily_covid_cases.csv", index=False)
    print(f"  -> {len(cases):,} rows")

    print("Generating AEFI (adverse event) log...")
    aefi = generate_aefi_log(daily_vax)
    aefi.to_csv(RAW_DIR / "aefi_reports.csv", index=False)
    print(f"  -> {len(aefi):,} rows")

    print("Generating vaccine wastage log...")
    wastage = generate_wastage_log(daily_vax)
    wastage.to_csv(RAW_DIR / "vaccine_wastage_log.csv", index=False)
    print(f"  -> {len(wastage):,} rows")

    print("Generating center staffing log...")
    staffing = generate_staffing_log()
    staffing.to_csv(RAW_DIR / "center_staffing_log.csv", index=False)
    print(f"  -> {len(staffing):,} rows")

    print("Generating appointments / no-show log...")
    appointments = generate_appointments_log(daily_vax)
    appointments.to_csv(RAW_DIR / "appointments_log.csv", index=False)
    print(f"  -> {len(appointments):,} rows")

    total_doses = daily_vax["doses_administered"].sum()
    total_cases = cases["new_confirmed_cases"].sum()
    total_wasted = wastage["total_doses_wasted"].sum()
    total_aefi = len(aefi)
    print("\nSummary")
    print("-------")
    print(f"Study window : {daily_vax['date'].min()} -> {daily_vax['date'].max()}")
    print(f"Total doses administered (network): {total_doses:,}")
    print(f"Total modeled confirmed cases      : {total_cases:,}")
    print(f"Total doses wasted (open-vial+expired): {total_wasted:,}")
    print(f"Total AEFI reports                 : {total_aefi:,}")
    print(f"\nRaw files written to: {RAW_DIR}")

    print("\nComputing operational KPIs (coverage, wastage, staffing, AEFI, appointments)...")
    build_operational_kpis(RAW_DIR, PROCESSED_DIR)


if __name__ == "__main__":
    main()
