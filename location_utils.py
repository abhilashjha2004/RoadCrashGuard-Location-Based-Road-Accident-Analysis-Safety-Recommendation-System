import requests
from geopy.geocoders import Nominatim
import ipinfo

def get_current_location():
    """Detects the approximate location based on IP address."""
    try:
        # Using ipinfo.io for approximate location (free tier doesn't always need a key for basic info)
        handler = ipinfo.getHandler()
        details = handler.getDetails()
        if hasattr(details, 'loc'):
            lat, lon = details.loc.split(',')
            return float(lat), float(lon), details.city
        return None, None, "Unknown"
    except Exception as e:
        print(f"Error detecting location: {e}")
        return None, None, "Unknown"

# Hardcoded fallback for common Indian cities
CITY_FALLBACK = {
    "delhi": (28.6139, 77.2090, "New Delhi, Delhi, India"),
    "mumbai": (19.0760, 72.8777, "Mumbai, Maharashtra, India"),
    "bangalore": (12.9716, 77.5946, "Bengaluru, Karnataka, India"),
    "bengaluru": (12.9716, 77.5946, "Bengaluru, Karnataka, India"),
    "chennai": (13.0827, 80.2707, "Chennai, Tamil Nadu, India"),
    "kolkata": (22.5726, 88.3639, "Kolkata, West Bengal, India"),
    "hyderabad": (17.3850, 78.4867, "Hyderabad, Telangana, India"),
    "chandigarh": (30.7333, 76.7794, "Chandigarh, India"),
    "nh44": (28.6139, 77.2090, "NH44 (Defaulting to Delhi segment)")
}

def get_coordinates(location_name):
    """Converts a location name to coordinates with retry logic and local fallback."""
    import time
    
    # Check fallback first
    query = location_name.lower().strip()
    if query in CITY_FALLBACK:
        return CITY_FALLBACK[query]
    
    geolocator = Nominatim(user_agent="road_crash_guard_final_v3")
    
    for attempt in range(3):
        try:
            location = geolocator.geocode(location_name, timeout=15)
            if location:
                return location.latitude, location.longitude, location.address
            break
        except Exception as e:
            print(f"Geocoding Error (Attempt {attempt+1}): {e}")
            time.sleep(2)
            
    return None, None, None
