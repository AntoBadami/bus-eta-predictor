from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app import config
from app.clients import mbta, weather, traffic
from app.errors import ETAError
from app.features import construir_features


def _parse_ts(s: str | None) -> datetime:
    if not s:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


class ETAService:
    def __init__(self, traza, paradas, sanitizer, modelo):
        self.traza = traza
        self.paradas = paradas
        self.sanitizer = sanitizer
        self.modelo = modelo

    def vehiculos(self, direction_id: int) -> list[dict]:
        return mbta.listar_vehiculos(direction_id)

    def listar_paradas(self, direction_id: int) -> list[dict]:
        return self.paradas.listar(direction_id)

    def calcular_eta(self, vehicle_id: str, direction_id: int, stop_id: str) -> dict:
        vehiculo = next((v for v in mbta.listar_vehiculos(direction_id)
                         if v["id"] == vehicle_id), None)
        if vehiculo is None:
            raise ETAError("El colectivo ya no está circulando en ese sentido", 404)
        parada = self.paradas.obtener(direction_id, stop_id)
        shape_id = config.SHAPE_BY_DIRECTION[direction_id]

        lat, lon = vehiculo["latitude"], vehiculo["longitude"]
        clima = weather.obtener_clima(lat, lon)
        trafico = traffic.obtener_trafico(lat, lon)
        ts = _parse_ts(vehiculo["updated_at"])

        # --- Sanitización (módulo intercambiable) ---
        raw = self.sanitizer.sanitize(
            {"vehicle": vehiculo, "clima": clima, "trafico": trafico, "timestamp": ts}
        )
        vehiculo, clima, trafico, ts = raw["vehicle"], raw["clima"], raw["trafico"], raw["timestamp"]

        dist = self.traza.distancia_en_traza(shape_id, lon, lat)
        desvio_m = self.traza.distancia_fuera_de_traza(shape_id, lon, lat)
        restante = parada["distancia_parada_traza_km"] - dist
        if restante <= config.MIN_DIST_RESTANTE_KM:
            raise ETAError("El colectivo ya pasó por esa parada o está llegando a ella", 409)

        X = construir_features(vehiculo, clima, trafico, ts, dist, restante)

        # --- Predicción (modelo intercambiable) ---
        eta = self.modelo.predict(X)

        return {
            "eta_seconds": round(eta, 1),
            "vehicle": vehiculo,
            "stop": parada,
            "clima": clima,
            "trafico": trafico,
            "horario": {
                "timestamp_utc": ts.isoformat(),
                "hora_boston": ts.astimezone(ZoneInfo("America/New_York")).strftime("%H:%M:%S"),
                "dia_semana": ts.weekday(),
            },
            "distancias": {
                "distancia_en_traza_km": round(dist, 3),
                "distancia_restante_km": round(restante, 3),
                "desvio_traza_m": round(desvio_m, 1),
            },
        }
    