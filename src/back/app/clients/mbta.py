import httpx
from app import config
from app.errors import ETAError
from app.cache import TTLCache

def _consultar_vehiculos(direction_id: int) -> list[dict]:
    headers = {"x-api-key": config.MBTA_API_KEY} if config.MBTA_API_KEY else {}
    params = {"filter[route]": config.ROUTE_ID, "filter[direction_id]": direction_id}
    try:
        r = httpx.get(f"{config.MBTA_BASE_URL}/vehicles", params=params,
                      headers=headers, timeout=config.HTTP_TIMEOUT)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise ETAError(f"Error consultando la API de MBTA: {e}", 502)

    vehiculos = []
    for item in r.json().get("data", []):
        a = item["attributes"]
        if a.get("latitude") is None or a.get("longitude") is None:
            continue
        trip = ((item.get("relationships") or {}).get("trip") or {}).get("data")
        vehiculos.append({
            "id": item["id"],
            "label": a.get("label") or item["id"],
            "direction_id": a.get("direction_id"),
            "latitude": a["latitude"],
            "longitude": a["longitude"],
            "current_status": a.get("current_status"),
            "occupancy_status": a.get("occupancy_status"),
            "updated_at": a.get("updated_at"),
            "trip_id": trip["id"] if trip else None,
        })
    return vehiculos

_cache = TTLCache(config.CACHE_VEHICLES_TTL)


def listar_vehiculos(direction_id: int) -> list[dict]:
    return _cache.get_or_set(direction_id, lambda: _consultar_vehiculos(direction_id))