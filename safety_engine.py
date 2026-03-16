from sklearn.cluster import DBSCAN
import numpy as np
from geopy.geocoders import Nominatim
import time

def detect_hotspots(df, eps_km=1, min_samples=3):
    """Uses DBSCAN clustering to detect accident clusters (hotspots)."""
    if df.empty or len(df) < min_samples:
        return []
    
    coords = df[['latitude', 'longitude']].values
    # Convert kms to radians for use with haversine metric
    kms_per_radian = 6371.0088
    epsilon = eps_km / kms_per_radian
    
    db = DBSCAN(eps=epsilon, min_samples=min_samples, algorithm='ball_tree', metric='haversine').fit(np.radians(coords))
    
    # Identify cluster centers as hotspots
    labels = db.labels_
    unique_labels = set(labels)
    hotspots = []
    
    for label in unique_labels:
        if label == -1: continue # Noise
        
        class_member_mask = (labels == label)
        xy = coords[class_member_mask]
        centroid = xy.mean(axis=0)
        
        # Reverse Geocode to find address
        address = "Unknown Location"
        try:
            from geopy.exc import GeocoderServiceError
            geolocator = Nominatim(user_agent="road_crash_guard_hotspots_v2")
            location = geolocator.reverse(f"{centroid[0]}, {centroid[1]}", timeout=5)
            if location:
                address = location.address
            time.sleep(1) # Rate limit for Nominatim
        except Exception as e:
            print(f"Reverse geocode error: {e}")
            address = f"Hotspot near {centroid[0]:.4f}, {centroid[1]:.4f}"

        hotspots.append({
            'latitude': centroid[0],
            'longitude': centroid[1],
            'size': len(xy),
            'address': address
        })
        
    return hotspots

def calculate_safety_score(analysis, hotspots):
    """Calculates a safety score from 0 to 10 based on density, severity, and hotspots."""
    score = 10.0
    total = analysis.get('total_accidents', 0)
    
    # Deductions
    # 1. Density
    score -= min(total * 0.2, 3.0) # Up to 3 points deduction for total volume
    
    # 2. Severity
    severity = analysis.get('severity_dist', {})
    fatal_count = severity.get('Fatal', 0)
    high_count = severity.get('High', 0)
    score -= (fatal_count * 1.5)
    score -= (high_count * 0.5)
    
    # 3. Hotspots
    score -= (len(hotspots) * 1.0)
    
    return max(min(round(score, 1), 10.0), 0.0)

def get_recommendations(score, analysis, hotspots_count):
    """Generates safety recommendations based on analysis patterns."""
    recommendations = []
    
    if score <= 4:
        recommendations.append("🚨 HIGH RISK ZONE: Avoid this area if possible or maintain extreme vigilance.")
    elif score <= 7:
        recommendations.append("⚠️ MODERATE RISK: Stay alert and follow all safety protocols.")
    else:
        recommendations.append("✅ RELATIVELY SAFE ZONE: Drive safely.")
        
    if hotspots_count > 0:
        recommendations.append(f"📍 CAUTION: {hotspots_count} accident hotspots detected near your path.")
        
    time_dist = analysis.get('time_dist', {})
    if time_dist.get('Night', 0) > time_dist.get('Morning', 0) * 1.5:
        recommendations.append("🌙 Night driving is particularly dangerous here. Ensure headlights are functional.")
        
    weather_dist = analysis.get('weather_dist', {})
    if weather_dist.get('Rainy', 0) > analysis.get('total_accidents', 0) / 4:
        recommendations.append("🌧️ This area is prone to wet-weather accidents. Reduce speed during rain.")
        
    recommendations.append("📱 Keep your phone away while driving.")
    
    return recommendations

def get_risk_level(score):
    if score <= 4: return "High"
    if score <= 7: return "Medium"
    return "Low"
