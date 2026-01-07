# Προσθήκη Temp/Precip στα capitals
capitals_plot = capitals.copy()
capitals_plot['Temp'] = df_weather.iloc[frame]['temperature']
capitals_plot['Precip'] = df_weather.iloc[frame]['precipitation']

# Αν υπάρχουν NaN, βάζουμε 0
capitals_plot['Temp'] = capitals_plot['Temp'].fillna(0)
capitals_plot['Precip'] = capitals_plot['Precip'].fillna(0)

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

capitals_plot['ColorTemp'] = capitals_plot['Temp'].apply(temp_color)

# Δημιουργία χάρτη με ασφαλές size
if st.session_state.map_type == '850hPa Temperature':
    fig = px.scatter_geo(
        capitals_plot, lat='Lat', lon='Lon', text='City',
        size=capitals_plot['Temp'].abs()+0.1,  # size πάντα >0
        color='Temp',
        color_continuous_scale=["purple","darkblue","lightblue","lightgreen","green","yellow","orange","red"],
        range_color=[-20,35],
        projection="natural earth", scope="europe"
    )
else:
    fig = px.scatter_geo(
        capitals_plot, lat='Lat', lon='Lon', text='City',
        size=capitals_plot['Precip']+0.1,  # size πάντα >0
        color='Precip',
        color_continuous_scale=["lightblue","blue","darkblue","pink","purple"],
        range_color=[0,30],
        projection="natural earth", scope="europe"
    )












