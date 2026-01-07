import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests

st.set_page_config(layout="wide", page_title="Weather Insights Greece Model")
st.title("Weather Insights Greece Model")

# ---------------------------
# Πρωτεύουσες Ευρώπης
capitals = pd.DataFrame({
    "City":["Athens","Berlin","Paris","Rome","Madrid","Lisbon","Warsaw","Vienna","Brussels","Copenhagen","Stockholm","Oslo","Helsinki","Budapest","Prague"],
    "Lat":[37.9838,52.5200,48.8566,41.9028,40.4168,38.7169,52.2297,48.2082,50.8503,55.6761,59.3293,59.9139,60.1699,47.4979,50.0755],
    "Lon":[23.7275,13.4050,2.3522,12.4964,-3.7038,-9.1392,21.0122,16.3738,4.3517,12.5686,18.0686,10.7522,24.9384,19.0402,14.4378]
})

# ---------------------------
# Session State
if 'frame' not in st.session_state: st.session_state.frame = 0
if 'map_type' not in st.session_state: st.session_state.map_type = '850hPa Temperature'
if 'play' not in st.session_state: st.session_state.play = False

# ---------------------------
# Ευρωπαϊκό Grid (latitude / longitude)
lat_min, lat_max = 35, 70
lon_min, lon_max = -10, 40
n_lat, n_lon = 60, 80
lats = np.linspace(lat_min, lat_max, n_lat)
lons = np.linspace(lon_min, lon_max, n_lon)
lon_grid, lat_grid = np.meshgrid(lons, lats)

# ---------------------------
# Dummy Ensemble Function (αντικαταστήστε με Open-Meteo API)
@st.cache_data(ttl=1800)
def fetch_ensemble_data():
    times = [datetime.utcnow() + timedelta(hours=3*i) for i in range(40)]  # 5 μέρες, 3h step
    n_times = len(times)
    temp_members = np.random.uniform(-10,30,(5,n_lat,n_lon,n_times))  # 5 ensemble μέλη
    precip_members = np.random.uniform(0,25,(5,n_lat,n_lon,n_times))
    return times, temp_members, precip_members

times, temp_members, precip_members = fetch_ensemble_data()
n_times = len(times)

# ---------------------------
# Sidebar επιλογές
st.sidebar.header("Επιλογές Χρόνου")
frame_slider = st.sidebar.slider("Επιλέξτε frame:", 0, n_times-1, st.session_state.frame)
st.session_state.frame = frame_slider

step_hours = st.sidebar.slider("Βήμα ωρών Next:", 1, 24, 3)

# ---------------------------
# Κουμπί αλλαγής χάρτη
if st.sidebar.button("Αλλαγή Χάρτη"):
    st.session_state.map_type = 'Precipitation' if st.session_state.map_type=='850hPa Temperature' else '850hPa Temperature'

# ---------------------------
# Start / Stop
col1, col2 = st.columns(2)
with col1:
    if st.button("Start"):
        st.session_state.play = True
with col2:
    if st.button("Stop"):
        st.session_state.play = False

# ---------------------------
# Αυτοματη κίνηση
if st.session_state.play:
    st.session_state.frame += step_hours
    if st.session_state.frame >= n_times:
        st.session_state.frame = 0

frame = st.session_state.frame
current_time = times[frame]

# ---------------------------
# Υπολογισμός ensemble mean & percentiles
if st.session_state.map_type == '850hPa Temperature':
    data = temp_members[:,:,:,frame]
    value = np.mean(data, axis=0)
    lower = np.percentile(data,20,axis=0)
    upper = np.percentile(data,80,axis=0)
    color_scale = ["#800080", "#00008B", "#ADD8E6", "#90EE90", "#008000", "#FFFF00", "#FFA500", "#FF0000"]
    range_color = [-15,30]
else:
    data = precip_members[:,:,:,frame]
    value = np.mean(data, axis=0)
    lower = np.percentile(data,20,axis=0)
    upper = np.percentile(data,80,axis=0)
    color_scale = ["#ADD8E6","#0000FF","#00008B","#FFC0CB","#800080"]
    range_color = [0,25]

plot_df = pd.DataFrame({
    "lat": lat_grid.flatten(),
    "lon": lon_grid.flatten(),
    "value": value.flatten(),
    "lower": lower.flatten(),
    "upper": upper.flatten()
})

# ---------------------------
# Plotly Density Mapbox
fig = px.density_mapbox(
    plot_df, lat='lat', lon='lon', z='value', radius=10,
    center=dict(lat=55, lon=10), zoom=3,
    mapbox_style="carto-positron",
    color_continuous_scale=color_scale,
    opacity=0.6,
    range_color=range_color
)

# Προσθήκη πρωτευουσών
for i,row in capitals.iterrows():
    fig.add_scattermapbox(
        lat=[row['Lat']], lon=[row['Lon']], mode='markers+text',
        marker=dict(size=10,color='black'),
        text=[row['City']], textposition="top center"
    )

# Header
fig.update_layout(
    title=f"{st.session_state.map_type} - {current_time.strftime('%Y-%m-%d %H:%M UTC')} | Weather Insights Greece Model",
    margin={"r":0,"t":50,"l":0,"b":0},
    height=700
)

# ---------------------------
st.plotly_chart(fig, use_container_width=True)
st.markdown("<div style='text-align:center; font-size:12px;'>Weather Insights Greece</div>", unsafe_allow_html=True)



















