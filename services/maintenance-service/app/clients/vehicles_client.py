import httpx

from app.core.config import settings


class VehicleNotFoundError(Exception):
    """El vehículo solicitado no existe."""


class VehicleServiceUnavailableError(Exception):
    """No se puede verificar el vehículo."""


def verify_vehicle_exists(vehicle_id: int) -> None:
    url = (
        f"{settings.vehicles_service_url.rstrip('/')}"
        f"/vehicles/{vehicle_id}"
    )

    try:
        response = httpx.get(url, timeout=3.0)
    except httpx.RequestError as exc:
        raise VehicleServiceUnavailableError from exc

    if response.status_code == 404:
        raise VehicleNotFoundError

    if response.status_code != 200:
        raise VehicleServiceUnavailableError
