# Solar PV Uptake by LSOA

This project analyses Solar PV uptake at LSOA level, combining geospatial connection data with population statistics to identify areas with high solar potential but low adoption.

## Files
- `processing.ipynb` — Cleans and aggregates Solar PV connection data, computes uptake and priority metrics, and outputs data csv.
- `model_table.csv` — Processed LSOA-level dataset used by the dashboard (solar uptake, potential, categories, and priority score).
- `app.py` — Streamlit dashboard for interactively exploring Solar PV uptake, potential, and priority areas.
