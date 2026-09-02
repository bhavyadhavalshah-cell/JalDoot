from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import HazardZone, User
from app.schemas import HazardZoneResponse, HazardZoneCreate
from app.auth import get_current_admin

router = APIRouter(prefix="/hazards", tags=["Hazard Zones"])

@router.get("/", response_model=List[HazardZoneResponse])
def get_all_hazards(db: Session = Depends(get_db)):
    """Returns all active and inactive maritime hazard zones"""
    return db.query(HazardZone).filter(HazardZone.active == True).all()

@router.post("/create", response_model=HazardZoneResponse)
def create_hazard_zone(
    hazard_in: HazardZoneCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin endpoint to publish a new hazard zone / cyclone alert"""
    new_hazard = HazardZone(
        name=hazard_in.name,
        zone_type=hazard_in.zone_type,
        latitude=hazard_in.latitude,
        longitude=hazard_in.longitude,
        radius_km=hazard_in.radius_km,
        severity=hazard_in.severity,
        description=hazard_in.description,
        active=hazard_in.active if hazard_in.active is not None else True
    )
    db.add(new_hazard)
    db.commit()
    db.refresh(new_hazard)
    return new_hazard
