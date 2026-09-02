import json
import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import User, SOSAlert, GPSPing
from app.schemas import SOSCreate, SOSResponse
from app.auth import get_current_user, get_current_admin
from app.services.sms_service import send_free_sms_alert
from app.services.alert_service import find_sos_dispatch_vessels
from app.services.email_service import send_sos_alert_email

router = APIRouter(prefix="/sos", tags=["Emergency SOS"])

@router.post("/trigger", response_model=Dict[str, Any])
def trigger_sos_alert(
    sos_data: SOSCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers emergency SOS:
    1. Notifies Admin Dashboard.
    2. Broadcasts to all vessels within 20 km. If 0 found, falls back to the 3 nearest vessels.
    3. Logs notified vessels list (within-range vs fallback) against the SOS record.
    4. Sends free carrier SMS alert.
    """
    vessel_id = current_user.vessel_number or f"VESSEL-{current_user.username}"

    # 1. Compute Notified Vessels (20km or fallback 3 nearest)
    dispatch_info = find_sos_dispatch_vessels(
        db=db,
        origin_lat=sos_data.latitude,
        origin_lon=sos_data.longitude,
        exclude_user_id=current_user.id,
        radius_km=20.0
    )

    notified_vessels_str = json.dumps(dispatch_info)
    
    # 2. Record SOS in Database
    new_sos = SOSAlert(
        user_id=current_user.id,
        vessel_number=vessel_id,
        fisherman_name=current_user.username,
        latitude=sos_data.latitude,
        longitude=sos_data.longitude,
        emergency_type=sos_data.emergency_type or "DISTRESS",
        details=sos_data.details or f"Emergency distress beacon activated by {current_user.username}",
        status="ACTIVE",
        notified_vessels_json=notified_vessels_str
    )
    db.add(new_sos)

    # Log/Update latest GPS ping
    ping = GPSPing(
        user_id=current_user.id,
        vessel_number=vessel_id,
        latitude=sos_data.latitude,
        longitude=sos_data.longitude,
        speed_knots=0.0,
        heading=0.0,
        in_hazard_zone=True
    )
    db.add(ping)
    db.commit()
    db.refresh(new_sos)

    # 3. Dispatch Automated Real Email to jaldootprojectsih@gmail.com
    email_result = send_sos_alert_email(
        fisherman_name=current_user.username,
        vessel_number=vessel_id,
        latitude=sos_data.latitude,
        longitude=sos_data.longitude,
        phone_number=current_user.phone_number or "9825000001",
        emergency_type=sos_data.emergency_type or "DISTRESS",
        details=sos_data.details or f"Emergency distress beacon activated by {current_user.username}",
        notified_vessels_count=dispatch_info["count"],
        dispatch_mode=dispatch_info["dispatch_mode"],
        timestamp=new_sos.timestamp
    )

    # 4. Dispatch SMS / Email-to-SMS Alert
    alert_msg = (
        f"🚨 MAYDAY SOS: Vessel {vessel_id} ({current_user.username}) at [{sos_data.latitude:.4f}, {sos_data.longitude:.4f}]. "
        f"Mode: {dispatch_info['dispatch_mode']} ({dispatch_info['count']} ships alerted)."
    )
    sms_result = send_free_sms_alert(
        phone_number=settings.ADMIN_ALERT_PHONE,
        message_text=alert_msg,
        carrier="generic"
    )

    mode_text = "within 20 km" if dispatch_info["dispatch_mode"] == "WITHIN_RANGE" else "nearest 3 vessels (extended range)"

    return {
        "success": True,
        "sos_id": new_sos.id,
        "vessel_number": vessel_id,
        "status": "DISPATCHED",
        "dispatch_mode": dispatch_info["dispatch_mode"],
        "notified_vessels_count": dispatch_info["count"],
        "notified_vessels": dispatch_info["notified_vessels"],
        "timestamp": new_sos.timestamp.isoformat(),
        "email_dispatch": email_result,
        "sms_dispatch": sms_result,
        "message": f"SOS Broadcasted to Disaster Command, email sent to jaldootprojectsih@gmail.com, and {dispatch_info['count']} vessels alerted {mode_text}."
    }

@router.get("/active", response_model=List[SOSResponse])
def get_active_sos_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns active emergency SOS alerts (visible to Admin)"""
    alerts = db.query(SOSAlert).filter(SOSAlert.status == "ACTIVE").order_by(SOSAlert.timestamp.desc()).all()
    return alerts

@router.post("/{sos_id}/resolve")
@router.put("/{sos_id}/resolve")
def resolve_sos_alert(
    sos_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin action to mark an SOS alert as resolved in real-time"""
    sos = db.query(SOSAlert).filter(SOSAlert.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=404, detail="SOS alert not found")
    
    sos.status = "RESOLVED"
    sos.resolved_at = datetime.datetime.utcnow()
    db.commit()
    return {
        "success": True, 
        "sos_id": sos_id,
        "status": "RESOLVED",
        "message": f"SOS #{sos_id} for Vessel {sos.vessel_number} marked as resolved."
    }
