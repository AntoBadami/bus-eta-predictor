from datetime import datetime
import numpy as np
import pandas as pd

COLUMNAS = [
    "direction_id", "distancia_en_traza", "temperature_2m", "precipitation",
    "relative_humidity_2m", "weather_code", "current_speed", "free_flow_speed",
    "current_travel_time", "freeflow_travel_time", "hora_sin", "hora_cos",
    "current_status_encoded", "dia_semana", "occupancy_encoded", "is_day_encoded",
    "velocidad_traza_kmh", "distancia_restante_km", "eta_teorico_freeflow",
    "eta_teorico_actual", "ratio_velocidad", "ratio_tiempo_via", "progreso_recorrido",
]

CATEGORICAS = ["direction_id", "weather_code", "current_status_encoded",
               "dia_semana", "occupancy_encoded", "is_day_encoded"]

STATUS_MAP = {"STOPPED_AT": 0, "IN_TRANSIT_TO": 1}   # INCOMING_AT (no mapeado) -> 1
OCCUPANCY_MAP = {"MANY_SEATS_AVAILABLE": 1, "FEW_SEATS_AVAILABLE": 2, "FULL": 3}


def _div(a, b):
    return a / b if b else float("nan")


def construir_features(vehicle: dict, clima: dict, trafico: dict, ts: datetime,
                       distancia_en_traza: float, distancia_restante: float) -> pd.DataFrame:
    seg = ts.hour * 3600 + ts.minute * 60 + ts.second
    cs, ff = trafico["current_speed"], trafico["free_flow_speed"]
    ct, ft = trafico["current_travel_time"], trafico["freeflow_travel_time"]

    fila = {
        "direction_id": int(vehicle["direction_id"]),
        "distancia_en_traza": distancia_en_traza,
        "temperature_2m": clima["temperature_2m"],
        "precipitation": clima["precipitation"],
        "relative_humidity_2m": clima["relative_humidity_2m"],
        "weather_code": float(clima["weather_code"]),
        "current_speed": cs,
        "free_flow_speed": ff,
        "current_travel_time": ct,
        "freeflow_travel_time": ft,
        "hora_sin": float(np.sin(2 * np.pi * seg / 86400)),
        "hora_cos": float(np.cos(2 * np.pi * seg / 86400)),
        "current_status_encoded": STATUS_MAP.get(vehicle["current_status"], 1),
        "dia_semana": ts.weekday(),                       # 0=Lunes ... 6=Domingo (UTC)
        "occupancy_encoded": OCCUPANCY_MAP.get(vehicle["occupancy_status"], 1),
        "is_day_encoded": int(clima["is_day"]),
        "velocidad_traza_kmh": float(cs),                 # sin ping anterior -> current_speed
        "distancia_restante_km": distancia_restante,
        "eta_teorico_freeflow": _div(distancia_restante, ff) * 3600,
        "eta_teorico_actual": _div(distancia_restante, cs) * 3600,
        "ratio_velocidad": _div(cs, ff),
        "ratio_tiempo_via": _div(ct, ft),
        "progreso_recorrido": _div(distancia_en_traza, distancia_en_traza + distancia_restante),
    }

    X = pd.DataFrame([fila], columns=COLUMNAS)
    X["is_day_encoded"] = X["is_day_encoded"].astype("Int64")
    for col in CATEGORICAS:
        X[col] = X[col].astype("category")
    return X