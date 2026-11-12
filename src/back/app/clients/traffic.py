import httpx
from app import config
from app.cache import TTLCache, ContadorUso
from app.errors import ETAError

URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

_cache = TTLCache(config.CACHE_TRAFFIC_TTL)
_contador = ContadorUso(config.TOMTOM_USAGE_FILE, config.TOMTOM_MAX_REQUESTS)


def uso() -> dict:
    return {"usadas": _contador.usadas, "limite": _contador.limite}


def _consultar(lat: float, lon: float) -> dict:
    if not _contador.reservar():
        raise ETAError("Se alcanzó el límite configurado de consultas a TomTom", 429)
    params = {"key": config.TOMTOM_API_KEY, "point": f"{lat},{lon}", "unit": "KMPH"}
    try:
        r = httpx.get(URL, params=params, timeout=config.HTTP_TIMEOUT)
        r.raise_for_status()
        d = r.json()["flowSegmentData"]
        return {
            "current_speed": d["currentSpeed"],
            "free_flow_speed": d["freeFlowSpeed"],
            "current_travel_time": d["currentTravelTime"],
            "freeflow_travel_time": d["freeFlowTravelTime"],
        }
    except (httpx.HTTPError, KeyError) as e:
        raise ETAError(f"Error consultando la API de tráfico: {e}", 502)


def obtener_trafico(lat: float, lon: float) -> dict:
    # Clave redondeada (~110 m): colectivos cercanos reutilizan la misma respuesta
    clave = (round(lat, 3), round(lon, 3))
    return _cache.get_or_set(clave, lambda: _consultar(lat, lon))