import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Weather Insights Greece Model")

st.title("Weather Insights Greece Model")

# --- Πρωτεύουσες Ευρώπης ---
capitals = pd.DataFrame({
    "City":["Athens","Berlin","Paris","Rome","Madrid","Lisbon","Warsaw","Vienna","Brussels","Copenhagen","Stockholm","Oslo","Helsinki","Budapest","Prague"],
    "Lat":[37.9838,52.5200,48.8566,41.9028,40.4168,38.7169,52.2297,48.2082,50.8503,55.6761,59.3293,59.9139,60.1699,47.4979,50.0755],
    "Lon":[23.7275,13.4050,2.3522,12.4964,-3.7038,-9.1392,21.0122,16.3738,4.3517,12.5683,18.0686,10.7522,24.9384,19.0402,14.4378]
})

# --- Επιλογή map ---
map_choice = st.selectbox("Διάλεξε Χάρτη:", ["850hPa Temperature", "Precipitation"])

# --- Ανάκτηση δεδομένων από Open-Meteo ---
def fetch_weather():
    # Κατεβάζουμε forecast 5 ημερών για Ευρώπη (approx mid-point)
    lats = capitals['Lat'].mean()
    lons = capitals['Lon'].mean()
    start = datetime.utcnow()
    end = start + timedelta(days=5)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lats}&longitude={lons}&hourly=temperature_2m,precipitation&timezone=UTC"
    r = requests.get(url)
    data = r.json()
    times = data['hourly']['time']
    temp = data['hourly']['temperature_2m']
    precip = data['hourly']['precipitation']
    df = pd.DataFrame({"time": times, "temperature": temp, "precipitation": precip})
    df['time'] = pd.to_datetime(df['time'])
    return df

df_weather = fetch_weather()

# --- Animation ---
st.write("Παίξε την πρόβλεψη (3 ώρες ανά frame)")
start_btn, stop_btn = st.columns(2)
if start_btn.button("Start"):
    st.session_state['play'] = True
if stop_btn.button("Stop"):
    st.session_state['play'] = False

if 'play' not in st.session_state:
    st.session_state['play'] = False

# --- Επιλογή frame ---
frame = 0
if st.session_state['play']:
    import time
    for i in range(0, len(df_weather), 3):
        frame = i
        st.session_state['play'] = True
        time.sleep(1.5)
        st.experimental_rerun()

current_time = df_weather.iloc[frame]['time']

# --- Χρώματα θερμοκρασίας ---
def temp_color(t):
    if t<-10: return "purple"
    elif -9<=t<=-5: return "darkblue"
    elif -4<=t<=0: return "lightblue"
    elif 1<=t<=5: return "lightgreen"
    elif 6<=t<=10: return "green"
    elif 11<=t<=15: return "yellow"
    elif 16<=t<=20: return "orange"
    else: return "red"

# --- Plot ---
if map_choice=="850hPa Temperature":
    capitals['Temp'] = df_weather.iloc[frame]['temperature']
    capitals['Color'] = capitals['Temp'].apply(temp_color)
    fig = px.scatter_geo(capitals, lat='Lat', lon='Lon', text='City', color='Temp',
                         color_continuous_scale=["purple","darkblue","lightblue","lightgreen","green","yellow","orange","red"],
                         range_color=[-20,35], projection="natural earth", scope="europe")
else:
    capitals['Precip'] = df_weather.iloc[frame]['precipitation']
    fig = px.scatter_geo(capitals, lat='Lat', lon='Lon', text='City', color='Precip',
                         color_continuous_scale=["lightblue","blue","darkblue","pink","purple"],
                         range_color=[0,30], projection="natural earth", scope="europe")

fig.update_layout(
    title=f"Weather Insights Greece Model - {current_time.strftime('%Y-%m-%d %H:%M UTC')}",
    geo=dict(showland=True, landcolor="lightgrey"),
    margin={"r":0,"t":50,"l":0,"b":0}
)

st.plotly_chart(fig, use_container_width=True)

