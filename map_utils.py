import folium
from folium.plugins import HeatMap
import pandas as pd

def create_incident_map(lat, lon, incidents, historical_df=None, hotspots=None):
    """Creates a Folium map with real-time incidents, historical heatmap, and hotspots."""
    # Create base map
    m = folium.Map(location=[lat, lon], zoom_start=12, tiles="cartodbpositron")
    
    # Add marker for the queried location
    folium.Marker(
        [lat, lon],
        popup="Query Location",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)
    
    # 1. Add HeatMap layer
    if historical_df is not None and not historical_df.empty:
        heat_data = [[row['latitude'], row['longitude']] for index, row in historical_df.iterrows()]
        HeatMap(heat_data, radius=15, blur=10, min_opacity=0.3).add_to(m)
        
        # 2. Add Markers for Major/High Severity Accidents
        major_accidents = historical_df[historical_df['severity'].isin(['High', 'Fatal'])]
        for _, row in major_accidents.iterrows():
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=4,
                color='darkred',
                fill=True,
                fill_color='red',
                popup=f"Severity: {row['severity']} | Vehicle: {row['vehicle_type']}"
            ).add_to(m)
    
    # 3. Highlight Detected Hotspots (DBSCAN)
    if hotspots:
        for hs in hotspots:
            folium.Circle(
                location=[hs['latitude'], hs['longitude']],
                radius=1000, # 1km radius
                color='crimson',
                fill=True,
                fill_color='crimson',
                fill_opacity=0.4,
                popup=f"🔥 <b>Hotspot</b><br>Location: {hs['address']}<br>Accidents: {hs['size']}"
            ).add_to(m)
    
    # 4. Add markers for real-time incidents (TomTom)
    for incident in incidents:
        coords = incident.get('geometry', {}).get('coordinates', [])
        if len(coords) >= 2:
            inc_lat, inc_lon = coords[1], coords[0]
            desc = incident.get('properties', {}).get('description', 'Traffic Incident')
            folium.Marker(
                location=[inc_lat, inc_lon],
                popup=desc,
                icon=folium.Icon(color='orange', icon='warning')
            ).add_to(m)
            
    return m
