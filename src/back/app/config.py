import os
from pathlib import Path
from dotenv import load_dotenv

BACK_DIR = Path(__file__).resolve().parents[1]   # src/back
ROOT_DIR = Path(__file__).resolve().parents[3]   # routing-engine
load_dotenv(BACK_DIR / ".env")

MBTA_API_KEY = os.getenv("MBTA_API_KEY", "")
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")
MBTA_BASE_URL = "https://api-v3.mbta.com"
ROUTE_ID = "1"

GTFS_ZIP = ROOT_DIR / "data" / "GTFS.zip"
PARADAS_CSV = ROOT_DIR / "data" / "paradas_distancia_traza.csv"
MODEL_PATH = ROOT_DIR / "models" / "modelo_eta_lgbm.pkl"

# shape_id de la traza que se usa para cada sentido (los de stops_along_route.py)
SHAPE_BY_DIRECTION = {0: "010154", 1: "010156"}

# Solo se predice para paradas futuras con diferencia > 0.03 km
MIN_DIST_RESTANTE_KM = 0.03
HTTP_TIMEOUT = 10.0

TOMTOM_MAX_REQUESTS = int(os.getenv("TOMTOM_MAX_REQUESTS", "9000"))  # margen bajo el tope de 10 mil
TOMTOM_USAGE_FILE = ROOT_DIR / "data" / "tomtom_usage.json"

CACHE_VEHICLES_TTL = 10    # segundos
CACHE_TRAFFIC_TTL = 120
CACHE_WEATHER_TTL = 600