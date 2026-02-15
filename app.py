import pandas as pd
import streamlit as st
import pydeck as pdk

# -----------------------
# CONFIG
# -----------------------
MODEL_PATH = "data/model_table.csv"
MAP_HEIGHT_PX = 560
TABLE_HEIGHT_PX = 500

st.set_page_config(page_title="UKPN Solar PV: Mapping Untapped Potential", layout="wide")

st.title("UKPN Solar PV: Mapping Untapped Potential")
st.caption(
    "Screening tool to identify areas with high solar potential but low uptake, "
    "using Solar PV connections per 1,000 population and a latitude-based proxy for solar potential."
)

# -----------------------
# LOAD DATA
# -----------------------
def load_model(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    for col in ["lsoa_code", "lsoa_name", "category"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    for col in [
        "latitude", "longitude",
        "solar_connections", "population",
        "solar_per_1000_pop", "potential_lat_score",
        "priority_score"
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["latitude", "longitude"]).copy()
    df = df[df["latitude"].between(48, 61) & df["longitude"].between(-9, 3)].copy()
    return df

df = load_model(MODEL_PATH)

# -----------------------
# STABLE PRIORITY NORMALISATION (PERCENTILE, GLOBAL)
# -----------------------
# Percentile rank gives a better spread than min-max scaling
p = df["priority_score"].astype(float)
p_pct = p.rank(pct=True)  # 0..1
PRIORITY_PCT = dict(zip(df["lsoa_code"], p_pct))

# -----------------------
# SIDEBAR FILTERS
# -----------------------
with st.sidebar:
    st.header("Filters")

    preferred_order = [
        "High potential / Low uptake (PRIORITY)",
        "High potential / High uptake",
        "Low potential / High uptake",
        "Low potential / Low uptake",
    ]
    present = set(df["category"].dropna().unique().tolist())
    cats = [c for c in preferred_order if c in present] + sorted(list(present - set(preferred_order)))

    chosen = st.multiselect("Category", cats, default=cats)

    min_pop = st.slider("Minimum population", 0, int(df["population"].max()), 0, step=100)
    max_points = st.slider("Max points on map (performance)", 500, 20000, 16500, step=500)
    top_n = st.slider("Top-N priority table", 10, 200, 50, step=10)

    st.markdown("---")
    st.subheader("Colour tuning")
    gamma = st.slider("Sensitivity (gamma)", 0.4, 2.5, 1.5, 0.1)
    # gamma < 1 -> more contrast in the middle/high end
    # gamma > 1 -> more contrast near low end

filtered = df[(df["category"].isin(chosen)) & (df["population"] >= min_pop)].copy()

# -----------------------
# SUMMARY METRICS
# -----------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("LSOAs in view", f"{len(filtered):,}")
c2.metric("Median uptake (per 1k pop)", f"{filtered['solar_per_1000_pop'].median():.2f}")
c3.metric("Median potential score", f"{filtered['potential_lat_score'].median():.3f}")
c4.metric("Priority LSOAs", f"{(filtered['category'] == 'High potential / Low uptake (PRIORITY)').sum():,}")

st.markdown("---")

left, right = st.columns([1.4, 1])

# -----------------------
# MAP
# -----------------------
with left:
    st.subheader("Solar under-utilisation per LSOA")
    st.caption("LSOA centroids. Colour shows priority percentile.")

    show = filtered.sort_values("priority_score", ascending=False).head(max_points).copy()

    if show.empty:
        st.warning("No data to display for the selected filters.")
    else:
        # Priority percentile (global) so colours stay consistent when filtering
        show["p"] = show["lsoa_code"].map(PRIORITY_PCT).fillna(0.5).clip(0, 1)

        # Apply gamma curve for sensitivity control
        show["pg"] = show["p"] ** gamma

        # ---- Diverging palette: Blue -> Yellow -> Red ----
        # Piecewise linear interpolation:
        # 0.0: blue (0, 90, 255)
        # 0.5: yellow (255, 225, 0)
        # 1.0: red (230, 57, 70)

        def interp(a, b, t):
            return a + (b - a) * t

        r = []
        g = []
        b = []

        for v in show["pg"].tolist():
            if v <= 0.5:
                t = v / 0.5
                r.append(int(interp(0, 255, t)))
                g.append(int(interp(90, 225, t)))
                b.append(int(interp(255, 0, t)))
            else:
                t = (v - 0.5) / 0.5
                r.append(int(interp(255, 230, t)))
                g.append(int(interp(225, 57, t)))
                b.append(int(interp(0, 70, t)))

        show["r"] = r
        show["g"] = g
        show["b"] = b

        view_state = pdk.ViewState(
            latitude=float(show["latitude"].mean()),
            longitude=float(show["longitude"].mean()),
            zoom=6
        )

        layer = pdk.Layer( 
            "ScatterplotLayer",
            data=show,
            get_position="[longitude, latitude]",
            get_radius=200,
            radius_min_pixels=3,
            radius_max_pixels=35,
            pickable=True,
            opacity=0.85,
            get_fill_color="[r, g, b, 180]",
        )

        tooltip = {
    "html": """
    <b>{lsoa_name}</b><br/>
    <b>LSOA:</b> {lsoa_code}<br/>
    <hr style="margin:4px 0"/>
    <b>Solar PV connections:</b> {solar_connections}<br/>
    <b>Population:</b> {population}<br/>
    <b>Uptake:</b> {solar_per_1000_pop} per 1,000<br/>
    <hr style="margin:4px 0"/>
    <b>Potential score (latitude proxy):</b> {potential_lat_score}<br/>
    <b>Priority score:</b> {priority_score}<br/>
    <b>Category:</b> {category} 
    """
}

        st.pydeck_chart(
            pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip, height=MAP_HEIGHT_PX),
            use_container_width=True
        )

        st.markdown("**Legend:** 🔵 low priority → 🟡 medium → 🔴 high priority")

# -----------------------
# TABLE
# -----------------------
with right:
    st.subheader("Highest-priority LSOAs")
    st.caption("Ranked by priority score.")

    pr = filtered.sort_values("priority_score", ascending=False).head(top_n)

    st.dataframe(
        pr[
            [
                "lsoa_code", "lsoa_name", "category",
                "solar_connections", "population",
                "solar_per_1000_pop", "potential_lat_score",
                "priority_score"
            ]
        ],
        use_container_width=True,
        hide_index=True,
        height=TABLE_HEIGHT_PX
    )

st.markdown("---")

# -----------------------
# RELATIONSHIPS
# -----------------------
st.subheader("Quick relationships")
cc1, cc2 = st.columns(2)

with cc1:
    st.caption("Latitude-based potential vs. solar PV uptake")
    st.scatter_chart(
        filtered.dropna(subset=["potential_lat_score", "solar_per_1000_pop"]),
        x="potential_lat_score",
        y="solar_per_1000_pop"
    )

    st.caption(
    "Interpretation: There is no strong relationship between latitude-based solar potential and current solar PV uptake. "
    "Areas with similar potential often show very different adoption levels."
)

with cc2:
    st.caption("Distribution of solar PV uptake (connections per 1k population)")
    st.bar_chart(filtered["solar_per_1000_pop"])

    st.caption(
    "Interpretation: Solar PV uptake is highly uneven across LSOAs, with most areas showing very low adoption "
    "and a small number of locations accounting for much higher uptake."
)