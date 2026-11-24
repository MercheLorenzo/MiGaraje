import httpx
import os

from app.core.config import settings


class VehicleNotFoundError(Exception):
    pass


class VehicleServiceUnavailableError(Exception):
    pass


def _headers() -> dict[str, str]:
    """La clave interna se envía solo si existe, como en la API original."""
    key = os.getenv("INTERNAL_API_KEY")
    return {"X-Internal-Key": key} if key else {}


def get_vehicle_mileages() -> dict[int, int]:
    """Consulta los kilómetros una vez para el listado entero, sin N+1 peticiones."""
    url = f"{settings.vehicles_service_url.rstrip('/')}/vehicles"
    try:
        headers = _headers()
        kwargs = {"headers": headers} if headers else {}
        response = httpx.get(url, **kwargs, timeout=5.0)
        if response.status_code != 200:
            raise VehicleServiceUnavailableError(
                f"vehicles-service devolvió HTTP {response.status_code}"
            )
        vehicles = response.json()
        if not isinstance(vehicles, list):
            raise ValueError("La lista de vehículos no es una lista")
        return {int(v["id"]): int(v["current_mileage"]) for v in vehicles}
    except (httpx.RequestError, ValueError, TypeError, KeyError) as exc:
        raise VehicleServiceUnavailableError(
            "No se puede consultar el kilometraje actual de los vehículos"
        ) from exc


def verify_vehicle_exists(vehicle_id: int) -> None:
    url = f"{settings.vehicles_service_url.rstrip('/')}/vehicles/{vehicle_id}"

    try:
        headers = _headers()
        response = httpx.get(url, **({"headers": headers} if headers else {}), timeout=5.0)
    except httpx.RequestError as exc:
        raise VehicleServiceUnavailableError from exc

    if response.status_code == 404:
        raise VehicleNotFoundError

    if response.status_code >= 500:
        raise VehicleServiceUnavailableError

    if response.status_code != 200:
        raise VehicleServiceUnavailableError
