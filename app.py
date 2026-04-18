"""
EpiAlert Interactive Dashboard
Real-time Disease Outbreak Detection and Visualization
"""

import streamlit as st
import pandas as pd
import folium
from folium import plugins
from streamlit_folium import st_folium
from datetime import datetime

# --------------------------------------------------

# PAGE CONFIG

# --------------------------------------------------

st.set_page_config(
page_title="EpiAlert - Disease Outbreak Detection",
page_icon="🦠",
layout="wide"
)

# --------------------------------------------------

# CSS

# --------------------------------------------------

st.markdown("""

<style>
.main-header{
font-size:2.5rem;
font-weight:bold;
color:#DC143C;
text-align:center;
}
.sub-header{
font-size:1.2rem;
text-align:center;
color:gray;
margin-bottom:2rem;
}
</style>

""", unsafe_allow_html=True)

# --------------------------------------------------

# CONSTANTS

# --------------------------------------------------

RISK_COLORS = {
"high":"#DC143C",
"medium":"#FF8C00",
"low":"#FFD700",
"normal":"#32CD32"
}

DISEASE_CLASSIFICATION = {
'fever_rash_jointpain':[('dengue',0.75),('chikungunya',0.2)],
'fever_with_cough':[('influenza',0.65),('covid_like',0.25)],
'gastrointestinal_severe':[('cholera',0.7),('food_poisoning',0.2)],
'fever_only':[('typhoid',0.5),('malaria',0.3)],
'respiratory_severe':[('pneumonia',0.6),('tuberculosis',0.25)]
}

# --------------------------------------------------

# LOAD DATA

# --------------------------------------------------

@st.cache_data
def load_alert_data():

```
try:
    df = pd.read_csv("alerts.csv")
    df.columns = df.columns.str.lower()
    return df

except:
    return pd.DataFrame()
```

@st.cache_data
def load_pincode_coordinates():

```
try:
    df = pd.read_csv("pincode_coordinates.csv")

    df.columns = df.columns.str.lower()

    df = df.rename(columns={
        "lat":"latitude",
        "lon":"longitude",
        "lng":"longitude",
        "district":"city"
    })

    return df

except:
    return pd.DataFrame()
```

# --------------------------------------------------

# LOGIC

# --------------------------------------------------

def classify_disease(symptom_cluster, spike_ratio):

```
if symptom_cluster not in DISEASE_CLASSIFICATION:
    return ("unknown",0.5)

disease,prob = DISEASE_CLASSIFICATION[symptom_cluster][0]

boost = min(spike_ratio/5,0.15)

return disease,min(prob+boost,0.95)
```

def detect_anomaly(daily_count,baseline,spike_ratio,score):

```
is_anomaly = spike_ratio > 2 and score > 0.8

if not is_anomaly:
    return False,"normal"

if spike_ratio >= 3:
    return True,"high"
elif spike_ratio >= 2:
    return True,"medium"
else:
    return True,"low"
```

# --------------------------------------------------

# MAP

# --------------------------------------------------

def create_map(alert_data,pincode_coords):

```
map_data = alert_data.merge(
    pincode_coords[['pincode','latitude','longitude','city','state']],
    on="pincode",
    how="left"
)

if len(map_data) == 0:
    center = [23,79]
else:
    center = [map_data.latitude.mean(),map_data.longitude.mean()]

m = folium.Map(
    location=center,
    zoom_start=5,
    tiles="cartodbpositron"
)

if len(map_data) > 0:

    heat_data = [
        [row.latitude,row.longitude,row.spike_ratio]
        for _,row in map_data.iterrows()
    ]

    plugins.HeatMap(
        heat_data,
        radius=25,
        blur=30
    ).add_to(m)

cluster = plugins.MarkerCluster().add_to(m)

for _,row in map_data.iterrows():

    popup = f"""
    <b>{row.city}, {row.state}</b><br>
    Pincode: {row.pincode}<br>
    Disease: {row.primary_disease}<br>
    Cases: {row.daily_count}<br>
    Spike: {row.spike_ratio}x
    """

    folium.CircleMarker(
        location=[row.latitude,row.longitude],
        radius=10,
        color="white",
        fill=True,
        fill_color=RISK_COLORS[row.risk_level],
        popup=popup
    ).add_to(cluster)

return m
```

# --------------------------------------------------

# APP

# --------------------------------------------------

def main():

```
st.markdown('<div class="main-header">🦠 EpiAlert Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-time Disease Outbreak Monitoring</div>', unsafe_allow_html=True)

alert_data = load_alert_data()
pincode_coords = load_pincode_coordinates()

col1,col2,col3,col4 = st.columns(4)

with col1:
    st.metric("Active Alerts",len(alert_data))

with col2:
    high=len(alert_data[alert_data.risk_level=="high"])
    st.metric("High Risk",high)

with col3:
    avg=alert_data.spike_ratio.mean() if len(alert_data)>0 else 0
    st.metric("Avg Spike",f"{avg:.2f}x")

with col4:
    loc=len(alert_data.pincode.unique()) if len(alert_data)>0 else 0
    st.metric("Locations",loc)

st.divider()

st.subheader("Disease Outbreak Map")

map_obj=create_map(alert_data,pincode_coords)

st_folium(map_obj,width=1400,height=600)

st.divider()

st.subheader("Active Alerts")

if len(alert_data)>0:

    st.dataframe(
        alert_data[['pincode','primary_disease','daily_count','spike_ratio','risk_level']],
        use_container_width=True
    )

else:

    st.info("No active alerts")

st.divider()

st.caption(
    f"EpiAlert Dashboard | Updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
```

if **name**=="**main**":
main()
