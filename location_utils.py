from geopy.geocoders import Nominatim
import ipinfo
import json
import os

CONFIG_FILE = ".location_config.json"

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
    "phagwara": (31.2240, 75.7708, "Phagwara, Punjab, India"),
    "nh44": (28.6139, 77.2090, "NH44 (Defaulting to Delhi segment)")
}

def get_coordinates(location_name):
    """Converts a location name to coordinates with retry logic and local fallback."""
    import time
    
    # Check fallback first
    query = location_name.lower().strip()
    if query in CITY_FALLBACK:
        print(f"Geocoding: Hit fallback for '{query}'")
        return CITY_FALLBACK[query]
    
    print(f"Geocoding: Calling Nominatim for '{location_name}'...")
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

def save_default_location(lat, lon, address):
    """Saves the default location to a local file."""
    try:
        data = {
            "latitude": lat,
            "longitude": lon,
            "address": address
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        print(f"Error saving default location: {e}")
        return False

def load_default_location():
    """Loads the default location from a local file if it exists."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        print(f"Error loading default location: {e}")
        return None
