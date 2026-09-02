import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Query, Depends
from app.models import OceanData, User
from app.auth import get_current_admin
from app.services.weather_service import set_simulation_modifier, get_simulation_state

router = APIRouter(prefix="/researcher", tags=["Researcher & Ocean Analytics"])

HISTORICAL_SERIES = {
    "Porbandar Offshore": {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "sst": [24.5, 25.1, 26.3, 27.8, 29.2, 28.5, 27.6, 27.1, 27.9, 28.4, 26.7, 25.2],
        "chlorophyll": [1.8, 2.1, 2.6, 2.9, 2.3, 3.4, 3.8, 3.6, 3.1, 2.8, 2.2, 1.9],
        "fish_productivity": [68, 74, 86, 82, 65, 88, 92, 89, 85, 84, 78, 70]
    },
    "Veraval Deep Trench": {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "sst": [25.0, 25.6, 26.8, 28.2, 29.6, 28.9, 28.1, 27.5, 28.2, 28.7, 27.1, 25.8],
        "chlorophyll": [2.2, 2.5, 3.1, 3.4, 2.8, 4.1, 4.5, 4.2, 3.7, 3.3, 2.7, 2.3],
        "fish_productivity": [72, 79, 91, 88, 70, 94, 98, 95, 90, 88, 83, 75]
    },
    "Gulf of Khambhat": {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "sst": [23.8, 24.5, 25.9, 27.4, 28.9, 28.0, 27.2, 26.8, 27.4, 27.9, 26.1, 24.6],
        "chlorophyll": [1.5, 1.8, 2.2, 2.5, 2.0, 3.0, 3.3, 3.1, 2.7, 2.4, 1.9, 1.6],
        "fish_productivity": [60, 67, 80, 76, 58, 82, 85, 83, 79, 77, 71, 63]
    },
    "Mumbai High Marine": {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "sst": [25.5, 26.0, 27.2, 28.6, 29.9, 29.1, 28.4, 27.9, 28.6, 29.0, 27.6, 26.3],
        "chlorophyll": [2.0, 2.3, 2.8, 3.0, 2.5, 3.8, 4.0, 3.8, 3.4, 3.0, 2.4, 2.1],
        "fish_productivity": [70, 77, 89, 85, 68, 91, 95, 92, 88, 86, 80, 73]
    }
}

@router.get("/historical-trends")
def get_historical_ocean_trends(
    region: str = Query("Porbandar Offshore"),
    current_admin: User = Depends(get_current_admin)
):
    """Admin-only: Historical monthly SST and Chlorophyll trends"""
    data = HISTORICAL_SERIES.get(region, HISTORICAL_SERIES["Porbandar Offshore"])
    return {
        "region": region,
        "available_regions": list(HISTORICAL_SERIES.keys()),
        "metrics": data
    }

@router.get("/what-if-simulation")
def simulate_fish_productivity(
    sst: float = Query(26.5, description="Hypothetical Sea Surface Temperature in °C (20 to 34)"),
    chlorophyll: float = Query(2.5, description="Hypothetical Chlorophyll-a in mg/m³ (0.5 to 6.0)"),
    wind_speed: float = Query(15.0, description="Hypothetical Wind Speed in km/h (0 to 60)"),
    current_admin: User = Depends(get_current_admin)
):
    """
    Admin-only: Calculates simulated productivity and dynamically links into fisherman Sea Safety Score.
    """
    optimal_sst = 26.5
    thermal_deviation = abs(sst - optimal_sst)
    
    productivity = 100.0 - (thermal_deviation * 16.0) + (min(chlorophyll, 5.0) * 8.0) - (max(0, wind_speed - 20.0) * 0.8)
    clamped_productivity = max(5.0, min(100.0, round(productivity, 1)))

    if sst < 25.0:
        target_species = ["Hilsa", "Croaker (Ghol)", "Silver Pomfret"]
        ecological_note = "Cold upwelling zone detected: High nutrient influx promoting benthic and demersal fish."
    elif sst <= 28.0:
        target_species = ["Indian Mackerel", "Yellowfin Tuna", "Kingfish (Surmai)", "Squid"]
        ecological_note = "Optimal thermal window: High pelagic schooling activity around thermal front boundaries."
    else:
        target_species = ["Deep Water Snapper", "Barracuda", "Skipjack Tuna"]
        ecological_note = "Thermal stress threshold: Fish migration towards deeper, cooler shelf waters."

    # Update global modifier affecting fisherman safety score
    sim_state = set_simulation_modifier(sst=sst, chlorophyll=chlorophyll, wind=wind_speed)

    # Also compute dynamic curve across temperatures for secondary graph
    temp_curve_labels = [f"{t}°C" for t in range(20, 35)]
    temp_curve_data = []
    for t in range(20, 35):
        t_dev = abs(t - 26.5)
        p = max(5.0, min(100.0, round(100.0 - (t_dev * 16.0) + (min(chlorophyll, 5.0) * 8.0) - (max(0, wind_speed - 20.0) * 0.8), 1)))
        temp_curve_data.append(p)

    return {
        "input_sst": sst,
        "input_chlorophyll": chlorophyll,
        "input_wind_speed": wind_speed,
        "fish_productivity_score": clamped_productivity,
        "safety_modifier_applied": sim_state["safety_score_modifier"],
        "confidence_score": 91,
        "target_species": target_species,
        "ecological_advisory": ecological_note,
        "biomass_density_estimate": f"{round(clamped_productivity * 18.2, 0)} kg/km²",
        "curve_labels": temp_curve_labels,
        "curve_data": temp_curve_data
    }
