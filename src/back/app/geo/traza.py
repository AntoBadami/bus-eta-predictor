import zipfile
import pandas as pd
from shapely.geometry import LineString, Point
from geopy.distance import geodesic


class ProcesadorTraza:
    def __init__(self, gtfs_zip_path, shape_ids):
        with zipfile.ZipFile(gtfs_zip_path) as z:
            with z.open("shapes.txt") as f:
                shapes = pd.read_csv(f, dtype={"shape_id": str})

        self._lineas = {}
        self._largos_km = {}
        for sid in shape_ids:
            pts = (
                shapes[shapes["shape_id"] == sid]
                .sort_values("shape_pt_sequence")[["shape_pt_lat", "shape_pt_lon"]]
                .to_numpy()
            )
            if len(pts) < 2:
                raise ValueError(f"El shape_id '{sid}' no existe en shapes.txt")
            self._lineas[sid] = LineString([(lon, lat) for lat, lon in pts])
            self._largos_km[sid] = sum(
                geodesic(pts[i], pts[i + 1]).km for i in range(len(pts) - 1)
            )

    def distancia_en_traza(self, shape_id: str, lon: float, lat: float) -> float:
        linea = self._lineas[shape_id]
        progreso = linea.project(Point(lon, lat), normalized=True)
        return progreso * self._largos_km[shape_id]

    def distancia_fuera_de_traza(self, shape_id: str, lon: float, lat: float) -> float:
        linea = self._lineas[shape_id]
        proyectado = linea.interpolate(linea.project(Point(lon, lat)))
        return geodesic((lat, lon), (proyectado.y, proyectado.x)).meters