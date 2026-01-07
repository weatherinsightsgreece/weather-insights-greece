import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

st.set_page_config(layout="wide", page_title="Weather Insights Greece Model")
st.markdown("<h2 style='text-align:left;'>Weather Insights Greece Model</h2>", unsafe_allow_html=True)

# Πρωτεύουσες Ευρώπης
capitals = pd.DataFrame({
    "City":["Athens","Berlin","Paris","Rome","Madrid","Lisbon","Warsaw","Vienna","Brussels","Copenhagen","Stockholm","Oslo","Helsinki","Budapest","Prague"],
    "Lat":[37.9838,52.5200,48.8566,41.9028,40.4168,38.7169,52.2297,48.2082,50.8503,55.6761,59.3293,59.9139,60.1699,47.4979,50.0755],
    "Lon":[23.7275,13.4050,2.3522,12.4964,-3.7038,-9.1392,21.0122,16.3738,4.3517,12.5683,18.0686,10.7522,24.9384,19.0402,14.4378]
})

# Φόρτωση δεδομένων
@st.cache_data(ttl=1800)
def fetch_weather():
    lat = capitals['Lat'].mean()
    lon = capitals['Lon'].mean()
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation&timezone=UTC"
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame({
        "time": pd.to_datetime(data['hourly']['time']),
        "temperature": data['hourly']['temperature_2m'],
        "precipitation": data['hourly']['precipitation']
    })
    return df

df_weather = fetch_weather()

# Session state για animation
if 'frame' not in st.session_state:
    st.session_state.frame = 0
if 'play' not in st.session_state:
    st.session_state.play = False

# Start / Stop κουμπιά
col1, col2 = st.columns(2)
if col1.button("Start"):
    st.session_state.play = True
if col2.button("Stop"):
    st.session_state.play = False

# Αυτόματο loop χωρίς rerun
if st.session_state.play:
    st_autorefresh(interval=1500, key="timer")  # Ανανεώνει κάθε 1.5 δευτερόλεπτο
    st.session_state.frame += 3
    if st.session_state.frame >= len(df_weather):
        st.session_state.frame = 0

frame = st.session_state.frame
current_time = df_weather.iloc[frame]['time']

# Χρώματα θερμοκρασίας
def temp_color(t):
    if t<-10: return "purple"
    elif -9<=t<=-5: return "darkblue"
    elif -4<=t<=0: return "lightblue"
    elif 1<=t<=5: return "lightgreen"
    elif 6<=t<=10: return "green"
    elif 11<=t<=15: return "yellow"
    elif 16<=t<=20: return "orange"
    else: return "red"

capitals_plot = capitals.copy()
capitals_plot['Temp'] = df_weather.iloc[frame]['temperature']
capitals_plot['Precip'] = df_weather.iloc[frame]['precipitation']

# Δημιουργία charts side-by-side
col_map1, col_map2 = st.columns(2)

# 850hPa Temperature
fig1 = px.scatter_geo(capitals_plot, lat='Lat', lon='Lon', text='City', color='Temp',
                      color_continuous_scale=["purple","darkblue","lightblue","lightgreen","green","yellow","orange","red"],
                      range_color=[-20,35], projection="natural earth", scope="europe")
fig1.update_layout(title=f"850hPa Temperature - {current_time.strftime('%Y-%m-%d %H:%M UTC')}",
                   geo=dict(showland=True, landcolor="lightgrey"), margin={"r":0,"t":50,"l":0,"b":0})
col_map1.plotly_chart(fig1, use_container_width=True)

# Υετός
fig2 = px.scatter_geo(capitals_plot, lat='Lat', lon='Lon', text='City', color='Precip',
                      color_continuous_scale=["lightblue","blue","darkblue","pink","purple"],
                      range_color=[0,30], projection="natural earth", scope="europe")
fig2.update_layout(title=f"Precipitation - {current_time.strftime('%Y-%m-%d %H:%M UTC')}",
                   geo=dict(showland=True, landcolor="lightgrey"), margin={"r":0,"t":50,"l":0,"b":0})
col_map2.plotly_chart(fig2, use_container_width=True)

# Footer
st.markdown("<div style='text-align:center; font-size:12px;'>Weather Insights Greece</div>", unsafe_allow_html=True)






