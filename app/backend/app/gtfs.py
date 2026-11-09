import zipfile
from functools import lru_cache

import pandas as pd
from geopy.distance import geodesic
from shapely.geometry import LineString, Point

from . import config


class Gtfs:
    def __init__(self, path: str):
        with zipfile.ZipFile(path) as z:
            shapes = pd.read_csv(z.open("shapes.txt"), dtype={"shape_id": str})
            self.stops = pd.read_csv(z.open("stops.txt"), dtype={"stop_id": str}).set_index("stop_id")

        self.lines, self.lengths_km = {}, {}
        for shape_id in config.SHAPES.values():
            pts = shapes[shapes["shape_id"] == shape_id].sort_values("shape_pt_sequence")
            coords = list(zip(pts["shape_pt_lon"], pts["shape_pt_lat"]))  # (lon, lat)
            if len(coords) < 2:
                raise ValueError(f"shape_id {shape_id} no está en shapes.txt (¿GTFS desactualizado?)")
            self.lines[shape_id] = LineString(coords)
            self.lengths_km[shape_id] = sum(
                geodesic((a[1], a[0]), (b[1], b[0])).km for a, b in zip(coords, coords[1:])
            )

    def project(self, shape_id: str, lat: float, lon: float) -> dict:
        """Misma lógica que el bot: km sobre la traza y metros fuera de ella."""
        line, punto = self.lines[shape_id], Point(lon, lat)
        proyectado = line.interpolate(line.project(punto))
        return {
            "shape_id": shape_id,
            "distancia_en_traza": line.project(punto, normalized=True) * self.lengths_km[shape_id],
            "distancia_fuera_traza": geodesic((lat, lon), (proyectado.y, proyectado.x)).meters,
        }

    def stop(self, stop_id: str):
        """None si no es una parada del GTFS."""
        if stop_id not in self.stops.index:
            return None
        s = self.stops.loc[stop_id]
        return {
            "id": stop_id,
            "name": s["stop_name"],
            "latitude": float(s["stop_lat"]),
            "longitude": float(s["stop_lon"]),
        }


@lru_cache(maxsize=1)
def get_gtfs() -> Gtfs:
    return Gtfs(config.GTFS_PATH)