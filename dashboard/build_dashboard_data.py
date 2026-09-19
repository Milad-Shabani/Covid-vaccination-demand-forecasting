"""
Dashboard Data Builder
------------------------
Aggregates every raw/processed table + report artifact into one JSON
payload so the dashboard is a fully static, self-contained HTML file.
"""
import json
import base64
import os
import pandas as pd
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
REPORTS = os.path.join(BASE, "reports")
OUT = os.path.join(os.path.dirname(__file__), "dist")
os.makedirs(OUT, exist_ok=True)


def r(x, n=2):
    if isinstance(x, (np.floating, np.integer)):
        x = x.item()
    return round(x, n) if isinstance(x, float) else x


centers = pd.read_csv(os.path.join(RAW, "vaccination_centers.csv"))
daily_vax = pd.read_csv(os.path.join(RAW, "daily_vaccinations.csv"))
supply = pd.read_csv(os.path.join(RAW, "supply_center_log.csv"))
cases = pd.read_csv(os.path.join(RAW, "daily_covid_cases.csv"))
population = pd.read_csv(os.path.join(RAW, "population_by_locality_age.csv"))
aefi = pd.read_csv(os.path.join(RAW, "aefi_reports.csv"))
wastage = pd.read_csv(os.path.join(RAW, "vaccine_wastage_log.csv"))
staffing = pd.read_csv(os.path.join(RAW, "center_staffing_log.csv"))
appointments = pd.read_csv(os.path.join(RAW, "appointments_log.csv"))

coverage_by_dose = pd.read_csv(os.path.join(PROC, "coverage_by_dose.csv"))
coverage_by_locality = pd.read_csv(os.path.join(PROC, "coverage_by_locality.csv"))
wastage_summary = pd.read_csv(os.path.join(PROC, "wastage_summary.csv"))
staffing_summary = pd.read_csv(os.path.join(PROC, "staffing_utilization_summary.csv"))
aefi_summary = pd.read_csv(os.path.join(PROC, "aefi_rate_summary.csv"))
appt_perf = pd.read_csv(os.path.join(PROC, "appointment_performance_monthly.csv"))
future_forecast = pd.read_csv(os.path.join(PROC, "future_forecast_30d.csv"))

metrics_multistep = pd.read_csv(os.path.join(REPORTS, "metrics_multistep.csv"))
metrics_onestep = pd.read_csv(os.path.join(REPORTS, "metrics_onestep.csv"))

data = {}

# ============================================================= OVERVIEW ===
total_doses = int(daily_vax["doses_administered"].sum())
daily_totals = daily_vax.groupby("date")["doses_administered"].sum().reset_index()
daily_totals["date"] = pd.to_datetime(daily_totals["date"])
peak_row = daily_totals.loc[daily_totals["doses_administered"].idxmax()]
total_eligible = int(population["eligible_population"].sum())
cov_final = coverage_by_dose[coverage_by_dose["date"] == coverage_by_dose["date"].max()]
cov_map = dict(zip(cov_final["dose_number"], cov_final["coverage_pct"]))
total_cases = int(cases["new_confirmed_cases"].sum())
cases_peak = cases.loc[cases["new_confirmed_cases"].idxmax()]
total_wasted = int(wastage["total_doses_wasted"].sum())
overall_wastage_rate = round(total_wasted / wastage["doses_drawn_from_vials"].sum() * 100, 2)
overall_util = round(staffing_summary["avg_utilization_pct"].mean(), 1)
overall_noshow = round(appointments["no_shows"].sum() / appointments["appointments_scheduled"].sum() * 100, 1)
serious_rate = float(aefi_summary.loc[aefi_summary["severity"].str.contains("Serious"), "rate_per_100k_doses"].iloc[0])

data["overview"] = {
    "kpis": {
        "total_doses": total_doses,
        "total_centers": int(len(centers)),
        "study_days": int(len(daily_totals)),
        "eligible_population": total_eligible,
        "coverage_1st": r(cov_map.get("1st Dose", 0), 1),
        "coverage_2nd": r(cov_map.get("2nd Dose", 0), 1),
        "coverage_booster": r(cov_map.get("Booster", 0), 1),
        "total_cases": total_cases,
        "peak_daily_doses": int(peak_row["doses_administered"]),
        "peak_doses_date": peak_row["date"].strftime("%Y-%m-%d"),
        "peak_daily_cases": int(cases_peak["new_confirmed_cases"]),
        "avg_doses_per_day": r(daily_totals["doses_administered"].mean()),
        "wastage_rate_pct": overall_wastage_rate,
        "staffing_utilization_pct": overall_util,
        "no_show_rate_pct": overall_noshow,
        "aefi_serious_rate": serious_rate,
    },
    "doses_trend": {"dates": daily_totals["date"].dt.strftime("%Y-%m-%d").tolist(),
                     "doses": daily_totals["doses_administered"].tolist()},
    "cases_trend": {"dates": cases["date"].tolist(), "cases": cases["new_confirmed_cases"].tolist()},
    "coverage_trend": {
        "dates": sorted(coverage_by_dose["date"].unique().tolist()),
        "first": coverage_by_dose[coverage_by_dose["dose_number"] == "1st Dose"].sort_values("date")["coverage_pct"].tolist(),
        "second": coverage_by_dose[coverage_by_dose["dose_number"] == "2nd Dose"].sort_values("date")["coverage_pct"].tolist(),
        "booster": coverage_by_dose[coverage_by_dose["dose_number"] == "Booster"].sort_values("date")["coverage_pct"].tolist(),
    },
}

# ============================================================ COVERAGE ===
vtype_mix = daily_vax.groupby("vaccine_type")["doses_administered"].sum()
dose_mix = daily_vax.groupby("dose_number")["doses_administered"].sum()
data["coverage"] = {
    "by_locality": coverage_by_locality.to_dict(orient="records"),
    "vaccine_type_totals": vtype_mix.to_dict(),
    "dose_number_totals": dose_mix.reindex(["1st Dose", "2nd Dose", "Booster"]).to_dict(),
    "kpis": {
        "total_first": int(dose_mix.get("1st Dose", 0)),
        "total_second": int(dose_mix.get("2nd Dose", 0)),
        "total_booster": int(dose_mix.get("Booster", 0)),
        "avg_locality_coverage": r(coverage_by_locality["first_dose_coverage_pct"].mean(), 1),
        "best_locality": coverage_by_locality.loc[coverage_by_locality["first_dose_coverage_pct"].idxmax(), "locality"],
        "lagging_locality": coverage_by_locality.loc[coverage_by_locality["first_dose_coverage_pct"].idxmin(), "locality"],
    },
}

# ============================================================== EPIDEMIC ===
cases["cases_7d_avg"] = cases["new_confirmed_cases"].rolling(7, min_periods=1).mean().round(1)
data["epidemic"] = {
    "dates": cases["date"].tolist(),
    "new_cases": cases["new_confirmed_cases"].tolist(),
    "cases_7d_avg": cases["cases_7d_avg"].tolist(),
    "cumulative_cases": cases["cumulative_confirmed_cases"].tolist(),
    "doses_dates": daily_totals["date"].dt.strftime("%Y-%m-%d").tolist(),
    "doses": daily_totals["doses_administered"].tolist(),
    "kpis": {
        "total_cases": total_cases,
        "peak_cases": int(cases_peak["new_confirmed_cases"]),
        "peak_cases_date": cases_peak["date"],
        "final_cumulative": int(cases["cumulative_confirmed_cases"].iloc[-1]),
    },
}

# =========================================================== CENTERS ===
by_center = daily_vax.groupby(["center_id", "center_name"])["doses_administered"].sum().reset_index()
by_center["share_pct"] = r(by_center["doses_administered"] / by_center["doses_administered"].sum() * 100, 1)
by_center = by_center.merge(centers[["center_id", "locality", "center_type", "relative_capacity"]], on="center_id")
by_center = by_center.sort_values("doses_administered", ascending=False)
data["centers"] = {
    "table": by_center.to_dict(orient="records"),
    "kpis": {
        "top_center": by_center.iloc[0]["center_name"],
        "top_center_doses": int(by_center.iloc[0]["doses_administered"]),
        "lowest_center": by_center.iloc[-1]["center_name"],
        "lowest_center_doses": int(by_center.iloc[-1]["doses_administered"]),
    },
}

# ============================================================== SUPPLY ===
data["supply"] = {
    "dates": supply["date"].tolist(),
    "doses_received": supply["doses_received"].tolist(),
    "doses_distributed": supply["doses_distributed"].tolist(),
    "closing_stock": supply["closing_stock"].tolist(),
    "wastage_by_center": wastage_summary.to_dict(orient="records"),
    "kpis": {
        "total_received": int(supply["doses_received"].sum()),
        "total_distributed": int(supply["doses_distributed"].sum()),
        "final_stock": int(supply["closing_stock"].iloc[-1]),
        "total_wasted": total_wasted,
        "overall_wastage_rate_pct": overall_wastage_rate,
        "highest_wastage_center": wastage_summary.iloc[0]["center_name"],
        "highest_wastage_rate": r(wastage_summary.iloc[0]["wastage_rate_pct"], 1),
    },
}

# ============================================================= STAFFING ===
staff_trend = staffing.groupby("date")["vaccinators_on_duty"].sum().reset_index()
data["staffing"] = {
    "by_center": staffing_summary.to_dict(orient="records"),
    "dates": staff_trend["date"].tolist(),
    "vaccinators_total": staff_trend["vaccinators_on_duty"].tolist(),
    "kpis": {
        "avg_utilization_pct": overall_util,
        "avg_vaccinators_network": r(staffing_summary["avg_vaccinators_on_duty"].sum(), 1),
        "most_utilized_center": staffing_summary.iloc[0]["center_name"],
        "most_utilized_pct": r(staffing_summary.iloc[0]["avg_utilization_pct"], 1),
        "least_utilized_center": staffing_summary.iloc[-1]["center_name"],
        "least_utilized_pct": r(staffing_summary.iloc[-1]["avg_utilization_pct"], 1),
    },
}

# =========================================================== APPOINTMENTS ===
total_appts = int(appointments["appointments_scheduled"].sum())
total_noshows = int(appointments["no_shows"].sum())
total_via_appt = int(appointments["doses_via_appointment"].sum())
total_via_walkin = int(appointments["doses_via_walkin"].sum())
data["appointments"] = {
    "monthly": appt_perf.to_dict(orient="records"),
    "kpis": {
        "total_appointments": total_appts,
        "total_no_shows": total_noshows,
        "no_show_rate_pct": overall_noshow,
        "doses_via_appointment": total_via_appt,
        "doses_via_walkin": total_via_walkin,
        "appointment_share_pct": r(total_via_appt / (total_via_appt + total_via_walkin) * 100, 1),
    },
}

# ================================================================= AEFI ===
by_vtype_severity = aefi.groupby(["vaccine_type", "severity"]).size().reset_index(name="count")
data["aefi"] = {
    "by_severity": aefi_summary.to_dict(orient="records"),
    "by_vaccine_type": by_vtype_severity.to_dict(orient="records"),
    "kpis": {
        "total_reports": int(len(aefi)),
        "mild_rate": float(aefi_summary.loc[aefi_summary["severity"].str.contains("Mild"), "rate_per_100k_doses"].iloc[0]),
        "moderate_rate": float(aefi_summary.loc[aefi_summary["severity"].str.contains("Moderate"), "rate_per_100k_doses"].iloc[0]),
        "serious_rate": serious_rate,
    },
}

# ============================================================== FORECAST ===
data["forecast"] = {
    "multistep_metrics": metrics_multistep.to_dict(orient="records"),
    "onestep_metrics": metrics_onestep.to_dict(orient="records"),
    "future_dates": future_forecast["date"].tolist(),
    "sarima_forecast": future_forecast["sarima_forecast"].round(1).tolist(),
    "sarima_lower": future_forecast["sarima_lower_95"].round(1).tolist(),
    "sarima_upper": future_forecast["sarima_upper_95"].round(1).tolist(),
    "xgboost_forecast": future_forecast["xgboost_forecast"].round(1).tolist(),
}

# Embed the existing report figures as base64 (self-contained, no external files)
figures = {}
fig_dir = os.path.join(REPORTS, "figures")
for fname in ["multistep_forecast_vs_actual.png", "onestep_forecast_vs_actual.png",
              "future_30day_forecast.png", "xgboost_feature_importance.png"]:
    fpath = os.path.join(fig_dir, fname)
    if os.path.exists(fpath):
        with open(fpath, "rb") as f:
            figures[fname] = "data:image/png;base64," + base64.b64encode(f.read()).decode()
data["figures"] = figures

with open(os.path.join(OUT, "dashboard_data.json"), "w") as fh:
    json.dump(data, fh, default=str)

print(f"Dashboard data written: {os.path.join(OUT, 'dashboard_data.json')}")
print(f"Size: {os.path.getsize(os.path.join(OUT, 'dashboard_data.json')) / 1024:.1f} KB")
