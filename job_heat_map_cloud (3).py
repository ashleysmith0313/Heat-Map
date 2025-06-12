
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

st.set_page_config(layout="wide")
st.title("📍 HeatMapMatrix – Territory Intelligence Dashboard")

radius_miles = st.slider("🔁 Select Radius (in miles)", min_value=5, max_value=100, value=25)

@st.cache_data
def load_data():
    jobs = pd.read_excel("latest_job_export.xlsx")
    zips = pd.read_excel("uszips.xlsx")
    jobs.columns = jobs.columns.str.strip().str.lower()
    zips.columns = zips.columns.str.strip().str.lower()
    return jobs, zips

jobs, zips = load_data()

# Determine the zip merge key from jobs file
merge_key_jobs = None
for col in jobs.columns:
    if "zip" in col or "postal" in col:
        merge_key_jobs = col
        break

if not merge_key_jobs or "zip" not in zips.columns:
    st.error("🛑 Could not find ZIP/postal code columns in both files. Check headers.")
    st.stop()

merged = pd.merge(jobs, zips, left_on=merge_key_jobs, right_on="zip", how="left")
merged = merged.drop_duplicates(subset=["id", merge_key_jobs, "county"])

m = folium.Map(location=[39.5, -98.35], zoom_start=5, control_scale=True)
marker_cluster = MarkerCluster().add_to(m)

for _, row in merged.iterrows():
    lat, lng = row.get("lat"), row.get("lng")
    if pd.notnull(lat) and pd.notnull(lng):
        tooltip = f"ID: {row.get('id')}<br>County: {row.get('county')}<br>ZIP: {row.get(merge_key_jobs)}"
        folium.Circle(
            location=(lat, lng),
            radius=radius_miles * 1609.34,
            color="blue",
            fill=True,
            fill_opacity=0.25,
            tooltip=tooltip
        ).add_to(marker_cluster)

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

st_data = st_folium(m, width=1400, height=700)
