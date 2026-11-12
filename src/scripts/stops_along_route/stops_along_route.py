import pandas as pd
from modules.ProcesadorGTFS import ProcesadorGTFS

def obtener_distancias_paradas():
    # Mapeo de trip_id de un viaje en una ruta especifica a su respetivo shape_id
    trips_shapes = {
        '78980885': '010154',
        '78980952': '010156'
    }
    
    # Cargar las tablas GTFS necesarias
    tablas_requeridas = ['stop_times', 'stops', 'trips', 'shapes']
    procesador = ProcesadorGTFS('data/GTFS.zip', tablas_requeridas)
    
    df_stop_times = procesador.datos['stop_times']
    df_stops = procesador.datos['stops']
    
    registros = []
    
    # Recorrer los trips y calcular la distancia sobre la traza para cada parada
    for trip_id, shape_id in trips_shapes.items():
        # Filtrar paradas del viaje y ordenar secuencialmente
        st_trip = df_stop_times[df_stop_times['trip_id'] == str(trip_id)].sort_values('stop_sequence')
        
        # Cruzar con stops.txt para obtener coordenadas lat/lon
        st_trip_full = st_trip.merge(df_stops, on='stop_id', how='left')
        
        for _, row in st_trip_full.iterrows():
            stop_id = row['stop_id']
            lat = float(row['stop_lat'])
            lon = float(row['stop_lon'])
            stop_sequence = row['stop_sequence']
            
            # Calcular la distancia proyectada usando el método de ProcesadorGTFS
            distancia_km = procesador.calcular_distancia_en_traza(shape_id, lon, lat)
            
            registros.append({
                'trip_id': trip_id,
                'shape_id': shape_id,
                'stop_sequence': stop_sequence,
                'stop_id': stop_id,
                'stop_lat': lat,
                'stop_lon': lon,
                'distancia_parada_traza_km': round(distancia_km, 4)
            })
            
    # Generar el DataFrame final y exportar a CSV
    df_resultado = pd.DataFrame(registros)
    
    archivo_salida = 'data/paradas_distancia_traza.csv'
    df_resultado.to_csv(archivo_salida, index=False, encoding='utf-8')
    print(f"Archivo CSV generado correctamente: {archivo_salida}")

if __name__ == "__main__":
    obtener_distancias_paradas()