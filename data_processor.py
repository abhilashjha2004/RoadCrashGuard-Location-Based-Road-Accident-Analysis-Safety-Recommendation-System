import pandas as pd
import requests
import io
from geopy.distance import geodesic
import os

ACCIDENTS_CSV = "data/accidents.csv"

def fetch_historical_data():
    """Loads accidents from local accidents.csv."""
    try:
        if os.path.exists(ACCIDENTS_CSV):
            return pd.read_csv(ACCIDENTS_CSV)
        else:
            print(f"Error: {ACCIDENTS_CSV} not found.")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error loading historical data: {e}")
        return pd.DataFrame()

def fetch_realtime_incidents(lat, lon, api_key=None):
    """Fetches real-time traffic incidents near coordinates using TomTom API."""
    if not api_key:
        return []
    
    # Define a bounding box around the coordinates (~5km)
    delta = 0.05 
    bbox = f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}"
    
    url = f"https://api.tomtom.com/traffic/services/5/incidentDetails?key={api_key}&bbox={bbox}&fields={{incidents{{type,geometry{{type,coordinates}},properties{{id,magnitudeOfDelay,description,cause,from,to,length,delay}}}}}}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('incidents', [])
        else:
            print(f"Failed to fetch real-time incidents: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching real-time incidents: {e}")
        return []

def filter_data_by_proximity(df, lat, lon, radius_km=20):
    """Filters data within a radius of 20 km using geopy.distance."""
    if df.empty:
        return df
    
    def is_nearby(row):
        try:
            point = (row['latitude'], row['longitude'])
            dist = geodesic((lat, lon), point).km
            return dist <= radius_km
        except:
            return False
            
    return df[df.apply(is_nearby, axis=1)]

def get_structured_analysis(df):
    """Returns structured analysis data from the accident dataframe."""
    if df.empty:
        return {
            "total_accidents": 0,
            "severity_dist": {},
            "weather_dist": {},
            "time_dist": {}
        }
    
    analysis = {
        "total_accidents": len(df),
        "severity_dist": df['severity'].value_counts().to_dict(),
        "weather_dist": df['weather'].value_counts().to_dict(),
        "time_dist": df['time_of_day'].value_counts().to_dict()
    }
    return analysis
