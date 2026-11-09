import requests
from fastapi import FastAPI, HTTPException, Query

from . import clients, config
from .gtfs import get_gtfs
from .predictor import get_predictor
from .sanitizer import get_sanitizer

app = FastAPI(title="ETA colectivos - ruta 1 MBTA")


def _bus(v: dict) -> dict:
    a = v["attributes"]
    return {
        "id": v["id"],
        "label": a.get("label"),
        "current_status": a.get("current_status"),
        "direction_id": a.get("direction_id"),
        "occupancy_status": a.get("occupancy_status"),
        "latitude": a.get("latitude"),
        "longitude": a.get("longitude"),
        "bearing": a.get("bearing"),
        "updated_at": a.get("updated_at"),
    }


@app.get("/api/vehicles")
def list_vehicles(direction: int = Query(..., ge=0, le=1)):
    try:
        data = clients.mbta_vehicles(direction)
    except requests.RequestException as e:
        raise HTTPException(502, f"Error consultando MBTA: {e}")
    return [
        _bus(v) for v in data.get("data", [])
        if v["attributes"].get("latitude") is not None
    ]


@app.get("/api/vehicles/{bus_id}/eta")
def eta(bus_id: str):
    try:
        data = clients.mbta_vehicle(bus_id)
    except requests.RequestException as e:
        if getattr(e.response, "status_code", None) == 404:
            raise HTTPException(404, "Colectivo no encontrado (puede haber terminado su recorrido)")
        raise HTTPException(502, f"Error consultando MBTA: {e}")

    v = data["data"]
    a, rel = v["attributes"], v.get("relationships", {})
    if (rel.get("route", {}).get("data") or {}).get("id") != config.ROUTE_ID:
        raise HTTPException(404, "Ese colectivo no pertenece a la ruta 1")

    lat, lon, direction = a["latitude"], a["longitude"], a["direction_id"]
    warnings = []

    # Traza y parada (GTFS)
    gtfs = get_gtfs()
    trace = gtfs.project(config.SHAPES[direction], lat, lon)
    trace["es_desvio"] = trace["distancia_fuera_traza"] > config.DEVIATION_THRESHOLD_M
    if trace["es_desvio"]:
        warnings.append("El colectivo está fuera de su traza: la predicción puede no ser confiable.")

    stop_id = ((rel.get("stop") or {}).get("data") or {}).get("id")
    stop = gtfs.stop(stop_id) if stop_id else None
    if stop:
        stop["current_status"] = a.get("current_status")
        stop["note"] = (
            "El colectivo está detenido en esta parada"
            if a.get("current_status") == "STOPPED_AT"
            else "Próxima parada del colectivo"
        )
    elif stop_id:
        warnings.append(f"La parada {stop_id} no figura en el GTFS cargado.")

    # Horario, clima y tránsito (igual que el bot: sin tránsito si hay desvío)
    local_time = clients.get_local_time(lat, lon)
    weather = clients.get_weather(lat, lon)
    traffic = None if trace["es_desvio"] else clients.get_traffic(lat, lon)
    if weather is None:
        warnings.append("No se pudo obtener el clima.")
    if traffic is None and not trace["es_desvio"]:
        warnings.append("No se pudo obtener el tránsito (¿falta TOMTOM_API_KEY?).")

    # Registro crudo con el esquema de sample.csv
    raw = {
        "bearing": a.get("bearing"),
        "current_status": a.get("current_status"),
        "direction_id": direction,
        "occupancy_status": a.get("occupancy_status"),
        "latitude": lat,
        "longitude": lon,
        "bus_id": v["id"],
        "route_pattern_id": config.PATTERNS[direction],
        "stop_id": stop_id,
        "current_stop_sequence": a.get("current_stop_sequence"),
        **trace,
        **local_time,
        **(weather or {}),
        **(traffic or {}),
    }

    features = get_sanitizer().sanitize(raw)
    predictor = get_predictor()
    try:
        eta_seconds = predictor.predict(features)
    except Exception as e:
        raise HTTPException(500, f"Error en el modelo: {e}")

    return {
        "bus": _bus(v),
        "stop": stop,
        "trace": trace,
        "weather": weather,
        "traffic": traffic,
        "time": local_time,
        "features": features,
        "eta_seconds": eta_seconds,
        "is_mock": predictor.is_mock,
        "warnings": warnings,
    }