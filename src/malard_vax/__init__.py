"""
Malard VaxForecast
===================
A synthetic, research/portfolio-grade dataset and forecasting toolkit
for COVID-19 vaccination operations at a district health network,
modeled on Malard County, Tehran Province, Iran.

NOTE ON DATA PROVENANCE
------------------------
This project ships **synthetic** data. Vaccination throughput and
per-center figures are simulated to follow a realistic operational
pattern (slow start -> ramp-up -> peak -> plateau -> decline) as
described in the project brief. Daily confirmed-case counts are
**modeled**, not sourced from an official county-level registry
(granular daily case data at the county level is not publicly
published in machine-readable form for this period). The case curve
is calibrated to match the *documented, published* national epidemic
timeline for Iran during this window - the Delta-driven fifth wave
(peaked mid-August 2021) and the Omicron-driven sixth wave (began
late December 2021, accelerated through January-February 2022) -
scaled down to a plausible county population. See
`docs/data_dictionary.md` for full details and sources.

Nothing in this repository should be treated as an official
epidemiological or health-system record.
"""

__version__ = "1.0.0"
