# Solar PV Uptake by LSOA

This project analyses Solar PV uptake at LSOA level, combining geospatial connection data with population statistics to identify areas with high solar potential but low adoption. The aim is to provide an exploratory screening tool to support network planning and discussion around where future Solar PV connections may be most impactful.

## Method overview
1. **Data preparation**
   - Solar PV connection data is extracted from a GeoJSON of UKPN LCT connections.
   - Geometries are reduced to LSOA centroids, with coordinates transformed to WGS84 where required.
   - Data is filtered to retain only Solar PV connections and aggregated to LSOA level.

2. **Normalising uptake**
   - Solar PV uptake is calculated as the number of Solar PV connections per 1,000 residents, using census population data.
   - This enables comparison between LSOAs of different sizes.

3. **Solar potential proxy**
   - Latitude is used as a simple proxy for solar potential, reflecting the broad north–south gradient in solar irradiance.
   - A relative potential score is derived by scaling latitude between observed minimum and maximum values.

4. **Prioritisation logic**
   - Median values of uptake and potential are used to classify LSOAs into four priority categories.
   - A continuous priority score is calculated by standardising (z-scoring) potential and uptake and combining them so that higher potential increases priority while higher existing uptake reduces it.

5. **Visualisation**
   - Results are explored through an interactive Streamlit dashboard with a map and ranked priority table.

## Limitations
- Latitude is a coarse proxy for solar potential and does not capture local factors such as roof orientation, shading, building height, or urban form.
- Median-based classification simplifies prioritisation and may exaggerate broad regional patterns (e.g. much of the north appearing lower priority).
- Aggregation at LSOA level may mask within-area variation.
- Analysis is exploratory and heuristic rather than predictive or causal.

## Future opportunities
- Incorporate richer measures of solar suitability (e.g. roof area, orientation, building type, land use).
- Integrate socio-economic variables such as tenure, income, and housing type to better understand adoption constraints.
- Extend prioritisation logic beyond medians using continuous thresholds or optimisation-based approaches.
- Link analysis to local authority boundaries to support targeted outreach, investment, or coordination with planning teams.

## Files
- `processing.ipynb` — Cleans and aggregates Solar PV connection data and computes uptake, potential, and priority metrics.
- `model_table.csv` — Processed LSOA-level dataset used by the dashboard (solar uptake, potential, categories, and priority score).
- `app.py` — Streamlit dashboard for interactively exploring Solar PV uptake, potential, and priority areas.
