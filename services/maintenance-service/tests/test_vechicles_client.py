import httpx
import pytest
from unittest.mock import Mock

from app.clients import vehicles_client
from app.clients.vehicles_client import (
    VehicleNotFoundError,
    VehicleServiceUnavailableError,
)


def test_verify_vehicle_exists_success(monkeypatch):
    mock_get = Mock(return_value=Mock(status_code=200))
    monkeypatch.setattr(vehicles_client.httpx, "get", mock_get)
    monkeypatch.setattr(
        vehicles_client.settings,
        "vehicles_service_url",
        "http://vehicles-service:8000",
    )

    vehicles_client.verify_vehicle_exists(1)

    mock_get.assert_called_once_with(
        "http://vehicles-service:8000/vehicles/1",
        timeout=3.0,
    )


def test_verify_vehicle_exists_not_found(monkeypatch):
    monkeypatch.setattr(
        vehicles_client.httpx,
        "get",
        Mock(return_value=Mock(status_code=404)),
    )

    with pytest.raises(VehicleNotFoundError):
        vehicles_client.verify_vehicle_exists(999)


@pytest.mark.parametrize("status_code", [400, 401, 403, 500, 502, 503])
def test_verify_vehicle_exists_unexpected_status(
    monkeypatch,
    status_code,
):
    monkeypatch.setattr(
        vehicles_client.httpx,
        "get",
        Mock(return_value=Mock(status_code=status_code)),
    )

    with pytest.raises(VehicleServiceUnavailableError):
        vehicles_client.verify_vehicle_exists(1)


def test_verify_vehicle_exists_connection_error(monkeypatch):
    def raise_connection_error(*args, **kwargs):
        raise httpx.ConnectError("Connection failed")

    monkeypatch.setattr(
        vehicles_client.httpx,
        "get",
        raise_connection_error,
    )

    with pytest.raises(VehicleServiceUnavailableError):
        vehicles_client.verify_vehicle_exists(1)