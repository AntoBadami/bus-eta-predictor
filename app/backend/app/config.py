import os
from dotenv import load_dotenv

load_dotenv()

# --- Ruta monitoreada (igual que el bot) ---
ROUTE_ID = "1"
SHAPES = {0: "010154", 1: "010156"}      # direction_id -> shape_id
PATTERNS = {0: "1-_-0", 1: "1-_-1"}      # direction_id -> route_pattern_id
DEVIATION_THRESHOLD_M = 70.0             # metros fuera de traza => desvío

# --- APIs ---
MBTA_BASE_URL = "https://api-v3.mbta.com"
MBTA_TOKEN = os.getenv("MBTA_TOKEN")
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
HTTP_TIMEOUT = 10

# --- Archivos ---
GTFS_PATH = os.getenv("GTFS_PATH", "data/GTFS.zip")
MODEL_PATH = os.getenv("MODEL_PATH")     # si no existe, se usa el mock

# --- Features que espera el modelo (PROVISORIO: ajustar cuando se definan) ---
MODEL_FEATURES = [
    "bearing", "direction_id", "latitude", "longitude",
    "distancia_en_traza", "distancia_fuera_traza",
    "temperature_2m", "precipitation", "relative_humidity_2m", "weather_code", "is_day",
    "current_speed", "free_flow_speed", "current_travel_time", "freeflow_travel_time", "confidence",
    "hora_sin", "hora_cos", "dia_semana", "es_finde",
    "ratio_congestion", "ratio_velocidad", "demora_s",
    "detenido", "ocupacion_ord",
]