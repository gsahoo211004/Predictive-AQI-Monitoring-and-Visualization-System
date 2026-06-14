import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium
import sys
import os

sys.path.append(os.path.dirname(__file__))

from src.data.fetcher import get_current_aqi, get_aqi_forecast, get_location_name
from src.utils.map_utils import create_base_map, add_aqi_marker
from src.ml.forecaster import run_forecast_pipeline

st.set_page_config(
    page_title="AQI Monitor",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 Predictive AQI Monitoring System")
st.markdown("Click anywhere on the map to get real-time air quality data and ML-powered forecasts.")

# Sidebar
with st.sidebar:
    st.header("How to use")
    st.markdown("""
    1. **Click** any location on the map
    2. View **current AQI** and pollutants
    3. See **ML forecast** for next 4 days
    4. Get **health recommendations**
    """)
    st.divider()
    st.markdown("**AQI Scale**")
    aqi_scale = {
        "1 — Good": "#00E400",
        "2 — Fair": "#FFFF00",
        "3 — Moderate": "#FF7E00",
        "4 — Poor": "#FF0000",
        "5 — Very Poor": "#8F3F97"
    }
    for label, color in aqi_scale.items():
        st.markdown(
            f'<div style="background:{color};color:{"#000" if "Good" in label or "Fair" in label else "#fff"};'
            f'padding:4px 10px;border-radius:4px;margin:2px 0;font-size:13px;">{label}</div>',
            unsafe_allow_html=True
        )

# Location input section
st.subheader("📍 Select Location")

col_search, col_btn = st.columns([4, 1])
with col_search:
    city_input = st.text_input(
        "Search city:",
        placeholder="e.g. Mumbai, Delhi, London, New York...",
        label_visibility="collapsed"
    )
with col_btn:
    search_clicked = st.button("🔍 Search", use_container_width=True)

# Resolve city name to coordinates
if search_clicked and city_input:
    from geopy.geocoders import Nominatim
    with st.spinner(f"Finding {city_input}..."):
        try:
            geolocator = Nominatim(user_agent="aqi_monitor")
            location = geolocator.geocode(city_input, timeout=10)
            if location:
                st.session_state["search_lat"] = location.latitude
                st.session_state["search_lon"] = location.longitude
                st.success(f"Found: {location.address}")
            else:
                st.error("City not found. Try a different name.")
        except Exception as e:
            st.error(f"Search error: {str(e)}")

# Build map — center on searched city if available
map_center_lat = st.session_state.get("search_lat", 20.5937)
map_center_lon = st.session_state.get("search_lon", 78.9629)
map_zoom = 10 if "search_lat" in st.session_state else 5

m = create_base_map(map_center_lat, map_center_lon, map_zoom)
map_data = st_folium(m, width="100%", height=450, returned_objects=["last_clicked"])

# Use searched coordinates if no map click yet
if not (map_data and map_data.get("last_clicked")) and "search_lat" in st.session_state:
    map_data = {"last_clicked": {
        "lat": st.session_state["search_lat"],
        "lng": st.session_state["search_lon"]
    }}

# Process map click
if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]

    st.divider()

    # Fetch data
    with st.spinner("Fetching AQI data..."):
        location_name = get_location_name(lat, lon)
        aqi_data = get_current_aqi(lat, lon)
        forecast_data = get_aqi_forecast(lat, lon)

    if aqi_data["status"] == "error":
        st.error(f"Error fetching data: {aqi_data['message']}")
    else:
        st.subheader(f"📊 Air Quality — {location_name}")

        # Current AQI metrics
        col1, col2, col3, col4 = st.columns(4)
        aqi_color = aqi_data["aqi_color"]
        col1.metric("AQI Index", aqi_data["aqi"])
        col2.metric("Status", aqi_data["aqi_label"])
        col3.metric("PM2.5", f"{aqi_data['components']['PM2.5']} µg/m³")
        col4.metric("PM10", f"{aqi_data['components']['PM10']} µg/m³")

        # Health advice
        st.markdown(
            f'<div style="background:{aqi_color};color:{"#000" if aqi_data["aqi"] <= 2 else "#fff"};'
            f'padding:12px 20px;border-radius:8px;margin:8px 0;font-size:15px;">'
            f'💡 {aqi_data["advice"]}</div>',
            unsafe_allow_html=True
        )

        # Pollutants breakdown
        st.subheader("🔬 Pollutant Breakdown")
        components = aqi_data["components"]
        fig_bar = px.bar(
            x=list(components.keys()),
            y=list(components.values()),
            labels={"x": "Pollutant", "y": "Concentration (µg/m³)"},
            color=list(components.values()),
            color_continuous_scale="RdYlGn_r",
        )
        fig_bar.update_layout(showlegend=False, height=300,
                              margin=dict(t=20, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

        # ML Forecast
        if forecast_data:
            st.subheader("🤖 ML-Powered AQI Forecast")
            with st.spinner("Running ML forecast pipeline..."):
                result = run_forecast_pipeline(forecast_data)

            if result["status"] == "success":
                metrics = result["metrics"]
                m1, m2, m3 = st.columns(3)
                m1.metric("Best Model", metrics["best_model"].replace("_", " ").title())
                m2.metric("MAE", metrics[metrics["best_model"]]["mae"])
                m3.metric("R² Score", metrics[metrics["best_model"]]["r2"])

                # Forecast chart
                pred_df = pd.DataFrame(result["predictions"])
                pred_df["timestamp"] = pd.to_datetime(pred_df["timestamp"])

                fig_forecast = go.Figure()
                fig_forecast.add_trace(go.Scatter(
                    x=pred_df["timestamp"], y=pred_df["aqi"],
                    name="Actual AQI", line=dict(color="#636EFA", width=2)
                ))
                fig_forecast.add_trace(go.Scatter(
                    x=pred_df["timestamp"], y=pred_df["ensemble_prediction"],
                    name="ML Prediction", line=dict(color="#EF553B", width=2, dash="dash")
                ))
                fig_forecast.update_layout(
                    xaxis_title="Time",
                    yaxis_title="AQI Level",
                    yaxis=dict(tickvals=[1,2,3,4,5],
                               ticktext=["Good","Fair","Moderate","Poor","Very Poor"]),
                    height=350,
                    margin=dict(t=20, b=20),
                    legend=dict(orientation="h", y=1.1)
                )
                st.plotly_chart(fig_forecast, use_container_width=True)

                # Updated map with marker
                st.subheader("📍 Selected Location")
                m2_map = create_base_map(lat, lon, zoom=10)
                m2_map = add_aqi_marker(m2_map, lat, lon, aqi_data, location_name)
                st_folium(m2_map, width="100%", height=300,
                         returned_objects=[])

        st.caption(f"Data fetched at {aqi_data['timestamp']} | Coordinates: {lat:.4f}, {lon:.4f}")

else:
    st.info("👆 Click anywhere on the map above to get started.")   