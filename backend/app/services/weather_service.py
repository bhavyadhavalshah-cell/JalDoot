import math
import logging
import datetime
import requests
from typing import Dict, Any, Tuple, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Coastal Reference Anchor Coordinates (Within 50 km of coast / sea)
COASTAL_ANCHORS = [
    # Gujarat Coast
    (23.23, 68.60), (23.05, 68.50), (22.83, 69.36), (22.83, 69.72), (22.70, 69.55),
    (22.62, 70.05), (22.47, 70.06), (22.45, 69.70), (22.46, 69.07), (22.24, 68.96),
    (21.64, 69.60), (21.25, 69.95), (21.12, 70.11), (20.90, 70.36), (20.71, 70.98),
    (20.87, 71.36), (20.91, 71.50), (21.76, 72.15), (21.71, 72.58), (21.17, 72.83),
    (20.95, 72.92), (20.61, 72.93), (20.42, 72.83), (20.19, 72.75),
    # Maharashtra Coast
    (19.97, 72.73), (19.69, 72.76), (19.47, 72.79), (18.92, 72.83), (18.65, 72.87),
    (18.30, 72.96), (17.81, 73.09), (17.30, 73.22), (16.99, 73.30), (16.37, 73.37),
    (16.06, 73.46), (15.86, 73.63),
    # Goa Coast
    (15.72, 73.70), (15.60, 73.74), (15.49, 73.82), (15.49, 73.77), (15.39, 73.81),
    (15.14, 73.95), (15.08, 73.96), (15.01, 74.02),
    # Karnataka & Kerala Coasts
    (14.80, 74.12), (14.28, 74.45), (13.35, 74.70), (12.87, 74.84), (11.93, 75.35),
    (11.25, 75.77), (9.97, 76.22), (8.88, 76.58), (8.08, 77.55),
    # East Coast Anchors
    (8.76, 78.13), (9.28, 79.31), (10.76, 79.84), (13.08, 80.27), (17.68, 83.21),
    (20.26, 86.67), (21.63, 87.51), (21.68, 88.25)
]

def check_is_coastal_region(latitude: float, longitude: float) -> bool:
    """
    Checks if a coordinate is within 50 km of coastal or marine waters.
    Returns True for coastal/marine locations, False for inland/non-coastal locations.
    """
    R = 6371.0
    for c_lat, c_lon in COASTAL_ANCHORS:
        dlat = math.radians(c_lat - latitude)
        dlon = math.radians(c_lon - longitude)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(latitude)) * math.cos(math.radians(c_lat)) *
             math.sin(dlon / 2) ** 2)
        dist = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)) * R
        if dist <= 55.0:
            return True
    return False

_simulation_state = {
    "whatif_modifier": 0.0,
    "active": False,
    "temperature_override": None,
    "chlorophyll_override": None
}

def set_simulation_modifier(modifier: float = 0.0, sst: float = None, chlorophyll: float = None, wind: float = None, active: bool = True) -> Dict[str, Any]:
    global _simulation_state
    if sst is not None:
        thermal_deviation = abs(sst - 26.5)
        prod = 100.0 - (thermal_deviation * 16.0)
        modifier = 0.0 if prod >= 75 else (-15.0 if prod < 40 else -6.0)
    _simulation_state["whatif_modifier"] = modifier
    _simulation_state["active"] = active
    _simulation_state["temperature_override"] = sst
    _simulation_state["chlorophyll_override"] = chlorophyll
    return {
        "whatif_modifier": modifier,
        "safety_score_modifier": modifier,
        "active": active
    }

def get_simulation_state() -> Dict[str, Any]:
    return _simulation_state

def calculate_coastal_20km_wave_height(open_sea_wave: float, wind_speed_kmh: float, distance_km: float = 20.0) -> float:
    wind_m_s = wind_speed_kmh / 3.6
    wind_factor = (wind_m_s ** 1.3) * 0.045
    shelf_shoaling = 1.0 + (0.12 * (1.0 - min(distance_km, 20.0) / 20.0))
    base_wave = max(open_sea_wave, wind_factor)
    coastal_wave = base_wave * shelf_shoaling
    return round(coastal_wave, 2)

def calculate_sea_safety_score(
    wind_speed_kmh: float, 
    wave_height_m: float, 
    weather_code: int, 
    whatif_modifier: float = 0.0,
    has_hazard: bool = False,
    hazard_name: str = None,
    hazard_severity: str = None
) -> Tuple[int, str, list]:
    score = 100.0
    reasons = []

    if has_hazard and hazard_name:
        if hazard_severity == "CRITICAL":
            score -= 45.0
            reasons.append(f"CRITICAL MARITIME DANGER: Inside {hazard_name} perimeter.")
        elif hazard_severity == "HIGH":
            score -= 28.0
            reasons.append(f"HIGH ALERT HAZARD ZONE: Active hazard inside {hazard_name}.")
        else:
            score -= 15.0
            reasons.append(f"LOW ALERT MARITIME ZONE: Caution inside {hazard_name}.")

    if wind_speed_kmh > 45:
        score -= 40
        reasons.append(f"High gale wind velocity ({wind_speed_kmh} km/h) exceeds safe limits.")
    elif wind_speed_kmh > 30:
        score -= 25
        reasons.append(f"Strong winds ({wind_speed_kmh} km/h) generating choppy seas.")
    elif wind_speed_kmh > 20:
        score -= 12
        reasons.append(f"Moderate breeze ({wind_speed_kmh} km/h) with localized chop.")
    elif wind_speed_kmh > 12:
        score -= 4

    if wave_height_m > 3.0:
        score -= 45
        reasons.append(f"Severe swell ({wave_height_m}m) exceeds safe craft limit.")
    elif wave_height_m > 2.0:
        score -= 28
        reasons.append(f"Rough sea swell ({wave_height_m}m) requires caution.")
    elif wave_height_m > 1.3:
        score -= 15
        reasons.append(f"Moderate wave height ({wave_height_m}m) on coastal shelf.")
    elif wave_height_m > 0.8:
        score -= 5

    if weather_code in [95, 96, 99]:
        score -= 35
        reasons.append("Marine thunderstorm warning active in sector.")
    elif weather_code in [65, 75, 82]:
        score -= 20
        reasons.append("Heavy rainfall reducing maritime visibility.")
    elif weather_code in [61, 63, 80, 81]:
        score -= 10
    elif weather_code in [45, 48]:
        score -= 15
        reasons.append("Dense sea fog impacting optical navigation.")

    score += whatif_modifier
    score = max(5, min(100, int(score)))

    if score >= 75:
        status = "SAFE"
        if not reasons:
            reasons.append(f"Wind speed {wind_speed_kmh} km/h is within safe navigational thresholds.")
            reasons.append(f"Coastal wave swell {wave_height_m}m is favorable for traditional & mechanized craft.")
            reasons.append("Atmospheric visibility and sea surface conditions are optimal.")
    elif score >= 50:
        status = "CAUTION"
        if not reasons:
            reasons.append(f"Moderate wind and sea state ({wind_speed_kmh} km/h, {wave_height_m}m swell).")
            reasons.append("Caution advised for small artisanal craft.")
    else:
        status = "DANGEROUS"
        if not reasons:
            reasons.append("Adverse weather or active maritime danger in sector.")
            reasons.append("Do not venture into open waters. Remain in harbor or designated sheltered bays.")

    return score, status, reasons

def parse_weather_code(code: int) -> str:
    mapping = {
        0: "Clear Sky",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",
        45: "Foggy Sea",
        48: "Depositing Rime Fog",
        51: "Light Coastal Drizzle",
        53: "Moderate Drizzle",
        55: "Dense Drizzle",
        61: "Slight Rain",
        63: "Moderate Rain",
        65: "Heavy Sea Rain",
        80: "Slight Rain Showers",
        81: "Moderate Showers",
        82: "Violent Showers",
        95: "Thunderstorm",
        96: "Thunderstorm with Slight Hail",
        99: "Severe Thunderstorm with Heavy Hail"
    }
    return mapping.get(code, "Clear Marine Conditions")

def fetch_marine_and_weather(
    latitude: float, 
    longitude: float, 
    whatif_modifier: float = 0.0,
    has_hazard: bool = False,
    hazard_name: str = None,
    hazard_severity: str = None
) -> Dict[str, Any]:
    lat = latitude
    lon = longitude
    temp_c = 28.5
    wind_kmh = 16.5
    wind_deg = 230.0
    wave_m = 1.1
    wave_period = 6.2
    w_code = 0
    w_desc = "Clear Sky"

    is_coastal = check_is_coastal_region(lat, lon)

    sim = get_simulation_state()
    total_mod = whatif_modifier + (sim["whatif_modifier"] if sim["active"] else 0.0)

    try:
        marine_url = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height,wave_direction,wave_period&timezone=auto"
        res_marine = requests.get(marine_url, timeout=3.5)
        if res_marine.status_code == 200:
            m_data = res_marine.json().get("current", {})
            raw_wave = m_data.get("wave_height")
            if raw_wave is not None:
                wave_m = float(raw_wave)
            if m_data.get("wave_period") is not None:
                wave_period = float(m_data.get("wave_period"))
    except Exception as e:
        logger.debug(f"Open-Meteo Marine API fallback: {e}")

    try:
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,wind_direction_10m,weather_code&timezone=auto"
        res_weather = requests.get(weather_url, timeout=3.5)
        if res_weather.status_code == 200:
            w_data = res_weather.json().get("current", {})
            if w_data.get("temperature_2m") is not None:
                temp_c = float(w_data.get("temperature_2m"))
            if w_data.get("wind_speed_10m") is not None:
                wind_kmh = float(w_data.get("wind_speed_10m"))
            if w_data.get("wind_direction_10m") is not None:
                wind_deg = float(w_data.get("wind_direction_10m"))
            if w_data.get("weather_code") is not None:
                w_code = int(w_data.get("weather_code"))
                w_desc = parse_weather_code(w_code)
    except Exception as e:
        logger.debug(f"Open-Meteo Weather API fallback: {e}")

    if sim["active"] and sim["temperature_override"] is not None:
        temp_c = sim["temperature_override"]

    wave_m = calculate_coastal_20km_wave_height(wave_m, wind_kmh, distance_km=20.0)

    if is_coastal:
        score, status, reasons = calculate_sea_safety_score(
            wind_speed_kmh=wind_kmh, 
            wave_height_m=wave_m, 
            weather_code=w_code, 
            whatif_modifier=total_mod,
            has_hazard=has_hazard,
            hazard_name=hazard_name,
            hazard_severity=hazard_severity
        )
    else:
        # Non-coastal region: score is dashed
        score = None
        status = "NON_COASTAL"
        reasons = [
            "Device is located in an inland / non-coastal region.",
            "Safe to Sail score is active only when near coastal or marine waters."
        ]

    return {
        "latitude": lat,
        "longitude": lon,
        "is_coastal_region": is_coastal,
        "temperature_c": round(temp_c, 1),
        "wind_speed_kmh": round(wind_kmh, 1),
        "wind_direction_deg": round(wind_deg, 0),
        "wave_height_m": round(wave_m, 2),
        "wave_period_s": round(wave_period, 1),
        "weather_code": w_code,
        "weather_description": w_desc,
        "sea_safety_score": score,
        "safety_status": status,
        "safety_reasons": reasons,
        "whatif_modifier_applied": total_mod,
        "data_timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    }
