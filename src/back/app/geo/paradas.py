import zipfile
import pandas as pd
from app.errors import ETAError


class CatalogoParadas:
    def __init__(self, csv_path, gtfs_zip_path, shape_by_direction: dict):
        # dtype=str: si no, el shape_id '010154' pierde el cero inicial
        df = pd.read_csv(csv_path, dtype={"trip_id": str, "shape_id": str, "stop_id": str})

        with zipfile.ZipFile(gtfs_zip_path) as z:
            with z.open("stops.txt") as f:
                stops = pd.read_csv(f, dtype=str, usecols=["stop_id", "stop_name"])
        nombres = dict(zip(stops["stop_id"], stops["stop_name"]))

        self._por_direccion = {}
        for direccion, shape_id in shape_by_direction.items():
            sub = df[df["shape_id"] == shape_id].sort_values("stop_sequence")
            self._por_direccion[direccion] = [
                {
                    "stop_id": r.stop_id,
                    "stop_name": nombres.get(r.stop_id, r.stop_id),
                    "stop_sequence": int(r.stop_sequence),
                    "stop_lat": float(r.stop_lat),
                    "stop_lon": float(r.stop_lon),
                    "distancia_parada_traza_km": float(r.distancia_parada_traza_km),
                }
                for r in sub.itertuples()
            ]

    def listar(self, direction_id: int) -> list[dict]:
        return self._por_direccion.get(direction_id, [])

    def obtener(self, direction_id: int, stop_id: str) -> dict:
        for p in self.listar(direction_id):
            if p["stop_id"] == stop_id:
                return p
        raise ETAError("La parada no pertenece a ese sentido de la ruta 1", 404)