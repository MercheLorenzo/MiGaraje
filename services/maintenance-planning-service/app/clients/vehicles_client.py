import httpx

from app.core.config import settings


class VehicleNotFoundError(Exception):
    pass


class VehicleServiceUnavailableError(Exception):
    pass


def verify_vehicle_exists(vehicle_id: int) -> None:
    url = f"{settings.vehicles_service_url.rstrip('/')}/vehicles/{vehicle_id}"

    try:
        response = httpx.get(url, timeout=5.0)
    except httpx.RequestError as exc:
        raise VehicleServiceUnavailableError from exc

    if response.status_code == 404:
        raise VehicleNotFoundError

    if response.status_code >= 500:
        raise VehicleServiceUnavailableError

    if response.status_code != 200:
        raise VehicleServiceUnavailableError
