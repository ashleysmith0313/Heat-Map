
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
    jobs = jobs[['ID', 'County', 'Postal Code']].drop_duplicates()
    jobs['State'] = jobs['Location'].str.extract(r'US-([A-Z]{2})-')
    merged = pd.merge(jobs, zips, left_on='Postal Code', right_on='zip', how='left')
    return merged[['ID', 'County', 'Postal Code', 'State', 'lat', 'lng']].dropna().drop_duplicates(subset=['Postal Code'])

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
        popup=f"ID: {row['ID']}\nCounty: {row['County']}\nZIP: {row['Postal Code']}"
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
