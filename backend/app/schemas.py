from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    vessel_number: Optional[str] = None
    vessel_photo: Optional[str] = None
    preferred_language: Optional[str] = "en"
    interface_mode: Optional[str] = "desktop"
    is_auto_responsive: Optional[bool] = False
    default_latitude: Optional[float] = None
    default_longitude: Optional[float] = None
    home_state: Optional[str] = None
    is_demo: Optional[bool] = False

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# User Schemas
class UserLogin(BaseModel):
    username_or_email: str
    password: str
    interface_mode: Optional[str] = "desktop"
    is_auto_responsive: Optional[bool] = False

class UserCreate(BaseModel):
    username: str
    password: str
    vessel_number: str
    phone_number: str = Field(..., description="Exactly 10 digit mobile number")
    preferred_language: Optional[str] = "en"
    interface_mode: Optional[str] = "mobile"
    is_auto_responsive: Optional[bool] = False

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        clean = "".join(filter(str.isdigit, v or ""))
        if len(clean) != 10:
            raise ValueError("Mobile number must be exactly 10 digits.")
        return clean

class PasswordResetRequest(BaseModel):
    phone_number: str = Field(..., description="Registered 10 digit mobile number")
    new_password: str = Field(..., min_length=4)
    confirm_password: str = Field(..., min_length=4)

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        clean = "".join(filter(str.isdigit, v or ""))
        if len(clean) != 10:
            raise ValueError("Mobile number must be exactly 10 digits.")
        return clean

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    vessel_number: Optional[str] = None
    vessel_photo: Optional[str] = None
    preferred_language: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LoginAuditResponse(BaseModel):
    id: int
    user_id: int
    username: str
    role: str
    interface_mode: str
    is_auto_responsive: bool
    timestamp: datetime

    class Config:
        from_attributes = True

# GPS Ping Schemas
class GPSPingCreate(BaseModel):
    latitude: float
    longitude: float
    speed_knots: Optional[float] = 0.0
    heading: Optional[float] = 0.0

class GPSPingResponse(BaseModel):
    id: int
    user_id: int
    vessel_number: Optional[str]
    latitude: float
    longitude: float
    speed_knots: float
    heading: float
    in_hazard_zone: bool
    near_boundary: bool
    is_demo: bool
    timestamp: datetime

    class Config:
        from_attributes = True

# SOS Alert Schemas
class SOSCreate(BaseModel):
    latitude: float
    longitude: float
    emergency_type: Optional[str] = "DISTRESS"
    details: Optional[str] = "Emergency distress beacon activated by vessel"

class SOSResponse(BaseModel):
    id: int
    user_id: int
    vessel_number: str
    fisherman_name: str
    latitude: float
    longitude: float
    emergency_type: str
    details: Optional[str]
    status: str
    notified_vessels_json: Optional[str] = None
    is_demo: bool
    timestamp: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Chat Message Schemas
class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "auto"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ChatResponse(BaseModel):
    reply: str
    detected_language: str
    confidence_score: int
    is_off_topic: bool = False
    timestamp: datetime
    explainable_factors: Dict[str, Any]

# Unified Q&A Card Schema for Admin Message Monitor
class UnifiedChatCard(BaseModel):
    id: int
    fisherman_name: str
    vessel_number: str
    question: str
    answer: str
    language: str
    timestamp: str

# Weather & Safety Schemas
class WeatherResponse(BaseModel):
    latitude: float
    longitude: float
    is_coastal_region: bool = True
    temperature_c: float
    wind_speed_kmh: float
    wind_direction_deg: float
    wave_height_m: float
    wave_period_s: float
    weather_code: int
    weather_description: str
    sea_safety_score: Optional[int] = None
    safety_status: str
    safety_reasons: List[str]
    whatif_modifier_applied: float = 0.0
    data_timestamp: str

# PFZ Zone Schemas
class PFZZone(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    radius_km: float
    polygon_coords: Optional[List[List[float]]] = None
    density_level: Optional[str] = "MAXIMUM"
    distance_km: float
    bearing_deg: float
    chlorophyll: float
    sst_celsius: float
    depth_m: Optional[int] = 35
    confidence_pct: int
    recommended_target_fish: List[str]
    isro_advisory_id: Optional[str] = "ISRO-INCOIS-OC3-PFZ-2026"
    satellite_sensor: Optional[str] = "Oceansat-3 OCM-3 & SSTM"
    upwelling_index: Optional[float] = 4.2
    data_timestamp: str

# Hazard Zone Schemas
class HazardZoneCreate(BaseModel):
    name: str
    zone_type: str # "LOW_ALERT", "HIGH_ALERT", "CRITICAL_DANGER"
    latitude: float
    longitude: float
    radius_km: float
    severity: str
    description: Optional[str] = None
    active: Optional[bool] = True

class HazardZoneResponse(BaseModel):
    id: int
    name: str
    zone_type: str
    latitude: float
    longitude: float
    radius_km: float
    severity: str
    description: Optional[str]
    active: bool

    class Config:
        from_attributes = True

# Network Event Schemas
class NetworkEventCreate(BaseModel):
    event_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    details: Optional[str] = None
