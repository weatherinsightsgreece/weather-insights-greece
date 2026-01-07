import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
from time import sleep

st.set_page_config(layout="wide", page_title="Weather Insights Greece Model")
st.title("Weather Insights Greece Model")

# ---------------------------------------------------------------------------
# Πρωτεύουσες Ευρώπης
capitals = pd.DataFrame({
    "City":["Athens","Berlin","Paris","Rome","Madrid","Lisbon","Warsaw","Vienna","Brussels","Copenhagen","Stockholm","Oslo","Helsinki","Budapest","Prague"],
    "Lat":[37.9838,52.5200,48.8566,41.9028,40.4168,38.7169,52.2297,48.2082,50.8503,55.6761,59.3293,59.9139,60.1699,47.4979,50.0755],
    "Lon":[23.7275,13.4050,2.3522,12.4964,-3.7038,-9.1392,21.0122,16.3738,4.3517,12.5686,18.0686,10.7522,24.9384,19.0402,14.4378]
})

# ---------------------------------------------------------------------------
# Session state
if 'frame' not in st.session_state: st.session_state.frame = 0
if 'map_type' not in st.session_state: st.session_state.map_type = '850hPa Temperature'
if 'ensemble_data' not in st.session_state: st.session_state.ensemble_data = None

# ---------------------------------------------------------------------------
# Sidebar options
st.sidebar.header("Επιλογές Χρόνου")
step_hours = st.sidebar.slider("Βήμα ωρών Next:", 1, 24, 3)

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Start"):
        st.session_state.play = True
with col2:
    if st.button("Stop"):
        st.session_state.play = False

if st.sidebar.button("Αλλαγή Χάρτη"):
    st.session_state.map_type = (
        'Precipitation' if st.session_state.map_type=='850hPa Temperature'
        else '850hPa Temperature'
    )

# ---------------------------------------------------------------------------
# Build grid for Europe
lat_min, lat_max = 35, 70
lon_min, lon_max = -10, 40
n_lat, n_lon = 20, 30  # μικρότερο grid για λιγότερες κλήσεις
lats = np.linspace(lat_min, lat_max, n_lat)
lons = np.linspace(lon_min, lon_max, n_lon)

# ---------------------------------------------------------------------------
# Function: Fetch ensemble from Open‑Meteo for one coordinate
def fetch_ensemble_point(lat, lon, forecast_days=5):
    """
    Καλεί το Open‑Meteo Ensemble API για ένα σημείο
    και επιστρέφει hourly ensemble forecast arrays.
    """
    url = (
        "https://api.open-meteo.com/v1/ensemble?"
        f"latitude={lat}&longitude={lon}"
        "&models=ecmwf_ifs04,gfs_ensem,icon_seamless"
        f"&hourly=temperature_2m,precipitation"
        f"&forecast_days={forecast_days}"
        "&timezone=UTC"
    )
    r = requests.get(url)
    sleep(0.1)  # Πολιτική rate limiting
    if not r.ok:
        return None
    return r.json()

# ---------------------------------------------------------------------------
# Load ensemble data if not loaded
if st.session_state.ensemble_data is None:
    st.info("Κατεβάζοντας ensemble δεδομένα για grid Ευρώπης — αυτό μπορεί να πάρει λίγο...")
    all_data = {}
    for lat in lats:
        for lon in lons:
            # key για κάθε grid
            key = f"{lat:.2f}_{lon:.2f}"
            data = fetch_ensemble_point(lat, lon)
            if data:
                all_data[key] = data
    st.session_state.ensemble_data = all_data
    st.success("Ensemble δεδομένα φορτώθηκαν")

ensemble = st.session_state.ensemble_data

# ---------------------------------------------------------------------------
# Prepare frames
times = list(next(iter(ensemble.values()))['hourly']['time'])
n_times = len(times)

if 'play' not in st.session_state:
    st.session_state.play = False

if st.session_state.play:
    st.session_state.frame = (st.session_state.frame + step_hours) % n_times

frame = st.session_state.frame
current_time = times[frame]

# ---------------------------------------------------------------------------
# Build heatmap grid for this frame
value_grid = np.zeros((n_lat, n_lon))
lower_grid = np.zeros((n_lat, n_lon))
upper_grid = np.zeros((n_lat, n_lon))

for i,lat in enumerate(lats):
    for j,lon in enumerate(lons):
        key = f"{lat:.2f}_{lon:.2f}"
        point = ensemble.get(key)
        if not point: continue
        # temperature ensemble members list-of-lists
        temp_ens = point['hourly']['temperature_2m'][frame]
        precip_ens = point['hourly']['precipitation'][frame]
        # mean + percentiles
        if st.session_state.map_type=='850hPa Temperature':
            arr = np.array(temp_ens)
        else:
            arr = np.array(precip_ens)
        value_grid[i,j] = np.mean(arr)
        lower_grid[i,j] = np.percentile(arr,20)
        upper_grid[i,j] = np.percentile(arr,80)

plot_df = pd.DataFrame({
    "lat": lat_grid.flatten(),
    "lon": lon_grid.flatten(),
    "value": value_grid.flatten(),
    "lower": lower_grid.flatten(),
    "upper": upper_grid.flatten()
})

# ---------------------------------------------------------------------------
# Color scales
if st.session_state.map_type == '850hPa Temperature':
    color_scale = ["#800080","#00008B","#ADD8E6","#90EE90","#008000","#FFFF00","#FFA500","#FF0000"]
    range_color = [-20,30]
else:
    color_scale = ["#ADD8E6","#0000FF","#00008B","#FFC0CB","#800080"]
    range_color = [0,30]

fig = px.density_mapbox(
    plot_df, lat="lat", lon="lon", z="value", radius=10,
    center=dict(lat=55, lon=10), zoom=3,
    mapbox_style="carto-positron",
    color_continuous_scale=color_scale,
    range_color=range_color,
    opacity=0.6
)

# add capital cities
for _,r in capitals.iterrows():
    fig.add_scattermapbox(
        lat=[r["Lat"]], lon=[r["Lon"]],
        mode="markers+text",
        text=[r["City"]], textposition="top center",
        marker=dict(size=10,color="black")
    )

fig.update_layout(
    title=f"{st.session_state.map_type} - {current_time} | Weather Insights Greece Model",
    margin={"r":0,"t":50,"l":0,"b":0}
)
st.plotly_chart(fig, use_container_width=True)




















