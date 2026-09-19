import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from malard_vax.data_generation.centers import VACCINE_TYPES, delivery_centers
from malard_vax.data_generation.vaccination_curve import (
    generate_daily_vaccinations,
    generate_supply_center_log,
)


def test_generated_columns_present():
    df = generate_daily_vaccinations(seed=1)
    expected = {"date", "jalali_date", "center_id", "center_name", "locality", "vaccine_type", "doses_administered"}
    assert expected.issubset(df.columns)


def test_only_known_centers_and_vaccine_types():
    df = generate_daily_vaccinations(seed=1)
    assert set(df["center_id"]) == set(delivery_centers()["center_id"])
    assert set(df["vaccine_type"]) == set(VACCINE_TYPES)


def test_doses_are_non_negative_integers():
    df = generate_daily_vaccinations(seed=1)
    assert (df["doses_administered"] >= 0).all()
    assert pd.api.types.is_integer_dtype(df["doses_administered"])


def test_network_starts_low_peaks_mid_and_ends_low():
    df = generate_daily_vaccinations(seed=1)
    daily_total = df.groupby("date")["doses_administered"].sum().sort_index()
    first_week_avg = daily_total.iloc[:7].mean()
    last_week_avg = daily_total.iloc[-7:].mean()
    peak = daily_total.rolling(7).mean().max()

    assert first_week_avg < 900          # brief described start: ~500/day
    assert last_week_avg < 1000          # brief described end: ~600/day
    assert peak > 2800                   # brief described peak: ~3500/day


def test_supply_log_distributed_matches_administered_totals():
    vax = generate_daily_vaccinations(seed=1)
    supply = generate_supply_center_log(vax, seed=1)
    daily_total = vax.groupby("date")["doses_administered"].sum()
    merged = supply.set_index("date")["doses_distributed"].reindex(daily_total.index)
    pd.testing.assert_series_equal(
        merged.astype(float), daily_total.astype(float), check_names=False
    )


def test_reproducible_with_same_seed():
    df1 = generate_daily_vaccinations(seed=99)
    df2 = generate_daily_vaccinations(seed=99)
    pd.testing.assert_frame_equal(df1, df2)
