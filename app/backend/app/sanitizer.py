"""
Sanitización: lista de pasos (funciones dict -> dict). Para cambiar el proceso,
editá DEFAULT_STEPS: agregá, quitá o reordená pasos. Cada paso recibe el registro
con el esquema de sample.csv y devuelve el registro modificado.
"""
from datetime import datetime
from math import cos, pi, sin
from typing import Callable
from zoneinfo import ZoneInfo

Step = Callable[[dict], dict]

OCUPACION = {
    "EMPTY": 0, "MANY_SEATS_AVAILABLE": 1, "FEW_SEATS_AVAILABLE": 2,
    "STANDING_ROOM_ONLY": 3, "CRUSHED_STANDING_ROOM_ONLY": 4, "FULL": 5,
}


def _local_dt(r: dict) -> datetime:
    tz = ZoneInfo(r.get("timezone") or "America/New_York")
    try:
        dt = datetime.fromisoformat(r["date_time"])
        return dt.astimezone(tz) if dt.tzinfo else dt.replace(tzinfo=tz)
    except Exception:
        return datetime.now(tz)


def add_time_features(r: dict) -> dict:
    dt = _local_dt(r)
    hora_dec = dt.hour + dt.minute / 60
    r["hora"], r["minuto"] = dt.hour, dt.minute
    r["dia_semana"] = dt.weekday()
    r["es_finde"] = dt.weekday() >= 5
    r["hora_sin"] = sin(2 * pi * hora_dec / 24)
    r["hora_cos"] = cos(2 * pi * hora_dec / 24)
    return r


def add_traffic_ratios(r: dict) -> dict:
    cur, free = r.get("current_travel_time"), r.get("freeflow_travel_time")
    if cur is not None and free:
        r["ratio_congestion"] = cur / free
        r["demora_s"] = cur - free
    cs, fs = r.get("current_speed"), r.get("free_flow_speed")
    if cs is not None and fs:
        r["ratio_velocidad"] = cs / fs
    return r


def add_status_features(r: dict) -> dict:
    r["detenido"] = int(r.get("current_status") == "STOPPED_AT")
    r["ocupacion_ord"] = OCUPACION.get(r.get("occupancy_status"))
    return r


DEFAULT_STEPS: list[Step] = [add_time_features, add_traffic_ratios, add_status_features]


class Sanitizer:
    def __init__(self, steps: list[Step] | None = None):
        self.steps = steps if steps is not None else DEFAULT_STEPS

    def sanitize(self, raw: dict) -> dict:
        data = dict(raw)
        for step in self.steps:
            data = step(data)
        return data


def get_sanitizer() -> Sanitizer:
    return Sanitizer()