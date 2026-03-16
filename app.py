import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium
import location_utils
import data_processor
import safety_engine
import map_utils
import time

# --- Page Config ---
st.set_page_config(page_title="RoadCrashGuard Pro", layout="wide", page_icon="🛡️")

# --- Premium UI Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .stCard {
        background: white;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    
    .metric-card {
        text-align: center;
        padding: 20px;
        border-radius: 12px;
        background: #ffffff;
        border: 1px solid #eef2f7;
    }
    
    h1 {
        font-weight: 800;
        color: #1a5276;
        text-align: center;
        letter-spacing: -1px;
    }
    
    h2, h3 {
        color: #2c3e50;
        font-weight: 600;
    }
    
    .stButton>button {
        border-radius: 10px;
        background: #1a5276;
        color: white;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background: #154360;
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("<h1>🛡️ RoadCrashGuard: Advanced Safety Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #5d6d7e;'>Location-Based Road Accident Analysis & Proactive Recommendations</p>", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    mode = st.radio("Detection Mode", ["📍 Current Location", "🔍 Search Location"])
    
    st.markdown("---")
    api_key = st.text_input("TomTom API Key (Optional)", type="password")
    
    if st.button("🚀 Run Analysis", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- Core Logic ---
lat, lon, address = None, None, None

if mode == "📍 Current Location":
    with st.spinner("🛰️ Detecting location..."):
        lat, lon, address = location_utils.get_current_location()
        if not lat:
            st.warning("⚠️ Could not detect IP location. Defaulting to Delhi.")
            lat, lon, address = 28.6139, 77.2090, "Delhi (Default)"
else:
    location_query = st.text_input("📍 Enter City or Highway (e.g. NH44, Bangalore)", placeholder="Search...")
    if location_query:
        with st.spinner("🌍 Geocoding..."):
            lat, lon, address = location_utils.get_coordinates(location_query)
            if not lat:
                st.error("❌ Location not found. Please try another name.")

if lat and lon:
    st.markdown(f"### 📍 Location: {address}")
    
    # 1. Fetch & Process Data
    with st.spinner("🔍 Analysing local data..."):
        historical_all = data_processor.fetch_historical_data()
        nearby_df = data_processor.filter_data_by_proximity(historical_all, lat, lon)
        real_time_incidents = data_processor.fetch_realtime_incidents(lat, lon, api_key)
        
        # Fallback logic if API failed/missing key
        if not real_time_incidents:
            real_time_incidents = [] # Just ensures it's an empty list if not valid
            
        analysis = data_processor.get_structured_analysis(nearby_df)
        hotspots = safety_engine.detect_hotspots(nearby_df)
        score = safety_engine.calculate_safety_score(analysis, hotspots)
        risk = safety_engine.get_risk_level(score)
        recommendations = safety_engine.get_recommendations(score, analysis, len(hotspots))

    # --- Top Row: Safety Score & Quick Stats ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-card'><h3>Safety Score</h3><h1 style='color: #27ae60;'>{score}/10</h1></div>", unsafe_allow_html=True)
    with col2:
        risk_color = "#e74c3c" if risk == "High" else "#f39c12" if risk == "Medium" else "#27ae60"
        st.markdown(f"<div class='metric-card'><h3>Risk Level</h3><h1 style='color: {risk_color};'>{risk}</h1></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><h3>Total Accidents</h3><h1>{analysis['total_accidents']}</h1></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'><h3>Hotspots</h3><h1>{len(hotspots)}</h1></div>", unsafe_allow_html=True)

    st.markdown("---")

    # --- Main Dashboard Section ---
    tab1, tab2, tab3 = st.tabs(["🗺️ Safety Map", "📊 Accident Analysis", "💡 Recommendations"])

    with tab1:
        st.subheader("Interactive Safety Map (Heatmap & Hotspots)")
        m = map_utils.create_incident_map(lat, lon, real_time_incidents, nearby_df, hotspots)
        st_folium(m, width=None, height=500, use_container_width=True)
        st.markdown("> 🔴 **Heatmap**: Background density | 🔘 **Markers**: High-severity events | 🌀 **Circles**: DBSCAN Hotspots")

    with tab2:
        st.subheader("Accident Analysis Charts")
        if not nearby_df.empty:
            c1, c2 = st.columns(2)
            
            with c1:
                # Weather Distribution
                fig_weather = px.bar(
                    x=list(analysis['weather_dist'].keys()),
                    y=list(analysis['weather_dist'].values()),
                    title="Accidents by Weather Condition",
                    labels={'x': 'Weather', 'y': 'Count'},
                    color=list(analysis['weather_dist'].values()),
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig_weather, use_container_width=True)
                
                # Time of Day Distribution
                fig_time = px.bar(
                    x=list(analysis['time_dist'].keys()),
                    y=list(analysis['time_dist'].values()),
                    title="Accidents by Time of Day",
                    labels={'x': 'Time', 'y': 'Count'},
                    color_discrete_sequence=['#1a5276']
                )
                st.plotly_chart(fig_time, use_container_width=True)

            with c2:
                # Severity Distribution
                fig_sev = px.pie(
                    names=list(analysis['severity_dist'].keys()),
                    values=list(analysis['severity_dist'].values()),
                    title="Severity Distribution",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.RdBu
                )
                st.plotly_chart(fig_sev, use_container_width=True)
                
                # Trend (Mock Trend based on index if no date, or just rows)
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(y=np.cumsum(np.ones(len(nearby_df))), mode='lines', name='Cumulative', fill='tozeroy'))
                fig_trend.update_layout(title="Accident Cumulative Trend (Visualisation)", xaxis_title="Recent Records", yaxis_title="Running Total")
                st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No data available for charts in this specific location.")

    with tab3:
        st.subheader("Safety Recommendations")
        for r in recommendations:
            st.info(r)

    # --- Hotspots Section ---
    if hotspots:
        st.markdown("---")
        st.subheader("📍 Accident Hotspot Locations")
        hotspot_df = pd.DataFrame(hotspots)
        # Reorder columns for better readability
        if 'address' in hotspot_df.columns:
            hotspot_df = hotspot_df[['address', 'size', 'latitude', 'longitude']]
            hotspot_df.columns = ['Location Name', 'Accident Density', 'Latitude', 'Longitude']
        
        st.dataframe(hotspot_df, use_container_width=True, hide_index=True)

else:
    st.markdown("<div style='text-align: center; padding: 100px;'><h3>👋 Welcome to RoadCrashGuard</h3><p>Please enter a location or enable Current Location to begin your safety analysis.</p></div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown("<p style='text-align: center;'>Built with ❤️ for Safer Roads | v2.0-Auto</p>", unsafe_allow_html=True)
