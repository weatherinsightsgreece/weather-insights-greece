import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

# ---------------------------
st.set_page_config(layout="wide", page_title="Weather Insights Greece Model")
st.markdown("<h2 style='text-align:left;'>Weather Insights Greece Model</h2>", unsafe_allow_html=True)

# ---------------------------
# Πρωτεύουσες Ευρώπης
capitals = pd.DataFrame({
    "City":["Athens","Berlin","Paris","Rome","Madrid","Lisbon","Warsaw","Vienna","Brussels","Copenhagen","Stockholm","Oslo","Helsinki","Budapest","Prague"],
    "Lat":[37.9838,52.5200,48.8566,41.9028,40.4168,38.7169,52.2297,48.2082,50.8503,55.6761,59.3293,59.9139,60.1699,47.4979,50.0755],
    "Lon":[23.7275,13.4050,2.3522,12.4964,-3.7038,-9.1392,21.0122,16.3738,4.3517,12.5686,18.0686,10.7522,24.9384,19.0402,14.4378]
})

# ---------------------------
# Session state
if 'frame' not in st.session_state: st.session_state.frame = 0
if 'map_type' not in st.session_state: st.session_state.map_type = '850hPa Temperature'
if 'play' not in st.session_state: st.session_state.play = False

# ---------------------------
# Fetch ensemble (placeholder για 3 μοντέλα)
@st.cache_data(ttl=1800)
def fetch_ensemble(lat, lon):
    dfs = []
    for _ in range(3):
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation&timezone=UTC"
        r = requests.get(url)
        data = r.json()
        df = pd.DataFrame({
            "time": pd.to_datetime(data['hourly']['time']),
            "temperature": data['hourly']['temperature_2m'],
            "precipitation": data['hourly']['precipitation']
        })
        dfs.append(df)
    df_ens = dfs[0].copy()
    df_ens['temperature'] = np.mean([df['temperature'] for df in dfs], axis=0)
    df_ens['precipitation'] = np.mean([df['precipitation'] for df in dfs], axis=0)
    df_ens.fillna(0, inplace=True)
    return df_ens

lat_center = capitals['Lat'].mean()
lon_center = capitals['Lon'].mean()
df_weather = fetch_ensemble(lat_center, lon_center)

# ---------------------------
# Sidebar επιλογές
st.sidebar.header("Επιλογές Χρόνου")
hours_list = df_weather['time'].dt.strftime("%Y-%m-%d %H:%M").tolist()
selected_hour = st.sidebar.selectbox("Επιλέξτε ώρα:", hours_list, index=st.session_state.frame)
step_hours = st.sidebar.slider("Βήμα ωρών Next:", min_value=1, max_value=24, value=3, step=1)
st.session_state.frame = hours_list.index(selected_hour)

# ---------------------------
# Κουμπί αλλαγής χάρτη
if st.button("Αλλαγή Χάρτη"):
    st.session_state.map_type = 'Precipitation' if st.session_state.map_type=='850hPa Temperature' else '850hPa Temperature'

# ---------------------------
# Κουμπί Start / Stop
col1, col2 = st.columns(2)
with col1:
    if st.button("Start"):
        st.session_state.play = True
with col2:
    if st.button("Stop"):
        st.session_state.play = False

# ---------------------------
# Next frame αυτόματα
if st.session_state.play:
    st.session_state.frame += step_hours
    if st.session_state.frame >= len(df_weather):
        st.session_state.frame = 0

frame = st.session_state.frame
current_time = df_weather.iloc[frame]['time']

# ---------------------------
# Grid Ευρώπης
lats = np.linspace(35, 70, 100)
lons = np.linspace(-10, 40, 100)
lon_grid, lat_grid = np.meshgrid(lons, lats)

if st.session_state.map_type == '850hPa Temperature':
    # Placeholder temperature data για smooth gradient
    temp_grid = 15 + 10*np.sin(lat_grid/10)*np.cos(lon_grid/10)
    # Custom color scale μόνο με χρώματα
    color_scale = ["#800080", "#00008B", "#ADD8E6", "#90EE90", "#008000", "#FFFF00", "#FFA500", "#FF0000"]
    range_color = [-15, 30]
else:
    temp_grid = np.random.uniform(0,25, size=lat_grid.shape)
    color_scale = ["#ADD8E6","#0000FF","#00008B","#FFC0CB","#800080"]
    range_color = [0,25]

plot_df = pd.DataFrame({
    "lat": lat_grid.flatten(),
    "lon": lon_grid.flatten(),
    "value": temp_grid.flatten()
})

# ---------------------------
# Plot με background map
fig = px.density_mapbox(
    plot_df, lat='lat', lon='lon', z='value', radius=15,
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

st.plotly_chart(fig, use_container_width=True)
st.markdown("<div style='text-align:center; font-size:12px;'>Weather Insights Greece</div>", unsafe_allow_html=True)


















