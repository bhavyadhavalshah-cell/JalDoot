from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import HazardZone
from app.schemas import WeatherResponse
from app.services.weather_service import fetch_marine_and_weather
from app.services.alert_service import calculate_haversine_distance

router = APIRouter(prefix="/weather", tags=["Marine Weather"])

@router.get("/", response_model=WeatherResponse)
@router.get("/current", response_model=WeatherResponse)
def get_current_marine_weather(
    lat: float = Query(21.63, description="Vessel Latitude"),
    lon: float = Query(69.60, description="Vessel Longitude"),
    db: Session = Depends(get_db)
):
    """
    Fetches real-time marine weather from Open-Meteo API (free, zero API key)
    and computes the Sea Safety Score (0-100) combining real wind, waves, and database hazard zones.
    """
    hazards = db.query(HazardZone).filter(HazardZone.active == True).all()
    
    # Check if vessel location falls within any active database hazard zone
    matched_hazard = None
    min_hazard_dist = 9999.0
    for h in hazards:
        dist = calculate_haversine_distance(lat, lon, h.latitude, h.longitude)
        if dist <= h.radius_km:
            if dist < min_hazard_dist:
                min_hazard_dist = dist
                matched_hazard = h

    has_hazard = matched_hazard is not None
    hazard_name = matched_hazard.name if matched_hazard else None
    hazard_severity = matched_hazard.severity if matched_hazard else None

    weather_data = fetch_marine_and_weather(
        latitude=lat, 
        longitude=lon, 
        has_hazard=has_hazard,
        hazard_name=hazard_name,
        hazard_severity=hazard_severity
    )
    return weather_data
