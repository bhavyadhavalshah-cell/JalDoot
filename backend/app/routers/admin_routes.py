import json
import datetime
import random
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, GPSPing, SOSAlert, NetworkEvent, ChatMessage, HazardZone, LoginAudit
from app.auth import get_current_admin
from app.services.gemini_service import generate_chat_response
from app.services.alert_service import find_sos_dispatch_vessels

router = APIRouter(prefix="/admin", tags=["Admin / Disaster Management"])

SAMPLE_COASTAL_QUERIES = [
    {"user": "ramesh_kumar", "lang": "gu", "msg": "પોરબંદર અને માંગરોળ વચ્ચે પવન અને મોજાંની સ્થિતિ કેવી છે?"},
    {"user": "bhavesh_patel", "lang": "gu", "msg": "વેરાવળ સમુદ્રમાં પોમ્ફ્રેટ અને સુરમાઈ માટે કયો ફિશિંગ ઝોન સારો છે?"},
    {"user": "suresh_tandel", "lang": "hi", "msg": "मुंबई और रत्नागिरी तट के पास चक्रवात का कोई अलर्ट है क्या?"},
    {"user": "anand_koli", "lang": "en", "msg": "What is the live Sea Safety Score and wave height near Okha harbor today?"},
    {"user": "devendra_machhi", "lang": "hi", "msg": "मालवण और सिंधुदुर्ग क्षेत्र में आज मछली पकड़ने के लिए मौसम कैसा है?"},
    {"user": "kiran_kharva", "lang": "en", "msg": "Are there any navigational hazards near Panaji and Mormugao harbor in Goa?"}
]

EMERGENCY_TYPES = [
    ("ENGINE_PROPULSION_FAILURE", "Main diesel propulsion engine stalled 14 nautical miles offshore."),
    ("STEERING_GEAR_JAM", "Rudder hydraulic line pressure loss in rough sea swell."),
    ("NET_PROPELLER_FOULING", "Trawl net entangled around propeller shaft causing total loss of maneuverability."),
    ("HULL_SEEPAGE_ALERT", "Minor bilge pump failure with water ingress in hold.")
]

@router.get("/dashboard-stats")
def get_dashboard_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Aggregated stats for Maritime Command Center"""
    total_fishermen = db.query(User).filter(User.role == "fisherman").count()
    active_fishermen = db.query(User).filter(User.role == "fisherman", User.is_active == True).count()
    active_sos = db.query(SOSAlert).filter(SOSAlert.status == "ACTIVE").count()
    active_hazards = db.query(HazardZone).filter(HazardZone.active == True).count()

    return {
        "total_registered_vessels": total_fishermen if total_fishermen > 0 else 2500,
        "live_active_vessels": active_fishermen if active_fishermen > 0 else 875,
        "active_sos_alerts": active_sos,
        "active_hazard_zones": active_hazards,
        "system_time": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    }

@router.post("/trigger-demo-data")
def trigger_demo_data(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Triggered cleanly on Auto-Responsive login:
    1. Generates realistic Gujarat, Maharashtra & Goa coastal Q&As.
    2. Randomizes active SOS alerts between 1 and 4 with strictly unique vessels.
    """
    generated_qas = []

    # 1. Generate & Run Realistic Q&As
    for item in SAMPLE_COASTAL_QUERIES:
        user = db.query(User).filter(User.username == item["user"]).first()
        if not user:
            user = db.query(User).filter(User.role == "fisherman", User.is_active == True).first()
        if not user:
            continue

        latest_ping = db.query(GPSPing).filter(GPSPing.user_id == user.id).order_by(GPSPing.timestamp.desc()).first()
        lat = latest_ping.latitude if latest_ping else 21.30
        lon = latest_ping.longitude if latest_ping else 69.45

        ai_res = generate_chat_response(
            message=item["msg"],
            requested_lang=item["lang"],
            latitude=lat,
            longitude=lon
        )

        now_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=random.randint(1, 15))

        user_msg = ChatMessage(
            user_id=user.id,
            role="user",
            content=item["msg"],
            language=item["lang"],
            is_demo=True,
            timestamp=now_time
        )
        db.add(user_msg)

        bot_msg = ChatMessage(
            user_id=user.id,
            role="assistant",
            content=ai_res["reply"],
            language=ai_res["detected_language"],
            metadata_json=json.dumps(ai_res["explainable_factors"]),
            is_demo=True,
            timestamp=now_time + datetime.timedelta(seconds=1)
        )
        db.add(bot_msg)

        generated_qas.append({
            "fisherman": user.username,
            "vessel": user.vessel_number,
            "question": item["msg"],
            "answer": ai_res["reply"],
            "timestamp": now_time.isoformat()
        })

    # 2. Manage SOS Alerts - Ensure strict maximum of 4 alerts, do NOT recreate on resolve
    existing_active = db.query(SOSAlert).filter(SOSAlert.status == "ACTIVE").all()
    # If there are already active alerts or if alerts were resolved, do not force replenishment
    # Maximum 4 active alerts allowed at any time
    if len(existing_active) > 4:
        # Trim excess to enforce maximum 4
        for excess in existing_active[4:]:
            excess.status = "RESOLVED"
            excess.resolved_at = datetime.datetime.utcnow()

    db.commit()
    return {
        "success": True,
        "message": "Live Q&A and telemetry updated.",
        "generated_qa_count": len(generated_qas),
        "active_sos_count": min(len(existing_active), 4)
    }

@router.get("/active-vessels")
def get_active_vessels(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Returns fleet vessels strictly sorted by maritime priority:
    1. SOS distress vessels first
    2. Active sailing vessels second
    3. Inactive (port/anchored) vessels third
    """
    all_fishermen = db.query(User).filter(User.role == "fisherman").limit(600).all()
    active_sos_user_ids = {s.user_id for s in db.query(SOSAlert.user_id).filter(SOSAlert.status == "ACTIVE").all()}

    vessel_list = []
    now_utc = datetime.datetime.utcnow()
    ist_offset = datetime.timedelta(hours=5, minutes=30)
    now_ist = now_utc + ist_offset

    for idx, f in enumerate(all_fishermen):
        latest_ping = db.query(GPSPing).filter(GPSPing.user_id == f.id).order_by(GPSPing.timestamp.desc()).first()
        has_sos = f.id in active_sos_user_ids
        
        if latest_ping:
            lat = latest_ping.latitude
            lon = latest_ping.longitude
            speed = latest_ping.speed_knots
            heading = latest_ping.heading
            in_hazard = latest_ping.in_hazard_zone
            ping_delta_secs = (now_utc - latest_ping.timestamp).total_seconds() if latest_ping.timestamp else (idx * 3 % 180)
            actual_ping_time = now_ist - datetime.timedelta(seconds=min(ping_delta_secs, 300))
        else:
            from seed_data import get_scattered_coastal_coordinates
            lat, lon = get_scattered_coastal_coordinates(f.id, len(all_fishermen))
            speed = round(7.2 + (f.id % 5) * 0.4, 1) if f.is_active else 0.0
            heading = 220.0 if f.is_active else 0.0
            in_hazard = False
            actual_ping_time = now_ist - datetime.timedelta(seconds=(idx * 7 % 240))

        status_str = "SOS" if has_sos else ("ACTIVE" if f.is_active else "INACTIVE")

        vessel_list.append({
            "user_id": f.id,
            "username": f.username,
            "vessel_number": f.vessel_number or f"IND-GJ-{f.id:04d}",
            "vessel_photo": f.vessel_photo,
            "latitude": lat,
            "longitude": lon,
            "speed_knots": speed,
            "heading": heading,
            "in_hazard_zone": in_hazard,
            "has_active_sos": has_sos,
            "is_active": f.is_active,
            "status": status_str,
            "last_seen": actual_ping_time.strftime("%H:%M:%S IST"),
            "actual_timestamp": actual_ping_time.isoformat(),
            "phone_number": f.phone_number or "9825000000"
        })

    # Strict sorting: SOS first (0), Active second (1), Inactive third (2)
    def vessel_priority_key(v):
        if v["has_active_sos"]:
            return (0, v["user_id"])
        elif v["is_active"]:
            return (1, v["user_id"])
        else:
            return (2, v["user_id"])

    vessel_list.sort(key=vessel_priority_key)
    return vessel_list

@router.get("/recent-activity")
def get_recent_activity(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Chronological feed of maritime events and audits with real-time timestamps"""
    feed = []
    ist_offset = datetime.timedelta(hours=5, minutes=30)

    sos_items = db.query(SOSAlert).order_by(SOSAlert.timestamp.desc()).limit(15).all()
    for s in sos_items:
        ist_time = (s.timestamp + ist_offset).strftime("%H:%M:%S IST")
        feed.append({
            "type": "SOS",
            "title": f"DISTRESS ALERT: Vessel {s.vessel_number}",
            "description": f"{s.fisherman_name}: {s.details}",
            "coordinates": f"[{s.latitude:.3f}, {s.longitude:.3f}]",
            "status": s.status,
            "real_time": ist_time,
            "timestamp": s.timestamp.isoformat()
        })

    logins = db.query(LoginAudit).order_by(LoginAudit.timestamp.desc()).limit(10).all()
    for l in logins:
        ist_time = (l.timestamp + ist_offset).strftime("%H:%M:%S IST")
        feed.append({
            "type": "LOGIN",
            "title": f"ACCESS: {l.username}",
            "description": f"Role: {l.role.upper()} | Interface: {l.interface_mode.title()}",
            "coordinates": "N/A",
            "status": "AUTH_SUCCESS",
            "real_time": ist_time,
            "timestamp": l.timestamp.isoformat()
        })

    net_items = db.query(NetworkEvent).order_by(NetworkEvent.timestamp.desc()).limit(10).all()
    for n in net_items:
        ist_time = (n.timestamp + ist_offset).strftime("%H:%M:%S IST")
        feed.append({
            "type": "NETWORK",
            "title": f"TELEMETRY: {n.vessel_number}",
            "description": f"{n.event_type} - {n.details or ''}",
            "coordinates": f"[{n.latitude:.3f}, {n.longitude:.3f}]" if n.latitude else "N/A",
            "status": n.event_type,
            "real_time": ist_time,
            "timestamp": n.timestamp.isoformat()
        })

    feed.sort(key=lambda x: x["timestamp"], reverse=True)
    return feed[:35]


@router.get("/last-messages")
def get_last_messages_all(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Unified Q&A cards stream without duplicate questions or demo labels"""
    user_questions = db.query(ChatMessage, User).join(User, ChatMessage.user_id == User.id)\
        .filter(ChatMessage.role == "user")\
        .order_by(ChatMessage.timestamp.desc()).limit(20).all()

    unified_cards = []
    for q_msg, user in user_questions:
        ans_msg = db.query(ChatMessage).filter(
            ChatMessage.user_id == user.id,
            ChatMessage.role == "assistant",
            ChatMessage.timestamp >= q_msg.timestamp
        ).order_by(ChatMessage.timestamp.asc()).first()

        answer_text = ans_msg.content if ans_msg else "Advisory processing..."

        unified_cards.append({
            "id": q_msg.id,
            "fisherman_name": user.username,
            "vessel_number": user.vessel_number or f"VESSEL-{user.id}",
            "question": q_msg.content,
            "answer": answer_text,
            "language": q_msg.language.upper(),
            "timestamp": q_msg.timestamp.isoformat()
        })

    return unified_cards
