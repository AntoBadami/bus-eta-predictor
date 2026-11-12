from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app import config
from app.errors import ETAError
from app.geo.traza import ProcesadorTraza
from app.geo.paradas import CatalogoParadas
from app.sanitizer.base import PassthroughSanitizer
from app.model.lgbm import LGBMETAModel
from app.service import ETAService
from app.clients import traffic

app = FastAPI(title="ETA colectivos MBTA - ruta 1")

# Para cambiar la sanitización o el modelo en el futuro, solo se tocan estas dos líneas:
sanitizer = PassthroughSanitizer()
modelo = LGBMETAModel(config.MODEL_PATH)

servicio = ETAService(
    traza=ProcesadorTraza(config.GTFS_ZIP, set(config.SHAPE_BY_DIRECTION.values())),
    paradas=CatalogoParadas(config.PARADAS_CSV, config.GTFS_ZIP, config.SHAPE_BY_DIRECTION),
    sanitizer=sanitizer,
    modelo=modelo,
)


class ETARequest(BaseModel):
    vehicle_id: str
    direction_id: int
    stop_id: str


@app.exception_handler(ETAError)
async def eta_error_handler(request, exc: ETAError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/api/vehicles")
def vehicles(direction: int = Query(..., ge=0, le=1)):
    return servicio.vehiculos(direction)


@app.get("/api/stops")
def stops(direction: int = Query(..., ge=0, le=1)):
    return servicio.listar_paradas(direction)


@app.post("/api/eta")
def eta(req: ETARequest):
    return servicio.calcular_eta(req.vehicle_id, req.direction_id, req.stop_id)

@app.get("/api/usage")
def usage():
    return {"tomtom": traffic.uso()}