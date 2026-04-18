"""
EpiAlert Interactive Dashboard
Real-time Disease Outbreak Detection and Visualization
"""

import streamlit as st
import pandas as pd
import folium
from folium import plugins
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import os

# Page configuration
st.set_page_config(
    page_title="EpiAlert - Disease Outbreak Detection",
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #DC143C;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .alert-high {
        background: #ffebee;
        border-left: 4px solid #DC143C;
    }
    .alert-medium {
        background: #fff3e0;
        border-left: 4px solid #FF8C00;
    }
    .alert-low {
        background: #fffde7;
        border-left: 4px solid #FFD700;
    }
</style>
""", unsafe_allow_html=True)

# Disease classification mapping
DISEASE_CLASSIFICATION = {
    'fever_rash_jointpain': [('dengue', 0.75), ('chikungunya', 0.20), ('zika', 0.05)],
    'fever_with_cough': [('influenza', 0.65), ('covid_like', 0.25), ('common_cold', 0.10)],
    'gastrointestinal_severe': [('cholera', 0.70), ('food_poisoning', 0.20), ('gastroenteritis', 0.10)],
    'fever_only': [('typhoid', 0.50), ('malaria', 0.30), ('viral_fever', 0.20)],
    'respiratory_severe': [('pneumonia', 0.60), ('tuberculosis', 0.25), ('covid_like', 0.15)],
    'skin_rash': [('measles', 0.60), ('chickenpox', 0.25), ('dengue', 0.15)],
    'neurological': [('meningitis', 0.65), ('encephalitis', 0.25), ('cerebral_malaria', 0.10)],
    'fever_respiratory': [('influenza', 0.60), ('covid_like', 0.30), ('pneumonia', 0.10)],
    'gastrointestinal_mild': [('gastroenteritis', 0.60), ('food_poisoning', 0.30), ('viral_infection', 0.10)],
    'vector_borne': [('dengue', 0.50), ('malaria', 0.30), ('chikungunya', 0.20)],
    'skin_infection': [('cellulitis', 0.50), ('impetigo', 0.30), ('fungal_infection', 0.20)],
    'unknown': [('unknown', 0.50), ('viral_fever', 0.30), ('bacterial_infection', 0.20)],
}

DISEASE_EMOJIS = {
    'dengue': '🦟', 'malaria': '🦟', 'chikungunya': '🦟', 'zika': '🦟',
    'cholera': '🤢', 'gastroenteritis': '🤢', 'food_poisoning': '🤢',
    'influenza': '🤧', 'covid_like': '😷', 'common_cold': '🤧',
    'pneumonia': '🫁', 'tuberculosis': '🫁',
    'typhoid': '🤒', 'measles': '🤒', 'chickenpox': '🤒',
    'meningitis': '🧠', 'encephalitis': '🧠',
    'unknown': '🦠'
}

RISK_COLORS = {
    'high': '#DC143C',
    'medium': '#FF8C00',
    'low': '#FFD700',
    'normal': '#32CD32'
}

# Database connection configuration
@st.cache_resource
def get_db_connection():
    """Get Databricks SQL connection"""
    try:
        connection = sql.connect(
            server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME"),
            http_path=os.getenv("DATABRICKS_HTTP_PATH"),
            access_token=os.getenv("DATABRICKS_TOKEN")
        )
        return connection
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_alert_data():
    """Load current alerts from gold anomaly table"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    query = """
    WITH latest_alerts AS (
        SELECT 
            pincode,
            symptom_cluster,
            primary_disease,
            primary_disease_prob as disease_confidence,
            report_date,
            daily_count,
            `30d_avg` as baseline,
            count_vs_30d_avg as spike_ratio,
            if_score as anomaly_score,
            alert_flag,
            risk_level,
            ROW_NUMBER() OVER (
                PARTITION BY pincode, symptom_cluster 
                ORDER BY report_date DESC
            ) as rn
        FROM workspace.default.epi_alert_gold_anomaly
    )
    SELECT 
        pincode,
        symptom_cluster,
        primary_disease,
        disease_confidence,
        report_date,
        daily_count,
        baseline,
        spike_ratio,
        anomaly_score,
        alert_flag,
        risk_level
    FROM latest_alerts
    WHERE rn = 1 AND alert_flag = 1
    ORDER BY spike_ratio DESC
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        
        df = pd.DataFrame(data, columns=columns)
        # Normalize column names
        df.columns = df.columns.str.lower()
        
        # Rename possible variations
        df = df.rename(columns={
            "lat": "latitude",
            "lon": "longitude",
            "lng": "longitude",
            "district": "city",
            "location": "city"
        })

return df
    except Exception as e:
        st.error(f"Failed to load alerts: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_pincode_coordinates():
    """Load pincode coordinates from Delta table"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    query = "SELECT * FROM workspace.epialert.epi_pincode_coordinates"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        cursor.close()
        df = pd.DataFrame(data, columns=columns)
        # Normalize column names
        df.columns = df.columns.str.lower()
        
        # Rename possible variations
        df = df.rename(columns={
            "lat": "latitude",
            "lon": "longitude",
            "lng": "longitude",
            "district": "city",
            "location": "city"
        })
        
        return df
    except Exception as e:
        st.error(f"Failed to load coordinates: {e}")
        return pd.DataFrame()

def classify_disease(symptom_cluster, spike_ratio):
    """Classify disease based on symptom cluster"""
    if symptom_cluster not in DISEASE_CLASSIFICATION:
        return ('unknown', 0.5)
    
    diseases = DISEASE_CLASSIFICATION[symptom_cluster]
    confidence_boost = min(spike_ratio / 5.0, 0.15)
    primary_disease, base_conf = diseases[0]
    return (primary_disease, min(base_conf + confidence_boost, 0.99))

def detect_anomaly(daily_count, baseline, spike_ratio, anomaly_score):
    """Detect if data represents an anomaly"""
    is_anomaly = spike_ratio > 2.0 and anomaly_score > 0.8
    
    if is_anomaly:
        if spike_ratio >= 3.0 or anomaly_score >= 0.85:
            risk_level = 'high'
        elif spike_ratio >= 2.0 or anomaly_score >= 0.7:
            risk_level = 'medium'
        else:
            risk_level = 'low'
    else:
        risk_level = 'normal'
    
    return is_anomaly, risk_level

def create_map(alert_data, pincode_coords, new_alert=None):
    """Create Folium map with alerts"""
    # Merge alerts with coordinates
    map_data = alert_data.merge(
        pincode_coords[['pincode', 'latitude', 'longitude', 'city', 'state']], 
        on='pincode', 
        how='left'
    )
    
    # Calculate center
    if len(map_data) > 0:
        center_lat = map_data['latitude'].mean()
        center_lon = map_data['longitude'].mean()
    else:
        center_lat, center_lon = 23.0, 79.0  # India center
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=5,
        tiles='CartoDB positron',
        prefer_canvas=True
    )
    
    # Add heatmap layer
    if len(map_data) > 0:
        heat_data = [
            [row['latitude'], row['longitude'], row['spike_ratio'] * row['daily_count']] 
            for _, row in map_data.iterrows()
        ]
        plugins.HeatMap(
            heat_data,
            min_opacity=0.3,
            radius=25,
            blur=30,
            gradient={0.0: 'green', 0.5: 'yellow', 0.7: 'orange', 0.85: 'orangered', 1.0: 'crimson'}
        ).add_to(m)
    
    # Add marker cluster
    marker_cluster = plugins.MarkerCluster().add_to(m)
    
    # Add existing alerts
    for _, row in map_data.iterrows():
        disease_emoji = DISEASE_EMOJIS.get(row['primary_disease'], '🦠')
        
        popup_html = f"""
        <div style="font-family: Arial; width: 280px;">
            <div style="background: {RISK_COLORS[row['risk_level']]}22; padding: 10px; border-radius: 8px 8px 0 0;">
                <h4 style="margin: 0; color: #333;">🚨 {row['city']}, {row['state']}</h4>
            </div>
            <div style="padding: 10px;">
                <table style="width: 100%; font-size: 12px;">
                    <tr><td><b>Pincode:</b></td><td>{row['pincode']}</td></tr>
                    <tr><td><b>Risk:</b></td><td><span style="background: {RISK_COLORS[row['risk_level']]}; color: white; padding: 2px 6px; border-radius: 8px;">{row['risk_level'].upper()}</span></td></tr>
                    <tr><td><b>Cases:</b></td><td><b>{row['daily_count']}</b></td></tr>
                    <tr><td><b>Spike:</b></td><td>{row['spike_ratio']:.2f}x</td></tr>
                    <tr><td><b>Disease:</b></td><td>{disease_emoji} {row['primary_disease']} ({row['disease_confidence']*100:.0f}%)</td></tr>
                </table>
            </div>
        </div>
        """
        
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=10 + (row['spike_ratio'] * 2),
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{row['city']} - {row['primary_disease']} - {row['risk_level']}",
            color='white',
            fill=True,
            fillColor=RISK_COLORS[row['risk_level']],
            fillOpacity=0.7,
            weight=2
        ).add_to(marker_cluster)
    
    # Add new alert if provided
    if new_alert:
        disease_emoji = DISEASE_EMOJIS.get(new_alert['primary_disease'], '🦠')
        
        popup_html = f"""
        <div style="font-family: Arial; width: 280px;">
            <div style="background: {RISK_COLORS[new_alert['risk_level']]}22; padding: 10px; border-radius: 8px 8px 0 0;">
                <h4 style="margin: 0; color: #333;">🆕 NEW ALERT: {new_alert['city']}, {new_alert['state']}</h4>
            </div>
            <div style="padding: 10px;">
                <table style="width: 100%; font-size: 12px;">
                    <tr><td><b>Pincode:</b></td><td>{new_alert['pincode']}</td></tr>
                    <tr><td><b>Risk:</b></td><td><span style="background: {RISK_COLORS[new_alert['risk_level']]}; color: white; padding: 2px 6px; border-radius: 8px;">{new_alert['risk_level'].upper()}</span></td></tr>
                    <tr><td><b>Cases:</b></td><td><b>{new_alert['daily_count']}</b></td></tr>
                    <tr><td><b>Baseline:</b></td><td>{new_alert['baseline']:.1f}</td></tr>
                    <tr><td><b>Spike:</b></td><td><b style="color: #DC143C;">{new_alert['spike_ratio']:.2f}x</b></td></tr>
                    <tr><td><b>Disease:</b></td><td>{disease_emoji} {new_alert['primary_disease']} ({new_alert['disease_confidence']*100:.0f}%)</td></tr>
                </table>
                <div style="margin-top: 8px; padding: 6px; background: #fff3cd; border-radius: 4px; font-size: 11px;">
                    ⚠️ NEW anomaly - requires attention
                </div>
            </div>
        </div>
        """
        
        folium.CircleMarker(
            location=[new_alert['latitude'], new_alert['longitude']],
            radius=15 + (new_alert['spike_ratio'] * 3),
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"🆕 NEW: {new_alert['city']} - {new_alert['primary_disease']} - {new_alert['risk_level']}",
            color='yellow',
            fill=True,
            fillColor=RISK_COLORS[new_alert['risk_level']],
            fillOpacity=0.9,
            weight=4
        ).add_to(m)
    
    # Add legend
    legend_html = f"""
    <div style="position: fixed; bottom: 50px; right: 50px; width: 200px; background: white; 
                border: 2px solid #ccc; border-radius: 10px; padding: 15px; z-index: 9999;">
        <h4 style="margin: 0 0 10px 0;">Risk Levels</h4>
        <div><span style="background: {RISK_COLORS['high']}; width: 20px; height: 20px; display: inline-block; border-radius: 50%;"></span> High Risk</div>
        <div><span style="background: {RISK_COLORS['medium']}; width: 20px; height: 20px; display: inline-block; border-radius: 50%;"></span> Medium Risk</div>
        <div><span style="background: {RISK_COLORS['low']}; width: 20px; height: 20px; display: inline-block; border-radius: 50%;"></span> Low Risk</div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

# Main App
def main():
    st.markdown('<div class="main-header">🦠 EpiAlert Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Real-time Disease Outbreak Detection & Monitoring</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Dashboard Controls")
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.divider()
        
        # Add new report section
        st.header("📝 Add New Health Report")
        
        with st.form("new_report_form"):
            pincode = st.number_input("Pincode", min_value=100000, max_value=999999, value=302001)
            
            symptom_cluster = st.selectbox(
                "Symptom Cluster",
                options=list(DISEASE_CLASSIFICATION.keys()),
                index=0
            )
            
            daily_count = st.number_input("Daily Case Count", min_value=1, max_value=1000, value=10)
            baseline = st.number_input("Baseline (30-day avg)", min_value=1.0, max_value=500.0, value=5.0, step=0.1)
            anomaly_score = st.slider("Anomaly Score", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
            
            submit_button = st.form_submit_button("🔍 Analyze & Submit", use_container_width=True)
        
        if submit_button:
            # Calculate spike ratio
            spike_ratio = daily_count / baseline
            
            # Detect anomaly
            is_anomaly, risk_level = detect_anomaly(daily_count, baseline, spike_ratio, anomaly_score)
            
            # Classify disease
            primary_disease, disease_confidence = classify_disease(symptom_cluster, spike_ratio)
            
            # Get coordinates
            pincode_coords = load_pincode_coordinates()
            coords = pincode_coords[pincode_coords['pincode'] == pincode]
            
            if len(coords) > 0:
                new_alert = {
                    'pincode': pincode,
                    'symptom_cluster': symptom_cluster,
                    'daily_count': daily_count,
                    'baseline': baseline,
                    'spike_ratio': spike_ratio,
                    'anomaly_score': anomaly_score,
                    'is_anomaly': is_anomaly,
                    'risk_level': risk_level,
                    'primary_disease': primary_disease,
                    'disease_confidence': disease_confidence,
                    'latitude': coords.iloc[0]['latitude'],
                    'longitude': coords.iloc[0]['longitude'],
                    'city': coords.iloc[0]['city'],
                    'state': coords.iloc[0]['state']
                }
                
                st.session_state['new_alert'] = new_alert
                
                # Display results
                st.divider()
                st.subheader("📊 Analysis Results")
                
                if is_anomaly:
                    st.error(f"⚠️ **ANOMALY DETECTED!**")
                    st.markdown(f"""
                    - **Location:** {new_alert['city']}, {new_alert['state']}
                    - **Disease:** {DISEASE_EMOJIS.get(primary_disease, '🦠')} {primary_disease.upper()} ({disease_confidence*100:.0f}%)
                    - **Risk Level:** {risk_level.upper()}
                    - **Spike Ratio:** {spike_ratio:.2f}x
                    - **Cases:** {daily_count} (baseline: {baseline:.1f})
                    """)
                else:
                    st.success("✅ **No Anomaly Detected**")
                    st.markdown(f"""
                    - **Location:** {new_alert['city']}, {new_alert['state']}
                    - **Spike Ratio:** {spike_ratio:.2f}x
                    - **Status:** Normal (below threshold)
                    """)
            else:
                st.error(f"❌ Pincode {pincode} not found in database")
    
    # Main content area
    # Load data
    alert_data = load_alert_data()
    pincode_coords = load_pincode_coordinates()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🚨 Active Alerts", len(alert_data))
    
    with col2:
        high_risk = len(alert_data[alert_data['risk_level'] == 'high']) if len(alert_data) > 0 else 0
        st.metric("🔴 High Risk", high_risk)
    
    with col3:
        avg_spike = alert_data['spike_ratio'].mean() if len(alert_data) > 0 else 0
        st.metric("📈 Avg Spike Ratio", f"{avg_spike:.2f}x")
    
    with col4:
        locations = len(alert_data['pincode'].unique()) if len(alert_data) > 0 else 0
        st.metric("📍 Affected Locations", locations)
    
    st.divider()
    
    # Map
    st.subheader("🗺️ Disease Outbreak Map")
    
    new_alert = st.session_state.get('new_alert', None)
    map_obj = create_map(alert_data, pincode_coords, new_alert)
    
    st_folium(map_obj, width=1400, height=600)
    
    # Alert table
    st.divider()
    st.subheader("📋 Active Alerts")
    
    if len(alert_data) > 0:
        # Format display data
        display_data = alert_data.copy()
        display_data['spike_ratio'] = display_data['spike_ratio'].apply(lambda x: f"{x:.2f}x")
        display_data['disease_confidence'] = display_data['disease_confidence'].apply(lambda x: f"{x*100:.0f}%")
        display_data['anomaly_score'] = display_data['anomaly_score'].apply(lambda x: f"{x:.3f}")
        
        st.dataframe(
            display_data[['pincode', 'symptom_cluster', 'primary_disease', 'disease_confidence', 
                          'daily_count', 'spike_ratio', 'risk_level']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No active alerts at this time.")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        EpiAlert Dashboard v1.0 | Powered by Databricks & Streamlit | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """.format(datetime=datetime), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
