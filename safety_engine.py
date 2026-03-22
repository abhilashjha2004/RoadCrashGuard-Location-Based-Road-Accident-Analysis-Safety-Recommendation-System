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
    
    # 1. Risk-Based Guidance
    if score <= 4:
        recommendations.append("🚨 **CRITICAL RISK**: This area has a high frequency of serious accidents. Avoid through-traffic if possible.")
    elif score <= 7:
        recommendations.append("⚠️ **MODERATE RISK**: Historical data shows frequent incidents. Stay focused and avoid distractions.")
    else:
        recommendations.append("✅ **STABLE ZONE**: Lower accident density detected. Maintain standard safety protocols.")
        
    # 2. Environmental & Time Factors
    time_dist = analysis.get('time_dist', {})
    if time_dist.get('Night', 0) > time_dist.get('Morning', 0) * 1.5:
        recommendations.append("🌙 **NIGHT HAZARD**: Significant accidents occur after dark. Ensure high-beam discipline and watch for unlit vehicles.")
        
    weather_dist = analysis.get('weather_dist', {})
    if weather_dist.get('Rainy', 0) > analysis.get('total_accidents', 0) / 4:
        recommendations.append("🌧️ **WET TRACTION**: Historical data suggests high slip-risk during rain. Increase following distance by 2x.")

    # 3. Structural Advice
    if hotspots_count > 2:
        recommendations.append(f"🛑 **CONGESTED HOTSPOTS**: {hotspots_count} accident clusters detected ahead. Sudden braking is common here.")

    return recommendations

def get_recommended_speed(score, analysis):
    """Calculates a dynamic recommended speed limit."""
    base_speed = 60 # Standard urban/semi-urban limit
    
    # 1. Score-based reduction
    if score < 4:
        rec_speed = 30
    elif score < 6:
        rec_speed = 40
    elif score < 8:
        rec_speed = 50
    else:
        rec_speed = 60
        
    # 2. Factor in night-time risks from data
    time_dist = analysis.get('time_dist', {})
    if time_dist.get('Night', 0) > analysis.get('total_accidents', 0) / 2:
        rec_speed -= 10 # Reduce speed if night accidents are dominant
        
    return max(rec_speed, 20) # Minimum 20 km/h for safety

def get_route_guidance(hotspots):
    """Provides route advice based on detected accident hotspots."""
    if not hotspots:
        return "✅ **ROUTE ADVICE**: No specific high-risk road clusters detected. Stick to main arterials and maintain standard safety."
    
    # Extract road names from hotspot addresses (simple heuristic: first part of address)
    high_risk_locations = []
    for hs in hotspots[:3]:
        addr = hs.get('address', 'Unknown Road')
        # Try to get a shorter road name/area
        short_addr = addr.split(',')[0]
        high_risk_locations.append(short_addr)
    
    if high_risk_locations:
        locs_str = " and ".join(high_risk_locations)
        return f"🗺️ **ROUTE ADVICE**: Data indicates higher accident density near **{locs_str}**. Exercise extra caution or use bypasses if your route passes through these areas."
    
    return "✅ **ROUTE ADVICE**: No specific high-risk road clusters detected on your current path."

def get_risk_level(score):
    if score <= 4: return "High"
    if score <= 7: return "Medium"
    return "Low"
