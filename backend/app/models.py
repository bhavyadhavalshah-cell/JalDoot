import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="fisherman") # "admin" or "fisherman"
    vessel_number = Column(String(100), nullable=True)
    vessel_photo = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    preferred_language = Column(String(10), default="en") # "en", "hi", "gu"
    is_active = Column(Boolean, default=True) # Active (30-40%) vs Inactive/Deactivated
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    gps_pings = relationship("GPSPing", back_populates="user", cascade="all, delete-orphan")
    sos_alerts = relationship("SOSAlert", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    network_events = relationship("NetworkEvent", back_populates="user", cascade="all, delete-orphan")
    login_audits = relationship("LoginAudit", back_populates="user", cascade="all, delete-orphan")

class LoginAudit(Base):
    __tablename__ = "login_audits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False)
    interface_mode = Column(String(20), default="desktop") # "mobile" or "desktop"
    is_auto_responsive = Column(Boolean, default=False)
    ip_address = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="login_audits")

class GPSPing(Base):
    __tablename__ = "gps_pings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vessel_number = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_knots = Column(Float, default=0.0)
    heading = Column(Float, default=0.0)
    in_hazard_zone = Column(Boolean, default=False)
    near_boundary = Column(Boolean, default=False)
    is_demo = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="gps_pings")

class SOSAlert(Base):
    __tablename__ = "sos_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vessel_number = Column(String(100), nullable=False)
    fisherman_name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    emergency_type = Column(String(50), default="DISTRESS")
    details = Column(Text, nullable=True)
    status = Column(String(20), default="ACTIVE") # "ACTIVE", "ACKNOWLEDGED", "RESOLVED"
    notified_vessels_json = Column(Text, nullable=True)
    is_demo = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sos_alerts")

class NetworkEvent(Base):
    __tablename__ = "network_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vessel_number = Column(String(100), nullable=True)
    event_type = Column(String(50), nullable=False) # "OFFLINE", "ONLINE", "BOUNDARY_CROSS", "DEMO_HAZARD_ENTRY"
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    details = Column(Text, nullable=True)
    is_demo = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="network_events")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False) # "user" or "assistant"
    content = Column(Text, nullable=False)
    language = Column(String(10), default="en") # "en", "hi", "gu"
    metadata_json = Column(Text, nullable=True)
    is_demo = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="chat_messages")

class HazardZone(Base):
    __tablename__ = "hazard_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    zone_type = Column(String(50), default="CRITICAL_DANGER") # "LOW_ALERT" (Yellow), "HIGH_ALERT" (Brown), "CRITICAL_DANGER" (Red)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_km = Column(Float, default=15.0)
    severity = Column(String(20), default="HIGH") # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class OceanData(Base):
    __tablename__ = "ocean_data"

    id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String(100), nullable=False)
    sst = Column(Float, nullable=False)
    chlorophyll = Column(Float, nullable=False)
    wave_height = Column(Float, nullable=False)
    wind_speed = Column(Float, nullable=False)
    fish_productivity_index = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

class SystemSetting(Base):
    __tablename__ = "system_settings"

    key = Column(String(50), primary_key=True)
    value = Column(String(255), nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
