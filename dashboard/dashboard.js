// ============================================================================
// Malard Vaccination Network — Operations Dashboard
// Static, self-contained. All data pre-aggregated at build time.
// ============================================================================
const NAV = [
  {id:"overview",     label:"Overview",              sub:"Network-wide campaign summary"},
  {id:"coverage",      label:"Vaccination & Coverage", sub:"Dose sequence, vaccine mix, coverage by locality"},
  {id:"epidemic",      label:"Epidemic Context",       sub:"Confirmed cases vs. vaccination throughput"},
  {id:"centers",       label:"Center Performance",     sub:"Doses, share and ranking by center"},
  {id:"supply",        label:"Supply &amp; Wastage",   sub:"Stock levels and vaccine wastage"},
  {id:"staffing",      label:"Staffing",               sub:"Vaccinators on duty and capacity utilization"},
  {id:"appointments",  label:"Appointments &amp; No-Shows", sub:"Scheduling channel mix and no-show trend"},
  {id:"safety",        label:"Safety (AEFI)",          sub:"Adverse events following immunization"},
  {id:"forecast",      label:"Forecast Comparison",    sub:"SARIMA vs. XGBoost, one-step and multi-step"},
];

const fmtNum = (v) => (v===null||v===undefined||isNaN(v)) ? "–" : Math.round(v).toLocaleString();
const fmtDec = (v,d=1) => (v===null||v===undefined||isNaN(v)) ? "–" : Number(v).toFixed(d);
const fmtPct = (v,d=1) => (v===null||v===undefined||isNaN(v)) ? "–" : Number(v).toFixed(d) + "%";

const PALETTE = {
  accent:"#0E7C86", blue:"#2F6FED", gold:"#C98A2C", red:"#C0392B",
  ink:"#0B2545", inkSoft:"#33465F", muted:"#72839C", line:"#E2E8F0",
  series:["#0E7C86","#2F6FED","#C98A2C","#C0392B","#6B5B95","#3E8C8C","#8A6D3B","#5C7A99"]
};
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
Chart.defaults.color = PALETTE.inkSoft;
Chart.defaults.borderColor = PALETTE.line;

let activeCharts = [];
function destroyCharts(){ activeCharts.forEach(c=>c.destroy()); activeCharts = []; }
function mkChart(ctx, config){ const c = new Chart(ctx, config); activeCharts.push(c); return c; }

function kpiCard(label, value, cls="") {
  return `<div class="kpi ${cls}"><div class="label">${label}</div><div class="num">${value}</div></div>`;
}
function card(title, innerHtml) {
  return `<div class="card"><h3>${title}</h3>${innerHtml}</div>`;
}
function chartWrap(id, tall="") { return `<div class="chart-wrap ${tall}"><canvas id="${id}"></canvas></div>`; }
function severityTag(sev){
  const cls = sev.includes("Mild") ? "mild" : sev.includes("Moderate") ? "mod" : "serious";
  return `<span class="tag ${cls}">${sev}</span>`;
}

function baseLineOpts(showLegend=true, suffix=""){
  return {responsive:true, maintainAspectRatio:false,
    interaction:{mode:"index", intersect:false},
    plugins:{legend:{display:showLegend, position:"bottom", labels:{boxWidth:10,font:{size:11}}}},
    scales:{ y:{ ticks:{ callback:(v)=> suffix==="%" ? v+"%" : fmtNum(v) }, grid:{color:PALETTE.line} },
             x:{ grid:{display:false}, ticks:{maxTicksLimit:10} } } };
}
function baseBarOpts(suffix=""){
  return {responsive:true, maintainAspectRatio:false,
    plugins:{legend:{display:false}},
    scales:{ y:{ ticks:{ callback:(v)=> suffix==="%" ? v+"%" : fmtNum(v) }, grid:{color:PALETTE.line} },
             x:{ grid:{display:false} } } };
}
function baseBarOptsH(suffix=""){
  return {responsive:true, maintainAspectRatio:false, indexAxis:"y",
    plugins:{legend:{display:false}},
    scales:{ x:{ ticks:{ callback:(v)=> suffix==="%" ? v+"%" : fmtNum(v) }, grid:{color:PALETTE.line} },
             y:{ grid:{display:false} } } };
}

// ---------------------------------------------------------------------------
// 1. OVERVIEW
// ---------------------------------------------------------------------------
function renderOverview(d){
  const k = d.overview.kpis;
  let html = `<div class="kpi-grid">
    ${kpiCard("Total Doses Administered", fmtNum(k.total_doses), "accent")}
    ${kpiCard("Vaccination Centers", k.total_centers)}
    ${kpiCard("Campaign Days", k.study_days)}
    ${kpiCard("Eligible Population", fmtNum(k.eligible_population))}
    ${kpiCard("1st-Dose Coverage", fmtPct(k.coverage_1st), "accent")}
    ${kpiCard("2nd-Dose Coverage", fmtPct(k.coverage_2nd), "accent")}
    ${kpiCard("Booster Coverage", fmtPct(k.coverage_booster), "accent")}
    ${kpiCard("Total Confirmed Cases", fmtNum(k.total_cases), "blue")}
    ${kpiCard("Peak Daily Doses", fmtNum(k.peak_daily_doses))}
    ${kpiCard("Peak Daily Cases", fmtNum(k.peak_daily_cases), "blue")}
    ${kpiCard("Avg Doses / Day", fmtNum(k.avg_doses_per_day))}
    ${kpiCard("Vaccine Wastage Rate", fmtPct(k.wastage_rate_pct), "gold")}
    ${kpiCard("Staffing Utilization", fmtPct(k.staffing_utilization_pct), "gold")}
    ${kpiCard("Appointment No-Show Rate", fmtPct(k.no_show_rate_pct), "gold")}
    ${kpiCard("Serious AEFI Rate /100k", fmtDec(k.aefi_serious_rate, 2), "red")}
  </div>
  <div class="grid-2">
    ${card("Daily Doses Administered (network)", chartWrap("chart-ov-doses","tall"))}
    ${card("Key Insights", `<ul class="insight-list">
      <li>The network reached ${fmtPct(k.coverage_1st)} first-dose coverage of the eligible population, with booster uptake at ${fmtPct(k.coverage_booster)}.</li>
      <li>Peak single-day throughput was ${fmtNum(k.peak_daily_doses)} doses on ${k.peak_doses_date}.</li>
      <li>Average staffing capacity utilization sits at ${fmtPct(k.staffing_utilization_pct)}, leaving headroom for surge days.</li>
      <li>Vaccine wastage runs at ${fmtPct(k.wastage_rate_pct)} network-wide, within typical multi-dose-vial ranges.</li>
      <li>${fmtPct(k.no_show_rate_pct)} of scheduled appointments result in a no-show.</li>
      <li>Serious adverse events remain rare at ${fmtDec(k.aefi_serious_rate,2)} per 100,000 doses.</li>
    </ul>`)}
  </div>
  <div class="grid-2">
    ${card("Confirmed Cases (daily)", chartWrap("chart-ov-cases"))}
    ${card("Cumulative Coverage by Dose", chartWrap("chart-ov-coverage"))}
  </div>`;
  document.getElementById("content").innerHTML = html;

  mkChart(document.getElementById("chart-ov-doses"), {type:"line",
    data:{labels:d.overview.doses_trend.dates, datasets:[{label:"Doses", data:d.overview.doses_trend.doses,
      borderColor:PALETTE.accent, backgroundColor:"rgba(14,124,134,0.08)", fill:true, tension:0.2, pointRadius:0}]},
    options:baseLineOpts(false)});

  mkChart(document.getElementById("chart-ov-cases"), {type:"line",
    data:{labels:d.overview.cases_trend.dates, datasets:[{label:"New Cases", data:d.overview.cases_trend.cases,
      borderColor:PALETTE.blue, backgroundColor:"transparent", tension:0.2, pointRadius:0}]},
    options:baseLineOpts(false)});

  mkChart(document.getElementById("chart-ov-coverage"), {type:"line",
    data:{labels:d.overview.coverage_trend.dates, datasets:[
      {label:"1st Dose", data:d.overview.coverage_trend.first, borderColor:PALETTE.series[0], pointRadius:0},
      {label:"2nd Dose", data:d.overview.coverage_trend.second, borderColor:PALETTE.series[1], pointRadius:0},
      {label:"Booster", data:d.overview.coverage_trend.booster, borderColor:PALETTE.series[3], pointRadius:0},
    ]}, options:baseLineOpts(true, "%")});
}

// ---------------------------------------------------------------------------
// 2. COVERAGE
// ---------------------------------------------------------------------------
function renderCoverage(d){
  const c = d.coverage;
  let html = `<div class="kpi-grid">
    ${kpiCard("Total 1st Doses", fmtNum(c.kpis.total_first), "accent")}
    ${kpiCard("Total 2nd Doses", fmtNum(c.kpis.total_second), "accent")}
    ${kpiCard("Total Boosters", fmtNum(c.kpis.total_booster), "accent")}
    ${kpiCard("Avg Locality Coverage", fmtPct(c.kpis.avg_locality_coverage))}
    ${kpiCard("Best-Covered Locality", c.kpis.best_locality)}
    ${kpiCard("Lagging Locality", c.kpis.lagging_locality, "gold")}
  </div>
  <div class="grid-2">
    ${card("First-Dose Coverage by Locality", chartWrap("chart-cov-locality"))}
    ${card("Dose-Sequence Mix", chartWrap("chart-cov-dosemix","short"))}
  </div>
  ${card("Doses by Vaccine Product", chartWrap("chart-cov-vtype"))}`;
  document.getElementById("content").innerHTML = html;

  mkChart(document.getElementById("chart-cov-locality"), {type:"bar",
    data:{labels:c.by_locality.map(r=>r.locality), datasets:[{label:"Coverage %", data:c.by_locality.map(r=>r.first_dose_coverage_pct), backgroundColor:PALETTE.accent}]},
    options:baseBarOpts("%")});

  mkChart(document.getElementById("chart-cov-dosemix"), {type:"doughnut",
    data:{labels:Object.keys(c.dose_number_totals), datasets:[{data:Object.values(c.dose_number_totals), backgroundColor:[PALETTE.series[0],PALETTE.series[1],PALETTE.series[3]]}]},
    options:{plugins:{legend:{position:"bottom"}}}});

  mkChart(document.getElementById("chart-cov-vtype"), {type:"bar",
    data:{labels:Object.keys(c.vaccine_type_totals), datasets:[{label:"Doses", data:Object.values(c.vaccine_type_totals), backgroundColor:PALETTE.blue}]},
    options:{...baseBarOpts(), indexAxis:"y"}});
}

// ---------------------------------------------------------------------------
// 3. EPIDEMIC CONTEXT
// ---------------------------------------------------------------------------
function renderEpidemic(d){
  const e = d.epidemic;
  let html = `<div class="kpi-grid">
    ${kpiCard("Total Confirmed Cases", fmtNum(e.kpis.total_cases), "blue")}
    ${kpiCard("Peak Daily Cases", fmtNum(e.kpis.peak_cases), "blue")}
    ${kpiCard("Peak Date", e.kpis.peak_cases_date)}
    ${kpiCard("Cumulative Cases (final)", fmtNum(e.kpis.final_cumulative), "blue")}
  </div>
  ${card("Daily Cases (7-day avg) vs. Vaccination Throughput", chartWrap("chart-epi-overlay","tall"))}
  <div style="margin-top:16px">${card("Cumulative Confirmed Cases", chartWrap("chart-epi-cumulative"))}</div>`;
  document.getElementById("content").innerHTML = html;

  mkChart(document.getElementById("chart-epi-overlay"), {type:"line",
    data:{labels:e.dates, datasets:[
      {label:"Cases (7d avg)", data:e.cases_7d_avg, borderColor:PALETTE.blue, yAxisID:"y", pointRadius:0},
      {label:"Doses Administered", data:e.doses, borderColor:PALETTE.accent, yAxisID:"y1", pointRadius:0},
    ]}, options:{responsive:true, maintainAspectRatio:false, interaction:{mode:"index",intersect:false},
      plugins:{legend:{position:"bottom"}},
      scales:{ y:{position:"left", title:{display:true,text:"Cases"}}, y1:{position:"right", title:{display:true,text:"Doses"}, grid:{display:false}},
               x:{grid:{display:false}, ticks:{maxTicksLimit:10}} }}});

  mkChart(document.getElementById("chart-epi-cumulative"), {type:"line",
    data:{labels:e.dates, datasets:[{label:"Cumulative Cases", data:e.cumulative_cases, borderColor:PALETTE.series[4],
      backgroundColor:"rgba(107,91,149,0.08)", fill:true, pointRadius:0}]}, options:baseLineOpts(false)});
}

// ---------------------------------------------------------------------------
// 4. CENTER PERFORMANCE
// ---------------------------------------------------------------------------
function renderCenters(d){
  const c = d.centers;
  let html = `<div class="kpi-grid">
    ${kpiCard("Top Center", c.kpis.top_center, "accent")}
    ${kpiCard("Top Center Doses", fmtNum(c.kpis.top_center_doses), "accent")}
    ${kpiCard("Lowest-Volume Center", c.kpis.lowest_center)}
    ${kpiCard("Lowest Center Doses", fmtNum(c.kpis.lowest_center_doses))}
  </div>
  <div class="grid-2">
    ${card("Total Doses by Center", chartWrap("chart-center-bar","tall"))}
    ${card("Center Detail", `<table><thead><tr><th>Center</th><th>Locality</th><th>Type</th><th>Doses</th><th>Share</th></tr></thead><tbody>
      ${c.table.map(r=>`<tr><td>${r.center_name}</td><td>${r.locality}</td><td>${r.center_type.replace("_"," ")}</td><td>${fmtNum(r.doses_administered)}</td><td>${fmtPct(r.share_pct)}</td></tr>`).join("")}
    </tbody></table>`)}
  </div>`;
  document.getElementById("content").innerHTML = html;
  mkChart(document.getElementById("chart-center-bar"), {type:"bar",
    data:{labels:c.table.map(r=>r.center_name), datasets:[{label:"Doses", data:c.table.map(r=>r.doses_administered), backgroundColor:PALETTE.accent}]},
    options:baseBarOptsH()});
}

// ---------------------------------------------------------------------------
// 5. SUPPLY & WASTAGE
// ---------------------------------------------------------------------------
function renderSupply(d){
  const s = d.supply;
  let html = `<div class="kpi-grid">
    ${kpiCard("Total Doses Received", fmtNum(s.kpis.total_received), "blue")}
    ${kpiCard("Total Doses Distributed", fmtNum(s.kpis.total_distributed), "blue")}
    ${kpiCard("Final Stock Level", fmtNum(s.kpis.final_stock))}
    ${kpiCard("Total Doses Wasted", fmtNum(s.kpis.total_wasted), "gold")}
    ${kpiCard("Network Wastage Rate", fmtPct(s.kpis.overall_wastage_rate_pct), "gold")}
    ${kpiCard("Highest-Wastage Center", s.kpis.highest_wastage_center, "gold")}
  </div>
  ${card("Supply Chain: Received / Distributed / Closing Stock", chartWrap("chart-supply-trend","tall"))}
  <div style="margin-top:16px">${card("Wastage Rate by Center", chartWrap("chart-supply-wastage"))}</div>`;
  document.getElementById("content").innerHTML = html;

  mkChart(document.getElementById("chart-supply-trend"), {type:"line",
    data:{labels:s.dates, datasets:[
      {label:"Received", data:s.doses_received, borderColor:PALETTE.blue, pointRadius:0},
      {label:"Distributed", data:s.doses_distributed, borderColor:PALETTE.accent, pointRadius:0},
      {label:"Closing Stock", data:s.closing_stock, borderColor:PALETTE.gold, pointRadius:0},
    ]}, options:baseLineOpts(true)});

  mkChart(document.getElementById("chart-supply-wastage"), {type:"bar",
    data:{labels:s.wastage_by_center.map(r=>r.center_name), datasets:[{label:"Wastage %", data:s.wastage_by_center.map(r=>r.wastage_rate_pct), backgroundColor:PALETTE.gold}]},
    options:baseBarOpts("%")});
}

// ---------------------------------------------------------------------------
// 6. STAFFING
// ---------------------------------------------------------------------------
function renderStaffing(d){
  const s = d.staffing;
  let html = `<div class="kpi-grid">
    ${kpiCard("Avg Network Utilization", fmtPct(s.kpis.avg_utilization_pct), "gold")}
    ${kpiCard("Avg Vaccinators (network)", fmtDec(s.kpis.avg_vaccinators_network))}
    ${kpiCard("Most-Utilized Center", s.kpis.most_utilized_center, "gold")}
    ${kpiCard("Most-Utilized %", fmtPct(s.kpis.most_utilized_pct), "gold")}
    ${kpiCard("Least-Utilized Center", s.kpis.least_utilized_center)}
    ${kpiCard("Least-Utilized %", fmtPct(s.kpis.least_utilized_pct))}
  </div>
  <div class="grid-2">
    ${card("Utilization % by Center", chartWrap("chart-staff-util"))}
    ${card("Total Vaccinators on Duty (network, daily)", chartWrap("chart-staff-trend"))}
  </div>`;
  document.getElementById("content").innerHTML = html;

  mkChart(document.getElementById("chart-staff-util"), {type:"bar",
    data:{labels:s.by_center.map(r=>r.center_name), datasets:[{label:"Utilization %", data:s.by_center.map(r=>r.avg_utilization_pct), backgroundColor:PALETTE.gold}]},
    options:baseBarOpts("%")});

  mkChart(document.getElementById("chart-staff-trend"), {type:"line",
    data:{labels:s.dates, datasets:[{label:"Vaccinators on Duty", data:s.vaccinators_total, borderColor:PALETTE.ink, pointRadius:0, tension:0.15}]},
    options:baseLineOpts(false)});
}

// ---------------------------------------------------------------------------
// 7. APPOINTMENTS & NO-SHOWS
// ---------------------------------------------------------------------------
function renderAppointments(d){
  const a = d.appointments;
  let html = `<div class="kpi-grid">
    ${kpiCard("Total Appointments Scheduled", fmtNum(a.kpis.total_appointments), "blue")}
    ${kpiCard("Total No-Shows", fmtNum(a.kpis.total_no_shows), "gold")}
    ${kpiCard("Avg No-Show Rate", fmtPct(a.kpis.no_show_rate_pct), "gold")}
    ${kpiCard("Doses via Appointment", fmtNum(a.kpis.doses_via_appointment), "accent")}
    ${kpiCard("Doses via Walk-in", fmtNum(a.kpis.doses_via_walkin))}
    ${kpiCard("Appointment Channel Share", fmtPct(a.kpis.appointment_share_pct), "accent")}
  </div>
  <div class="grid-2">
    ${card("Appointment vs. Walk-in Doses (monthly)", chartWrap("chart-appt-channel"))}
    ${card("No-Show Rate Trend (monthly)", chartWrap("chart-appt-noshow"))}
  </div>`;
  document.getElementById("content").innerHTML = html;

  mkChart(document.getElementById("chart-appt-channel"), {type:"bar",
    data:{labels:a.monthly.map(r=>r.month), datasets:[
      {label:"Via Appointment", data:a.monthly.map(r=>r.doses_via_appointment), backgroundColor:PALETTE.accent, stack:"s"},
      {label:"Via Walk-in", data:a.monthly.map(r=>r.doses_via_walkin), backgroundColor:PALETTE.blue, stack:"s"},
    ]}, options:{...baseBarOpts(), plugins:{legend:{display:true,position:"bottom"}}, scales:{...baseBarOpts().scales, x:{stacked:true,grid:{display:false}}, y:{...baseBarOpts().scales.y, stacked:true}}}});

  mkChart(document.getElementById("chart-appt-noshow"), {type:"line",
    data:{labels:a.monthly.map(r=>r.month), datasets:[{label:"No-Show Rate", data:a.monthly.map(r=>r.no_show_rate_pct), borderColor:PALETTE.gold, tension:0.2}]},
    options:baseLineOpts(false, "%")});
}

// ---------------------------------------------------------------------------
// 8. SAFETY (AEFI)
// ---------------------------------------------------------------------------
function renderSafety(d){
  const a = d.aefi;
  let html = `<div class="kpi-grid">
    ${kpiCard("Total AEFI Reports", fmtNum(a.kpis.total_reports))}
    ${kpiCard("Mild Rate /100k Doses", fmtDec(a.kpis.mild_rate,1), "accent")}
    ${kpiCard("Moderate Rate /100k Doses", fmtDec(a.kpis.moderate_rate,1), "gold")}
    ${kpiCard("Serious Rate /100k Doses", fmtDec(a.kpis.serious_rate,2), "red")}
  </div>
  <div class="grid-2">
    ${card("Reports by Severity", chartWrap("chart-safety-severity","short"))}
    ${card("Severity Reference Table", `<table><thead><tr><th>Severity</th><th>Reports</th><th>Rate / 100k Doses</th></tr></thead><tbody>
      ${a.by_severity.map(r=>`<tr><td>${severityTag(r.severity)}</td><td>${fmtNum(r.report_count)}</td><td>${fmtDec(r.rate_per_100k_doses,2)}</td></tr>`).join("")}
    </tbody></table>`)}
  </div>`;
  document.getElementById("content").innerHTML = html;

  mkChart(document.getElementById("chart-safety-severity"), {type:"doughnut",
    data:{labels:a.by_severity.map(r=>r.severity), datasets:[{data:a.by_severity.map(r=>r.report_count), backgroundColor:[PALETTE.accent,PALETTE.gold,PALETTE.red]}]},
    options:{plugins:{legend:{position:"bottom",labels:{boxWidth:9,font:{size:10}}}}}});
}

// ---------------------------------------------------------------------------
// 9. FORECAST COMPARISON
// ---------------------------------------------------------------------------
function renderForecast(d){
  const f = d.forecast;
  const allMetrics = [...f.multistep_metrics, ...f.onestep_metrics];
  let html = `<div class="kpi-grid">
    ${allMetrics.map(m=>kpiCard(m.model, "R² " + fmtDec(m.R2,3), m.R2 > 0.5 ? "accent" : "red")).join("")}
  </div>
  <div class="grid-2">
    ${card("Multi-step (45-day) Forecast vs. Actual", `<img class="report-fig" src="${d.figures['multistep_forecast_vs_actual.png']||''}">`)}
    ${card("One-step-ahead Forecast vs. Actual", `<img class="report-fig" src="${d.figures['onestep_forecast_vs_actual.png']||''}">`)}
  </div>
  <div class="grid-2">
    ${card("30-Day Future Forecast (SARIMA vs. XGBoost)", chartWrap("chart-fc-future","tall"))}
    ${card("XGBoost Feature Importance", `<img class="report-fig" src="${d.figures['xgboost_feature_importance.png']||''}">`)}
  </div>
  ${card("Full Metrics", `<table><thead><tr><th>Model</th><th>MAE</th><th>RMSE</th><th>MAPE %</th><th>sMAPE %</th><th>R²</th></tr></thead><tbody>
    ${allMetrics.map(m=>`<tr><td>${m.model}</td><td>${fmtDec(m.MAE,1)}</td><td>${fmtDec(m.RMSE,1)}</td><td>${fmtDec(m["MAPE_%"],1)}</td><td>${fmtDec(m["sMAPE_%"],1)}</td><td>${fmtDec(m.R2,3)}</td></tr>`).join("")}
  </tbody></table>`)}`;
  document.getElementById("content").innerHTML = html;

  mkChart(document.getElementById("chart-fc-future"), {type:"line",
    data:{labels:f.future_dates, datasets:[
      {label:"SARIMA Forecast", data:f.sarima_forecast, borderColor:PALETTE.accent, pointRadius:0},
      {label:"SARIMA 95% Upper", data:f.sarima_upper, borderColor:"rgba(14,124,134,0.25)", borderDash:[3,3], pointRadius:0},
      {label:"SARIMA 95% Lower", data:f.sarima_lower, borderColor:"rgba(14,124,134,0.25)", borderDash:[3,3], pointRadius:0, fill:"-1", backgroundColor:"rgba(14,124,134,0.06)"},
      {label:"XGBoost Forecast", data:f.xgboost_forecast, borderColor:PALETTE.red, pointRadius:0},
    ]}, options:baseLineOpts(true)});
}

// ---------------------------------------------------------------------------
// APP SHELL
// ---------------------------------------------------------------------------
const RENDERERS = {
  overview: renderOverview, coverage: renderCoverage, epidemic: renderEpidemic,
  centers: renderCenters, supply: renderSupply, staffing: renderStaffing,
  appointments: renderAppointments, safety: renderSafety, forecast: renderForecast,
};

let currentSection = "overview";

function appendFooter(){
  const el = document.getElementById("content");
  const footer = document.createElement("div");
  footer.className = "footer-author";
  footer.innerHTML = `
    <img src="__AUTHOR_PHOTO__" alt="Milad Shabani">
    <div>
      <div class="name">Built by Milad Shabani</div>
      <div class="role">Business Intelligence · Data Analytics · Data Engineering</div>
      <div class="links"><a href="https://github.com/Milad-Shabani" target="_blank" rel="noopener">GitHub: Milad-Shabani</a></div>
    </div>`;
  el.appendChild(footer);
}

function renderNav(){
  const list = document.getElementById("nav-list");
  list.innerHTML = NAV.map(n=>`<div class="nav-item ${n.id===currentSection?'active':''}" data-id="${n.id}"><span class="nav-dot"></span>${n.label}</div>`).join("");
  list.querySelectorAll(".nav-item").forEach(el=>{
    el.addEventListener("click", ()=>{ currentSection = el.dataset.id; goToSection(currentSection); });
  });
}

function goToSection(id){
  const meta = NAV.find(n=>n.id===id);
  document.getElementById("section-title").innerHTML = meta.label;
  document.getElementById("section-subtitle").innerHTML = meta.sub;
  document.querySelectorAll(".nav-item").forEach(el=>el.classList.toggle("active", el.dataset.id===id));
  destroyCharts();
  RENDERERS[id](DASHBOARD_DATA);
  appendFooter();
}

document.addEventListener("DOMContentLoaded", ()=>{
  renderNav();
  goToSection(currentSection);
});
