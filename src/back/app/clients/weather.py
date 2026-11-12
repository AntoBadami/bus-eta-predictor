import httpx
from app import config
from app.errors import ETAError
from app.cache import TTLCache

_cache = TTLCache(config.CACHE_WEATHER_TTL)

CAMPOS = ["temperature_2m", "precipitation", "relative_humidity_2m", "weather_code", "is_day"]


def _consultar(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join(CAMPOS),
        "timezone": "UTC",
    }
    try:
        r = httpx.get("https://api.open-meteo.com/v1/forecast", params=params,
                      timeout=config.HTTP_TIMEOUT)
        r.raise_for_status()
        actual = r.json()["current"]
        return {c: actual[c] for c in CAMPOS}
    except (httpx.HTTPError, KeyError) as e:
        raise ETAError(f"Error consultando la API de clima: {e}", 502)


def obtener_clima(lat: float, lon: float) -> dict:
    clave = (round(lat, 2), round(lon, 2))
    return _cache.get_or_set(clave, lambda: _consultar(lat, lon))
