import math
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models import HazardZone, User, GPSPing, SOSAlert, NetworkEvent
from app.services.sms_service import send_free_sms_alert

logger = logging.getLogger("JalDoot-AlertEngine")

# Coastal reference line approx (Western Coastline / Gujarat / Maharashtra coastline approximation)
COAST_ANCHOR_LAT = 21.60
COAST_ANCHOR_LON = 69.65
MAX_NETWORK_COVERAGE_KM = 35.0 # Max cellular connectivity range offshore

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates great-circle distance between two GPS coordinates in kilometers.
    """
    R = 6371.0 # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dLon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def check_gps_against_hazards_and_boundaries(
    db: Session,
    user: User,
    lat: float,
    lon: float
) -> Dict[str, Any]:
    """
    Checks if a fisherman's GPS ping enters any active hazard zones or crosses network boundaries.
    Automatically triggers SMS alerts when boundaries or danger zones are breached.
    """
    alerts_triggered = []
    in_hazard = False
    near_boundary = False
    
    # 1. Check Active Hazard Zones
    active_hazards = db.query(HazardZone).filter(HazardZone.active == True).all()
    for hazard in active_hazards:
        dist_km = calculate_haversine_distance(lat, lon, hazard.latitude, hazard.longitude)
        if dist_km <= hazard.radius_km:
            in_hazard = True
            msg = (
                f"⚠️ JALDOOT DANGER ALERT: Vessel {user.vessel_number or user.username} entered "
                f"Hazard Zone '{hazard.name}' ({hazard.zone_type}) at [{lat:.3f}, {lon:.3f}]. "
                f"Change course immediately!"
            )
            # Send automated SMS alert
            phone = user.phone_number or "+919876543210"
            send_free_sms_alert(phone, msg)
            alerts_triggered.append({
                "type": "HAZARD_ZONE_ENTRY",
                "hazard_name": hazard.name,
                "severity": hazard.severity,
                "distance_km": round(dist_km, 2)
            })
            break

    # 2. Check Offshore Network Coverage Boundary
    dist_from_coast = calculate_haversine_distance(lat, lon, COAST_ANCHOR_LAT, COAST_ANCHOR_LON)
    if dist_from_coast >= (MAX_NETWORK_COVERAGE_KM - 5.0):
        near_boundary = True
        if dist_from_coast >= MAX_NETWORK_COVERAGE_KM:
            msg = (
                f"📡 JALDOOT NETWORK NOTICE: Vessel {user.vessel_number or user.username} is outside "
                f"cellular coverage ({dist_from_coast:.1f} km offshore). "
                f"Offline safety cache & GPS tracker active."
            )
            phone = user.phone_number or "+919876543210"
            send_free_sms_alert(phone, msg)
            alerts_triggered.append({
                "type": "NETWORK_BOUNDARY_CROSSED",
                "distance_from_coast_km": round(dist_from_coast, 1)
            })

    return {
        "in_hazard_zone": in_hazard,
        "near_boundary": near_boundary,
        "distance_from_coast_km": round(dist_from_coast, 2),
        "alerts_triggered": alerts_triggered
    }

def find_sos_dispatch_vessels(
    db: Session, 
    origin_lat: float, 
    origin_lon: float, 
    exclude_user_id: int, 
    radius_km: float = 20.0
) -> Dict[str, Any]:
    """
    SOS Broadcast Logic:
    1. Finds all vessels within 20 km radius based on latest stored GPS positions.
    2. If zero vessels found within 20 km, finds the 3 nearest vessels outside that range (by distance).
    3. Returns list of notified vessels and whether they were 'within-range' or 'fallback-nearest'.
    """
    all_fishermen = db.query(User).filter(User.role == "fisherman", User.id != exclude_user_id).all()
    vessel_distances = []
    
    for f in all_fishermen:
        latest_ping = db.query(GPSPing).filter(GPSPing.user_id == f.id).order_by(GPSPing.timestamp.desc()).first()
        if latest_ping:
            dist = calculate_haversine_distance(origin_lat, origin_lon, latest_ping.latitude, latest_ping.longitude)
            vessel_distances.append({
                "user_id": f.id,
                "fisherman_name": f.username,
                "vessel_number": f.vessel_number or f"VESSEL-{f.id}",
                "distance_km": round(dist, 2),
                "latitude": latest_ping.latitude,
                "longitude": latest_ping.longitude,
                "timestamp": latest_ping.timestamp.isoformat()
            })
            
    # Sort all by distance ascending
    vessel_distances.sort(key=lambda x: x["distance_km"])

    # 1. Filter within 20 km
    within_range = [v for v in vessel_distances if v["distance_km"] <= radius_km]

    if within_range:
        for v in within_range:
            v["dispatch_type"] = "within_range_20km"
        return {
            "dispatch_mode": "WITHIN_RANGE",
            "notified_vessels": within_range,
            "count": len(within_range)
        }
    else:
        # 2. Fallback: 3 nearest vessels outside range
        fallback_3 = vessel_distances[:3]
        for v in fallback_3:
            v["dispatch_type"] = "fallback_nearest_out_of_range"
        return {
            "dispatch_mode": "FALLBACK_3_NEAREST",
            "notified_vessels": fallback_3,
            "count": len(fallback_3)
        }
