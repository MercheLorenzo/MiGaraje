from typing import Any
import httpx
from fastapi import HTTPException
from app.core.config import settings

URLS = {
    "vehicles": lambda:settings.vehicles_service_url,
    "maintenance": lambda:settings.maintenance_service_url,
    "planning": lambda:settings.planning_service_url,
    "statistics": lambda:settings.statistics_service_url,
    "notifications": lambda:settings.notifications_service_url,
}

def call(service: str, method: str, path: str, *, data: Any=None, params: dict | None=None):
    base = URLS[service]().rstrip("/")
    try:
        with httpx.Client(timeout=12) as client:
            response = client.request(method, base+path, json=data, params={k:v for k,v in (params or {}).items() if v is not None}, headers={"X-Internal-Key":settings.internal_api_key})
    except httpx.RequestError as exc:
        raise HTTPException(503, f"El servicio {service} no está disponible") from exc
    if response.status_code >= 400:
        try:detail = response.json().get("detail", response.text)
        except ValueError:detail = response.text
        raise HTTPException(response.status_code, detail)
    if response.status_code == 204:return None
    try:return response.json()
    except ValueError:return None
