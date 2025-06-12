
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from math import radians, cos, sin, asin, sqrt

st.set_page_config(layout="wide")
st.title("📍 HeatMapMatrix – Territory Intelligence Dashboard")

# User-defined radius input
radius_miles = st.slider("🔁 Select Radius (in miles)", min_value=5, max_value=100, value=25)

# Load data
jobs_file = "latest_job_export.xlsx"
zips_file = "uszips.xlsx"

@st.cache_data
def load_data():
    jobs = pd.read_excel(jobs_file)
    zips = pd.read_excel(zips_file)
    jobs.columns = jobs.columns.str.lower()
    zips.columns = zips.columns.str.lower()
    return jobs, zips

jobs, zips = load_data()

# Merge on zip
merged = pd.merge(jobs, zips, how="left", left_on="zip", right_on="zip")

# Remove duplicates
merged = merged.drop_duplicates(subset=["id", "zip", "county"])

# Center map
m = folium.Map(location=[39.5, -98.35], zoom_start=5, control_scale=True)
marker_cluster = MarkerCluster().add_to(m)

# Add job markers
for _, row in merged.iterrows():
    lat, lng = row["lat"], row["lng"]
    if pd.notnull(lat) and pd.notnull(lng):
        tooltip = f"ID: {row['id']}<br>County: {row['county']}<br>ZIP: {row['zip']}"
        folium.Circle(
            location=(lat, lng),
            radius=radius_miles * 1609.34,  # convert miles to meters
            color="blue",
            fill=True,
            fill_opacity=0.25,
            tooltip=tooltip
        ).add_to(marker_cluster)

# Address search
geolocator = Nominatim(user_agent="heatmap_app")

def geocode_address(address):
    try:
        return geolocator.geocode(address, timeout=10)
    except GeocoderTimedOut:
        return None

address = st.text_input("📫 Enter Address to Pin", "")
if address:
    location = geocode_address(address)
    if location:
        folium.Marker(
            [location.latitude, location.longitude],
            popup=address,
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)
        st.success("Address pinned successfully!")
    else:
        st.error("Address not found. Try again.")

# Display map
st_data = st_folium(m, width=1400, height=700)
