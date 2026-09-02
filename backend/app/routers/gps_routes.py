from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, GPSPing, NetworkEvent
from app.schemas import GPSPingCreate, GPSPingResponse, NetworkEventCreate
from app.auth import get_current_user
from app.services.alert_service import check_gps_against_hazards_and_boundaries

router = APIRouter(prefix="/gps", tags=["Live GPS Tracking"])

@router.post("/update", response_model=Dict[str, Any])
def update_gps_location(
    ping_data: GPSPingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Receives periodic live GPS coordinates (every 15-30 seconds) from navigator.geolocation.
    Stores coordinate ping, tests proximity to active hazard zones and offshore cellular boundaries,
    and returns immediate safety status flags.
    """
    vessel_id = current_user.vessel_number or f"VESSEL-{current_user.username}"

    # Check boundaries and hazards
    hazard_check = check_gps_against_hazards_and_boundaries(
        db=db,
        user=current_user,
        lat=ping_data.latitude,
        lon=ping_data.longitude
    )

    new_ping = GPSPing(
        user_id=current_user.id,
        vessel_number=vessel_id,
        latitude=ping_data.latitude,
        longitude=ping_data.longitude,
        speed_knots=ping_data.speed_knots or 0.0,
        heading=ping_data.heading or 0.0,
        in_hazard_zone=hazard_check["in_hazard_zone"],
        near_boundary=hazard_check["near_boundary"]
    )
    db.add(new_ping)
    db.commit()
    db.refresh(new_ping)

    return {
        "success": True,
        "ping_id": new_ping.id,
        "latitude": new_ping.latitude,
        "longitude": new_ping.longitude,
        "in_hazard_zone": new_ping.in_hazard_zone,
        "near_boundary": new_ping.near_boundary,
        "distance_from_coast_km": hazard_check["distance_from_coast_km"],
        "alerts_triggered": hazard_check["alerts_triggered"],
        "timestamp": new_ping.timestamp.isoformat()
    }

@router.post("/network-event")
def log_network_event(
    event_data: NetworkEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logs client-side network transition events (e.g. offline drop, online recovery).
    """
    vessel_id = current_user.vessel_number or f"VESSEL-{current_user.username}"
    net_event = NetworkEvent(
        user_id=current_user.id,
        vessel_number=vessel_id,
        event_type=event_data.event_type,
        latitude=event_data.latitude,
        longitude=event_data.longitude,
        details=event_data.details
    )
    db.add(net_event)
    db.commit()
    return {"success": True, "message": f"Network event {event_data.event_type} logged."}
