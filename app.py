import streamlit as st
import pandas as pd
import numpy as np
import xarray as xr
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
# Fetch GFS / ICON via Open-Meteo (safe for Streamlit)
@st.cache_data(ttl=1800)
def fetch_gfs(lat, lon):
    url = f"https://api.open-meteo.com/v1/gfs?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation&timezone=UTC"
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame({
        "time": pd.to_datetime(data['hourly']['time']),
        "temperature": data['hourly']['temperature_2m'],
        "precipitation": data['hourly']['precipitation']
    })
    df.fillna(0, inplace=True)
    return df

lat_center = capitals['Lat'].mean()
lon_center = capitals['Lon'].mean()
df_weather = fetch_gfs(lat_center, lon_center)

# ---------------------------
# Session state
if 'frame' not in st.session_state: st.session_state.frame = 0
if 'map_type' not in st.session_state: st.session_state.map_type = '850hPa Temperature'

# ---------------------------
# Sidebar επιλογές
st.sidebar.header("Επιλογές Χρόνου")
hours_list = df_weather['time'].dt.strftime("%Y-%m-%d %H:%M").tolist()
selected_hour = st.sidebar.selectbox("Επιλέξτε ώρα:", hours_list, index=st.session_state.frame)
step_hours = st.sidebar.slider("Πόσες ώρες να προχωρήσει με το Next:", min_value=1, max_value=24, value=3, step=1)
st.session_state.frame = hours_list.index(selected_hour)

# ---------------------------
# Κουμπί αλλαγής χάρτη
if st.button("Αλλαγή Χάρτη"):
    st.session_state.map_type = 'Precipitation' if st.session_state.map_type=='850hPa Temperature' else '850hPa Temperature'

# ---------------------------
# Κουμπί Next frame
if st.button(f"Next (+{step_hours} ώρες)"):
    st.session_state.frame += step_hours
    if st.session_state.frame >= len(df_weather):
        st.session_state.frame = 0

frame = st.session_state.frame
current_time = df_weather.iloc[frame]['time']

# ---------------------------
# Δημιουργία smooth grid για heatmap
lats = np.linspace(35, 60, 50)
lons = np.linspace(-10, 30, 50)
lon_grid, lat_grid = np.meshgrid(lons, lats)

if st.session_state.map_type == '850hPa Temperature':
    # interpolate temperature αερίων μαζών
    temp_value = df_weather.iloc[frame]['temperature']
    temp_grid = 15 + 10*np.sin(lat_grid/10)*np.cos(lon_grid/10)  # placeholder για smooth gradient
else:
    temp_value = df_weather.iloc[frame]['precipitation']
    temp_grid = np.random.uniform(0,20, size=lat_grid.shape)  # placeholder για smooth precipitation

# Flatten για Plotly
plot_df = pd.DataFrame({
    "lat": lat_grid.flatten(),
    "lon": lon_grid.flatten(),
    "value": temp_grid.flatten()
})

# ---------------------------
# Plot με gradient
fig = px.density_mapbox(
    plot_df, lat='lat', lon='lon', z='value', radius=20,
    center=dict(lat=50, lon=10), zoom=3,
    mapbox_style="carto-positron",
    color_continuous_scale="Turbo" if st.session_state.map_type=='850hPa Temperature' else "Blues",
    range_color=[plot_df['value'].min(), plot_df['value'].max()]
)

# Προσθήκη πρωτευουσών
for i,row in capitals.iterrows():
    fig.add_scattermapbox(
        lat=[row['Lat']], lon=[row['Lon']], mode='markers+text',
        marker=dict(size=10,color='black'),
        text=[row['City']], textposition="top center"
    )

# Title με ώρα + όνομα μοντέλου
fig.update_layout(
    title=f"{st.session_state.map_type} - {current_time.strftime('%Y-%m-%d %H:%M UTC')} | Weather Insights Greece Model",
    margin={"r":0,"t":50,"l":0,"b":0},
    height=700
)

st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("<div style='text-align:center; font-size:12px;'>Weather Insights Greece</div>", unsafe_allow_html=True)
















