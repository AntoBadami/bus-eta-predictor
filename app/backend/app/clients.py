from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from . import config


def _get(url, **kwargs):
    r = requests.get(url, timeout=config.HTTP_TIMEOUT, **kwargs)
    r.raise_for_status()
    return r.json()


def _mbta_headers():
    return {"x-api-key": config.MBTA_TOKEN} if config.MBTA_TOKEN else {}


# ---------- MBTA ----------
def mbta_vehicles(direction_id: int) -> dict:
    params = {
        "filter[route]": config.ROUTE_ID,
        "filter[direction_id]": direction_id,
    }
    return _get(f"{config.MBTA_BASE_URL}/vehicles", params=params, headers=_mbta_headers())


def mbta_vehicle(bus_id: str) -> dict:
    return _get(
        f"{config.MBTA_BASE_URL}/vehicles/{bus_id}",
        params={"include": "stop"},
        headers=_mbta_headers(),
    )


# ---------- Clima (Open-Meteo) ----------
def get_weather(lat: float, lon: float):
    try:
        data = _get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,precipitation,is_day,weather_code,relative_humidity_2m",
            },
        )
        c = data.get("current", {})
        return {
            "temperature_2m": c.get("temperature_2m"),
            "precipitation": c.get("precipitation"),
            "relative_humidity_2m": c.get("relative_humidity_2m"),
            "weather_code": c.get("weather_code"),
            "is_day": bool(c["is_day"]) if c.get("is_day") is not None else None,
        }
    except Exception:
        return None


# ---------- Tránsito (TomTom) ----------
def get_traffic(lat: float, lon: float):
    if not config.TOMTOM_API_KEY:
        return None
    try:
        data = _get(
            "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json",
            params={"key": config.TOMTOM_API_KEY, "point": f"{lat},{lon}", "unit": "KMPH"},
        )
        f = data.get("flowSegmentData", {})
        return {
            "current_speed": f.get("currentSpeed"),
            "free_flow_speed": f.get("freeFlowSpeed"),
            "current_travel_time": f.get("currentTravelTime"),
            "freeflow_travel_time": f.get("freeFlowTravelTime"),
            "confidence": f.get("confidence"),
            "road_closure": f.get("roadClosure"),
        }
    except Exception:
        return None


# ---------- Horario (timeapi.io, con fallback) ----------
def get_local_time(lat: float, lon: float) -> dict:
    try:
        d = _get(
            "https://timeapi.io/api/v1/time/current/coordinate",
            params={"latitude": lat, "longitude": lon},
        )
        return {"date_time": d["date_time"], "timezone": d["timezone"]}
    except Exception:
        tz = "America/New_York"
        return {"date_time": datetime.now(ZoneInfo(tz)).isoformat(), "timezone": tz}