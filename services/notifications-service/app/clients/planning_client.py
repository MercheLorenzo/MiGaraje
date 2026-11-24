import httpx
from app.core.config import settings

def load(url:str):
    response=httpx.get(url,headers={"X-Internal-Key":settings.internal_api_key},timeout=12)
    response.raise_for_status()
    return response.json()

def tasks():return load(settings.planning_service_url.rstrip("/")+"/maintenance-tasks")
def vehicles():return load(settings.vehicles_service_url.rstrip("/")+"/vehicles")
def users():return load(settings.gateway_service_url.rstrip("/")+"/internal/users")
