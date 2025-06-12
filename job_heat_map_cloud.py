
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

st.set_page_config(layout="wide")
st.title("📍 Interactive Job Heat Map with Custom Address Search")

@st.cache_data
def load_data():
    jobs = pd.read_excel("latest_job_export.xlsx")
    zips = pd.read_excel("uszips.xlsx")

    # Normalize column names
    jobs.columns = jobs.columns.str.strip().str.lower()
    zips.columns = zips.columns.str.strip().str.lower()

    st.write("🔍 Job Columns:", list(jobs.columns))
    st.write("📦 ZIP Columns:", list(zips.columns))

    if 'postal code' not in jobs.columns:
        st.error("❌ 'postal code' column not found in job file.")
        st.stop()

    jobs = jobs[['id', 'county', 'postal code']].drop_duplicates()
    merged = pd.merge(jobs, zips, left_on='postal code', right_on='zip', how='left')

    if 'lat' not in merged.columns or 'lng' not in merged.columns:
        st.error("❌ ZIP merge failed — 'lat' or 'lng' not found. Check uszips.xlsx.")
        st.stop()

    usable = merged[['id', 'county', 'postal code', 'lat', 'lng']].dropna()
    return usable.drop_duplicates(subset=['postal code'])

df = load_data()

address_input = st.text_input("Enter an address to drop a pin:", "")

m = folium.Map(location=[df['lat'].mean(), df['lng'].mean()], zoom_start=5, tiles="CartoDB positron")

for _, row in df.iterrows():
    folium.Circle(
        location=(row['lat'], row['lng']),
        radius=40233.6,
        color='blue',
        fill=True,
        fill_opacity=0.3,
        popup=f"ID: {row['id']}\nCounty: {row['county']}\nZIP: {row['postal code']}"
    ).add_to(m)

if address_input:
    geolocator = Nominatim(user_agent="job_map_app")
    location = geolocator.geocode(address_input)
    if location:
        folium.Marker(
            location=(location.latitude, location.longitude),
            popup=f"📍 {address_input}",
            icon=folium.Icon(color='red', icon='home')
        ).add_to(m)
    else:
        st.warning("Address not found. Try again.")

st_folium(m, width=1200, height=700)
