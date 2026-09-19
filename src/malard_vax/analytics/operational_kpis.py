"""
Derived operational KPIs computed from the raw synthetic tables, written
to data/processed/ for consumption by the dashboard and for ad-hoc
analysis. None of this re-fits the forecasting models - it is descriptive
analytics over the already-generated data.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def compute_coverage_by_dose(daily_vax: pd.DataFrame, population: pd.DataFrame) -> pd.DataFrame:
    """
    Cumulative distinct-recipients coverage % by dose number over time,
    network-wide. Since this is aggregate (not individual-level) synthetic
    data, "coverage" is approximated as cumulative doses of a given
    dose_number divided by total eligible population - a standard
    simplification used when only aggregate dose counts (not a person-level
    vaccination registry) are available.
    """
    total_eligible = population["eligible_population"].sum()
    daily = (
        daily_vax.groupby(["date", "dose_number"])["doses_administered"]
        .sum()
        .reset_index()
        .sort_values("date")
    )
    daily["cumulative_doses"] = daily.groupby("dose_number")["doses_administered"].cumsum()
    daily["coverage_pct"] = np.round(daily["cumulative_doses"] / total_eligible * 100, 2)
    return daily


def compute_coverage_by_locality(daily_vax: pd.DataFrame, population: pd.DataFrame) -> pd.DataFrame:
    """First-dose coverage % by locality, as of the end of the study window."""
    locality_pop = population.groupby("locality")["eligible_population"].sum().reset_index()
    first_dose_total = (
        daily_vax[daily_vax["dose_number"] == "1st Dose"]
        .groupby("locality")["doses_administered"].sum().reset_index()
        .rename(columns={"doses_administered": "cumulative_first_doses"})
    )
    out = locality_pop.merge(first_dose_total, on="locality", how="left").fillna(0)
    out["first_dose_coverage_pct"] = np.round(
        out["cumulative_first_doses"] / out["eligible_population"] * 100, 1
    )
    return out


def compute_wastage_summary(wastage: pd.DataFrame) -> pd.DataFrame:
    by_center = wastage.groupby("center_name").agg(
        total_doses_wasted=("total_doses_wasted", "sum"),
        total_doses_drawn=("doses_drawn_from_vials", "sum"),
    ).reset_index()
    by_center["wastage_rate_pct"] = np.round(
        by_center["total_doses_wasted"] / by_center["total_doses_drawn"].clip(lower=1) * 100, 2
    )
    return by_center.sort_values("wastage_rate_pct", ascending=False)


def compute_staffing_utilization(staffing: pd.DataFrame, daily_vax: pd.DataFrame) -> pd.DataFrame:
    doses_by_center_day = (
        daily_vax.groupby(["date", "center_id"])["doses_administered"].sum().reset_index()
    )
    merged = staffing.merge(doses_by_center_day, on=["date", "center_id"], how="left").fillna(0)
    merged["utilization_pct"] = np.round(
        merged["doses_administered"] / merged["theoretical_capacity_doses"].clip(lower=1) * 100, 1
    )
    by_center = merged.groupby("center_name").agg(
        avg_vaccinators_on_duty=("vaccinators_on_duty", "mean"),
        avg_utilization_pct=("utilization_pct", "mean"),
    ).reset_index()
    return by_center.sort_values("avg_utilization_pct", ascending=False), merged


def compute_aefi_rate(aefi: pd.DataFrame, daily_vax: pd.DataFrame) -> pd.DataFrame:
    total_doses = daily_vax["doses_administered"].sum()
    by_severity = aefi.groupby("severity").size().reset_index(name="report_count")
    by_severity["rate_per_100k_doses"] = np.round(
        by_severity["report_count"] / total_doses * 100_000, 2
    )
    return by_severity


def compute_appointment_performance(appointments: pd.DataFrame) -> pd.DataFrame:
    monthly = appointments.copy()
    monthly["month"] = pd.to_datetime(monthly["date"]).dt.to_period("M").astype(str)
    out = monthly.groupby("month").agg(
        appointments_scheduled=("appointments_scheduled", "sum"),
        no_shows=("no_shows", "sum"),
        doses_via_appointment=("doses_via_appointment", "sum"),
        doses_via_walkin=("doses_via_walkin", "sum"),
    ).reset_index()
    out["no_show_rate_pct"] = np.round(out["no_shows"] / out["appointments_scheduled"].clip(lower=1) * 100, 1)
    return out


def build_all(raw_dir: Path, processed_dir: Path) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)

    daily_vax = pd.read_csv(raw_dir / "daily_vaccinations.csv")
    population = pd.read_csv(raw_dir / "population_by_locality_age.csv")
    wastage = pd.read_csv(raw_dir / "vaccine_wastage_log.csv")
    staffing = pd.read_csv(raw_dir / "center_staffing_log.csv")
    aefi = pd.read_csv(raw_dir / "aefi_reports.csv")
    appointments = pd.read_csv(raw_dir / "appointments_log.csv")

    compute_coverage_by_dose(daily_vax, population).to_csv(
        processed_dir / "coverage_by_dose.csv", index=False)
    compute_coverage_by_locality(daily_vax, population).to_csv(
        processed_dir / "coverage_by_locality.csv", index=False)
    compute_wastage_summary(wastage).to_csv(
        processed_dir / "wastage_summary.csv", index=False)
    staffing_summary, staffing_daily = compute_staffing_utilization(staffing, daily_vax)
    staffing_summary.to_csv(processed_dir / "staffing_utilization_summary.csv", index=False)
    compute_aefi_rate(aefi, daily_vax).to_csv(
        processed_dir / "aefi_rate_summary.csv", index=False)
    compute_appointment_performance(appointments).to_csv(
        processed_dir / "appointment_performance_monthly.csv", index=False)

    print("Operational analytics written to", processed_dir)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    build_all(root / "data" / "raw", root / "data" / "processed")
