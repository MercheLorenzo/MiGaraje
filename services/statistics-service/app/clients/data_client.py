import httpx
from fastapi import HTTPException
from app.core.config import settings

def fetch(path:str,base:str):
    try:
        response=httpx.get(base.rstrip("/")+path,headers={"X-Internal-Key":settings.internal_api_key},timeout=12)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError,ValueError) as exc:
        raise HTTPException(503,"No se pueden consultar los datos para las estadísticas") from exc

def get_data():
    vehicles=fetch("/vehicles",settings.vehicles_service_url)
    maintenances=fetch("/maintenances",settings.maintenance_service_url)
    return vehicles,maintenances
