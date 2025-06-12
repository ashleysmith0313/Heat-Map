
import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from geopy.distance import geodesic

st.set_page_config(layout="wide")
st.title("📍 RadiusOS – Proximity Search Tool")

# Load data
@st.cache_data
def load_data():
    jobs = pd.read_excel("latest_job_export.xlsx")
    zips = pd.read_excel("uszips.xlsx")
    jobs.columns = jobs.columns.str.strip().str.lower()
    zips.columns = zips.columns.str.strip().str.lower()
    return jobs, zips

jobs, zips = load_data()

merge_key_jobs = next((col for col in jobs.columns if "zip" in col or "postal" in col), None)

if not merge_key_jobs or "zip" not in zips.columns:
    st.error("🛑 ZIP/postal code missing from one of the files.")
    st.stop()

merged = pd.merge(jobs, zips, left_on=merge_key_jobs, right_on="zip", how="left")
merged = merged.drop_duplicates(subset=["id", merge_key_jobs, "county"])

# Address search input
geolocator = Nominatim(user_agent="heatmap_app")

def geocode_address(address):
    try:
        return geolocator.geocode(address, timeout=10)
    except GeocoderTimedOut:
        return None

address = st.text_input("📫 Enter an address to filter jobs by proximity:")

# Only show slider if address is provided
if address:
    radius_miles = st.slider("🔁 Show jobs within X miles of address:", min_value=5, max_value=100, value=25)
    location = geocode_address(address)

    if location:
        lat_center, lng_center = location.latitude, location.longitude
        st.success(f"Pinned: {address} ({lat_center:.4f}, {lng_center:.4f})")

        def is_within_radius(row):
            if pd.notnull(row["lat"]) and pd.notnull(row["lng"]):
                return geodesic((lat_center, lng_center), (row["lat"], row["lng"])).miles <= radius_miles
            return False

        filtered = merged[merged.apply(is_within_radius, axis=1)]

        # Create and render map
        m = folium.Map(location=[lat_center, lng_center], zoom_start=6, control_scale=True)
        marker_cluster = MarkerCluster().add_to(m)

        # Pin center address
        folium.Marker(
            [lat_center, lng_center],
            popup="Search Center",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)

        for _, row in filtered.iterrows():
            lat, lng = row.get("lat"), row.get("lng")
            if pd.notnull(lat) and pd.notnull(lng):
                tooltip = f"ID: {row.get('id')}<br>County: {row.get('county')}<br>ZIP: {row.get(merge_key_jobs)}"
                folium.Circle(
                    location=(lat, lng),
                    radius=5000,  # visual marker radius in meters
                    color="blue",
                    fill=True,
                    fill_opacity=0.25,
                    tooltip=tooltip
                ).add_to(marker_cluster)

        st_data = st_folium(m, width=1400, height=700)
    else:
        st.error("❌ Address not found. Try a different one.")
else:
    st.info("🔎 Enter an address above to begin.")
