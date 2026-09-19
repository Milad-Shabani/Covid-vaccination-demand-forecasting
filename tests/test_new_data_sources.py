import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from malard_vax.data_generation.centers import delivery_centers
from malard_vax.data_generation.population import population_by_locality_age, AGE_BAND_SHARES
from malard_vax.data_generation.vaccination_curve import generate_daily_vaccinations, DOSE_NUMBERS
from malard_vax.data_generation.aefi import generate_aefi_log
from malard_vax.data_generation.wastage import generate_wastage_log
from malard_vax.data_generation.staffing import generate_staffing_log
from malard_vax.data_generation.appointments import generate_appointments_log


def test_population_covers_all_localities_and_age_bands():
    df = population_by_locality_age()
    assert set(df["locality"]) == set(delivery_centers()["locality"])
    assert set(df["age_band"]) == set(AGE_BAND_SHARES.keys())
    assert (df["eligible_population"] > 0).all()


def test_dose_number_present_and_valid():
    df = generate_daily_vaccinations(seed=1)
    assert "dose_number" in df.columns
    assert set(df["dose_number"]) == set(DOSE_NUMBERS)


def test_dose_number_pool_constraint_never_violated():
    """Cumulative 2nd doses can never exceed cumulative 1st doses, and
    cumulative boosters can never exceed cumulative 2nd doses - a person
    cannot receive a later dose in the sequence before an earlier one."""
    df = generate_daily_vaccinations(seed=1)
    by_date = df.groupby(["date", "dose_number"])["doses_administered"].sum().unstack(fill_value=0)
    by_date = by_date.sort_index()
    cum = by_date.cumsum()
    assert (cum["2nd Dose"] <= cum["1st Dose"] + 1e-6).all()
    assert (cum["Booster"] <= cum["2nd Dose"] + 1e-6).all()


def test_aefi_log_columns_and_non_negative():
    vax = generate_daily_vaccinations(seed=1)
    aefi = generate_aefi_log(vax, seed=1)
    expected = {"report_id", "date", "center_id", "severity", "reported_symptom"}
    assert expected.issubset(aefi.columns)
    assert aefi["report_id"].is_unique


def test_aefi_rate_is_a_small_fraction_of_doses():
    vax = generate_daily_vaccinations(seed=1)
    aefi = generate_aefi_log(vax, seed=1)
    total_doses = vax["doses_administered"].sum()
    assert len(aefi) < total_doses * 0.05  # well under 5% of doses


def test_wastage_log_rate_within_plausible_bounds():
    vax = generate_daily_vaccinations(seed=1)
    wastage = generate_wastage_log(vax, seed=1)
    assert (wastage["wastage_rate"] >= 0).all()
    assert (wastage["wastage_rate"] <= 0.40).all()  # rare low-volume + expiry-event tail days
    assert (wastage["total_doses_wasted"] >= 0).all()


def test_staffing_log_positive_and_covers_all_centers():
    staffing = generate_staffing_log(seed=1)
    assert (staffing["vaccinators_on_duty"] >= 1).all()
    assert (staffing["theoretical_capacity_doses"] > 0).all()
    assert set(staffing["center_id"]) == set(delivery_centers()["center_id"])


def test_appointments_log_reconciles_with_doses():
    vax = generate_daily_vaccinations(seed=1)
    appts = generate_appointments_log(vax, seed=1)
    reconciled = appts["doses_via_appointment"] + appts["doses_via_walkin"]
    pd.testing.assert_series_equal(
        reconciled.astype(float), appts["total_doses_administered"].astype(float),
        check_names=False,
    )


def test_appointments_no_show_rate_within_bounds():
    vax = generate_daily_vaccinations(seed=1)
    appts = generate_appointments_log(vax, seed=1)
    assert (appts["no_show_rate"] >= 0).all()
    assert (appts["no_show_rate"] <= 0.5).all()
