import gtfs_kit as gk
from shapely.geometry import Point
from geopy.distance import geodesic

class ProcesadorGTFS:
    def __init__(self, zip_path: str, tablas: list):
        """
        Inicializa el feed GTFS y extrae las tablas solicitadas.
        """
        self.feed = gk.read_feed(zip_path, dist_units='km')
        self.datos = {}
        
        for tabla in tablas:
            if hasattr(self.feed, tabla):
                self.datos[tabla] = getattr(self.feed, tabla)
            else:
                raise ValueError(f"La tabla '{tabla}' no existe en el feed GTFS.")

    def calcular_distancia_en_traza(self, shape_id: str, lon: float, lat: float) -> float:
        """
        Calcula la distancia (en km) desde el inicio de la traza hasta el punto proyectado.
        """
        # build_geometry_by_shape() devuelve un dict: {shape_id: LineString}
        geometrias = self.feed.build_geometry_by_shape()
        
        if shape_id not in geometrias:
            raise ValueError(f"El shape_id '{shape_id}' no existe en los shapes del feed.")
            
        linea = geometrias[shape_id]
        punto_colectivo = Point(lon, lat)
        
        # Obtener el porcentaje de avance (0.0 a 1.0) sobre el LineString
        progreso = linea.project(punto_colectivo, normalized=True)
        
        # Calcular la longitud real de la traza en kilómetros
        # Extraemos los puntos de la traza ordenados
        df_shape = self.datos['shapes'] if 'shapes' in self.datos else self.feed.shapes
        puntos_traza = (
            df_shape[df_shape['shape_id'] == shape_id]
            .sort_values('shape_pt_sequence')[['shape_pt_lat', 'shape_pt_lon']]
            .to_numpy()
        )
        
        # Sumamos la distancia geodésica punto a punto
        distancia_total_km = sum(
            geodesic(puntos_traza[i], puntos_traza[i + 1]).km
            for i in range(len(puntos_traza) - 1)
        )
        
        # Retornar la distancia equivalente recorriendo ese porcentaje
        return progreso * distancia_total_km
    
    def calcular_distancia_fuera_de_traza(self, shape_id: str, lon: float, lat: float) -> float:
        """
        Calcula la distancia ortogonal (desvío) de un punto respecto a su traza.
        
        :param shape_id: ID de la traza (definido en shapes.txt).
        :param lon: Longitud real del colectivo.
        :param lat: Latitud real del colectivo.
        :return: Distancia en metros que el colectivo está fuera de la traza.
        """
        geometrias = self.feed.build_geometry_by_shape()
        
        if shape_id not in geometrias:
            raise ValueError(f"El shape_id '{shape_id}' no existe en los shapes del feed.")
            
        linea = geometrias[shape_id]
        punto_colectivo = Point(lon, lat)
        
        # Encontrar a qué "distancia" (en grados) a lo largo de la línea cae la proyección
        distancia_a_lo_largo = linea.project(punto_colectivo)
        
        # Obtener el objeto Point exacto sobre la traza más cercano al colectivo
        punto_proyectado = linea.interpolate(distancia_a_lo_largo)
        
        # Calcular la distancia geodésica (real) entre la posición GPS y el punto proyectado
        # geopy requiere tuplas en formato (latitud, longitud)
        coord_real = (lat, lon)
        coord_proyectada = (punto_proyectado.y, punto_proyectado.x)
        
        # Retornamos la diferencia en metros
        distancia_desvio_metros = geodesic(coord_real, coord_proyectada).meters
        
        return distancia_desvio_metros

# ==========================================
# Ejemplo de uso:
# ==========================================
if __name__ == "__main__":
    # Tablas definidas por la especificación (routes, shapes, trips, etc.)
    tablas_deseadas = ['routes', 'shapes', 'trips']
    
    # Instanciamos la clase
    procesador = ProcesadorGTFS('GTFS/GTFS.zip', tablas_deseadas)
    
    # Acceder a una de las tablas extraídas (devuelve un pd.DataFrame)
    df_shapes = procesador.datos['shapes']
    print(df_shapes.head())
    
    # Calcular distancia de un punto GPS sobre una traza específica
    distancia = procesador.calcular_distancia_en_traza(
        shape_id='010154', 
        lon=-71.085198, 
        lat=42.342916
    )
    fuera_de_ruta = procesador.calcular_distancia_fuera_de_traza(
        shape_id='010154', 
        lon=-71.085198, 
        lat=42.342916
    )
    print(f"El colectivo recorrió {distancia:.2f} km de la traza.")
    print(f"El colectivo está a {fuera_de_ruta:.2f} metros de la traza.")