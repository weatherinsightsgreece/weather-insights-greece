import streamlit as st
import xarray as xr
from siphon.catalog import TDSCatalog
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time

# ---------------------
# Ρυθμίσεις σελίδας
# ---------------------
st.set_page_config(layout="wide")
st.title("Weather Insights Greece Model")

# ---------------------
# Περιοχή Ευρώπης
# ---------------------
lat_slice = slice(72, 34)
lon_slice = slice(-10, 40)

# ---------------------
# Φόρτωση δεδομένων με cache και TTL (auto-refresh)
# ---------------------
@st.cache_data(ttl=1800)  # ανανέωση κάθε 30 λεπτά
def load_data():
    # GFS
    gfs_catalog = TDSCatalog("https://thredds.ucar.edu/thredds/catalog/grib/NCEP/GEFS/Global_0p25deg/catalog.xml")
    gfs_ds = list(gfs_catalog.datasets.values())[0]
    gfs = xr.open_dataset(gfs_ds.access_urls['OPENDAP'])
    gfs850 = gfs['Temperature_isobaric'].sel(isobaric=85000) - 273.15
    gfs850 = gfs850.sel(latitude=lat_slice, longitude=lon_slice)
    gfs_precip = gfs['Total_precipitation_surface'].sel(latitude=lat_slice, longitude=lon_slice)

    # ICON
    icon_catalog = TDSCatalog("https://thredds.ucar.edu/thredds/catalog/grib/DWD/ICON-EU/icon-eu-0p0625deg/catalog.xml")
    icon_ds = list(icon_catalog.datasets.values())[0]
    icon = xr.open_dataset(icon_ds.access_urls['OPENDAP'])
    icon850 = icon['Temperature_isobaric'].sel(isobaric=85000) - 273.15
    icon850 = icon850.sel(latitude=lat_slice, longitude=lon_slice)

    # Multi-model median
    median_temp = (gfs850.median(dim='ensemble') + icon850.median(dim='ensemble')) / 2

    return median_temp, gfs_precip, gfs850.time.values

median_temp, precip, time_values = load_data()
lon = median_temp.longitude.values
lat = median_temp.latitude.values
frames = min(40, len(median_temp.time))

# ---------------------
# Πρωτεύουσες Ευρώπης
# ---------------------
capitals = {
    'Αθήνα':[37.98,23.72], 'Βιέννη':[48.21,16.37], 'Βρυξέλλες':[50.85,4.35],
    'Σόφια':[42.70,23.32], 'Βερολίνο':[52.52,13.40], 'Βουδαπέστη':[47.50,19.04],
    'Κοπεγχάγη':[55.68,12.57], 'Παρίσι':[48.85,2.35], 'Λισαβόνα':[38.72,-9.13],
    'Λονδίνο':[51.51,-0.13], 'Ρώμη':[41.90,12.50], 'Μαδρίτη':[40.42,-3.70],
    'Στοκχόλμη':[59.33,18.07], 'Ταλίν':[59.44,24.75], 'Ελσίνκι':[60.17,24.94],
    'Βαρσοβία':[52.23,21.01], 'Μπρατισλάβα':[48.15,17.11], 'Λουξεμβούργο':[49.61,6.13],
    'Μάλτα':[35.89,14.51], 'Σαράγεβο':[43.85,18.36], 'Βελιγράδι':[44.82,20.46],
    'Σκόπια':[41.99,21.43], 'Τίρανα':[41.33,19.82]
}

# ---------------------
# Toggle χάρτη
# ---------------------
if "map_type" not in st.session_state:
    st.session_state.map_type = "850hPa Θερμοκρασία"

if st.button("Αλλαγή Χάρτη"):
    st.session_state.map_type = "Υετός" if st.session_state.map_type=="850hPa Θερμοκρασία" else "850hPa Θερμοκρασία"

map_type = st.session_state.map_type

# ---------------------
# Start / Stop
# ---------------------
if "frame_idx" not in st.session_state:
    st.session_state.frame_idx = 0
if "playing" not in st.session_state:
    st.session_state.playing = False

if st.button("Start"):
    st.session_state.playing = True
if st.button("Stop"):
    st.session_state.playing = False

current_map = st.empty()

# ---------------------
# Auto-play loop με smooth animation
# ---------------------
while st.session_state.get("playing", False):
    idx = st.session_state.frame_idx
    next_idx = (idx + 1) % frames

    # Smooth interpolation
    temp_current = median_temp.isel(time=idx).values
    temp_next = median_temp.isel(time=next_idx).values
    rain_current = precip.isel(time=idx).values
    rain_next = precip.isel(time=next_idx).values

    steps = 5
    for s in range(steps):
        alpha = s / steps
        temp_frame = temp_current*(1-alpha) + temp_next*alpha
        rain_frame = rain_current*(1-alpha) + rain_next*alpha
        model_time = pd.to_datetime(str(time_values[idx])) + pd.Timedelta(hours=3*alpha)
        model_name = "Weather Insights Greece Model"

        fig = go.Figure()

        if map_type=="850hPa Θερμοκρασία":
            fig.add_trace(go.Heatmap(
                z=temp_frame, x=lon, y=lat,
                colorscale="RdBu_r",
                zmin=-15, zmax=30,
                colorbar=dict(title="T850 °C")
            ))
            toggle_text = "Υετός"
        else:
            fig.add_trace(go.Heatmap(
                z=rain_frame, x=lon, y=lat,
                colorscale=[
                    [0,"lightblue"],[0.2,"blue"],[0.4,"darkblue"],
                    [0.6,"pink"],[1,"purple"]
                ],
                zmin=0, zmax=25,
                colorbar=dict(title="mm")
            ))
            toggle_text = "850hPa"

        # Πρωτεύουσες
        for city,(lat_c,lon_c) in capitals.items():
            fig.add_trace(go.Scatter(x=[lon_c], y=[lat_c], mode='text', text=[city]))

        # Ημερομηνία/ώρα + όνομα μοντέλου
        fig.add_annotation(
            x=lon[0], y=lat[-1],
            text=f"{model_time.strftime('%Y-%m-%d %H:%M UTC')} | {model_name}",
            showarrow=False, xanchor='left', yanchor='top',
            font=dict(color="black", size=14)
        )

        # Toggle πάνω δεξιά
        fig.add_annotation(
            x=lon[-1], y=lat[-1],
            text=toggle_text,
            showarrow=False, xanchor='right', yanchor='top',
            font=dict(color="black", size=14)
        )

        # Όνομα "Weather Insights Greece" κάτω
        fig.add_annotation(
            x=(lon[0]+lon[-1])/2, y=lat[0]-2,
            text="Weather Insights Greece",
            showarrow=False,
            font=dict(size=12, color="black")
        )

        current_map.plotly_chart(fig, use_container_width=True)
        time.sleep(0.3)

    st.session_state.frame_idx = next_idx


