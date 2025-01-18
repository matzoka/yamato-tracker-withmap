import folium
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

def create_map(tolat, tolng, cities):
    """Create folium map with markers"""
    lat = tolat
    lng = tolng
    name = "No name"

    red_lat = 0.0
    red_lng = 0.0
    map = folium.Map(location=[lat, lng], zoom_start=6)

    for i, r in cities.iterrows():
        if i == 0:  # First item is current location
            colorsign = 'red'
            red_lat = r['latitude']
            red_lng = r['longtude']
        else:
            if red_lat == r['latitude'] and red_lng == r['longtude']:
                pass
            else:
                colorsign = 'green'

        folium.Marker(
            location=[r['latitude'], r['longtude']],
            popup=r['train'],
            icon=folium.Icon(color=colorsign),
        ).add_to(map)

    return map

def create_cities_dataframe(dataframe):
    """Create dataframe for map markers"""
    train = []
    latitude = []
    longtude = []

    for index,item in dataframe[0:].iterrows():
        tempLat = item['placeLat']
        if tempLat != 0:
            train.append(item['placeName'])
            latitude.append(item['placeLat'])
            longtude.append(item['placeLng'])

    return pd.DataFrame({
        'train': train,
        'latitude': latitude,
        'longtude': longtude,
    }).sort_index(ascending=True).dropna()
