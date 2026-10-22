from datetime import date
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main as main_module
from app.clients.vehicles_client import (
    VehicleNotFoundError,
    VehicleServiceUnavailableError,
)
from app.db.session import Base, get_db
from app.main import app
from app.models import MaintenanceRule, MaintenanceTask
from app.services import maintenance_rule_service, maintenance_task_service


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def vehicle_exists(vehicle_id: int) -> None:
    return None


def vehicle_not_found(vehicle_id: int) -> None:
    raise VehicleNotFoundError


def vehicles_service_unavailable(vehicle_id: int) -> None:
    raise VehicleServiceUnavailableError


@pytest.fixture
def client(monkeypatch):
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    app.dependency_overrides[get_db] = override_get_db

    monkeypatch.setattr(
        maintenance_rule_service,
        "verify_vehicle_exists",
        vehicle_exists,
    )
    monkeypatch.setattr(
        maintenance_task_service,
        "verify_vehicle_exists",
        vehicle_exists,
    )

    test_client = TestClient(app)

    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)


def rule_payload(**overrides):
    payload = {
        "vehicle_id": 1,
        "name": "Cambio de aceite",
        "maintenance_type": "oil_change",
        "description": "Cambio periódico de aceite y filtro",
        "interval_days": 180,
        "interval_months": None,
        "interval_kilometers": 10000,
        "last_performed_date": "2026-01-15",
        "last_performed_mileage": 45000,
        "reminder_days_before": 7,
        "is_active": True,
    }
    payload.update(overrides)
    return payload


def task_payload(**overrides):
    payload = {
        "vehicle_id": 1,
        "rule_id": None,
        "name": "Revisar aceite",
        "description": "Revisión del nivel de aceite",
        "due_date": "2026-12-15",
        "due_mileage": 55000,
    }
    payload.update(overrides)
    return payload


def create_rule(client, **overrides):
    response = client.post(
        "/maintenance-rules",
        json=rule_payload(**overrides),
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_task(client, **overrides):
    response = client.post(
        "/maintenance-tasks",
        json=task_payload(**overrides),
    )
    assert response.status_code == 201, response.text
    return response.json()


# Reglas de mantenimiento

def test_create_maintenance_rule(client):
    response = client.post(
        "/maintenance-rules",
        json=rule_payload(),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["vehicle_id"] == 1
    assert data["name"] == "Cambio de aceite"
    assert data["interval_days"] == 180
    assert data["interval_kilometers"] == 10000


def test_create_rule_without_any_interval(client):
    payload = rule_payload(
        interval_days=None,
        interval_months=None,
        interval_kilometers=None,
    )

    response = client.post("/maintenance-rules", json=payload)

    assert response.status_code == 422


def test_create_rule_with_invalid_vehicle_id(client):
    response = client.post(
        "/maintenance-rules",
        json=rule_payload(vehicle_id=0),
    )

    assert response.status_code == 422


def test_create_rule_with_nonexistent_vehicle(client, monkeypatch):
    monkeypatch.setattr(
        maintenance_rule_service,
        "verify_vehicle_exists",
        vehicle_not_found,
    )

    response = client.post(
        "/maintenance-rules",
        json=rule_payload(vehicle_id=9999),
    )

    assert response.status_code == 422


def test_create_rule_when_vehicles_service_is_unavailable(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        maintenance_rule_service,
        "verify_vehicle_exists",
        vehicles_service_unavailable,
    )

    response = client.post(
        "/maintenance-rules",
        json=rule_payload(),
    )

    assert response.status_code == 503


def test_list_maintenance_rules(client):
    create_rule(client)
    create_rule(client, vehicle_id=2, name="Revisión de neumáticos")

    response = client.get("/maintenance-rules")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_rules_by_vehicle(client):
    create_rule(client, vehicle_id=1)
    create_rule(client, vehicle_id=2, name="Revisión de neumáticos")

    response = client.get("/maintenance-rules?vehicle_id=1")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["vehicle_id"] == 1


def test_get_maintenance_rule_by_id(client):
    created = create_rule(client)

    response = client.get(f"/maintenance-rules/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Cambio de aceite"


def test_get_nonexistent_rule(client):
    response = client.get("/maintenance-rules/999")

    assert response.status_code == 404


def test_update_maintenance_rule(client):
    created = create_rule(client)

    response = client.put(
        f"/maintenance-rules/{created['id']}",
        json=rule_payload(
            name="Cambio completo de aceite",
            interval_kilometers=12000,
        ),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Cambio completo de aceite"
    assert response.json()["interval_kilometers"] == 12000


def test_update_nonexistent_rule(client):
    response = client.put(
        "/maintenance-rules/999",
        json=rule_payload(),
    )

    assert response.status_code == 404


def test_delete_maintenance_rule(client):
    created = create_rule(client)

    response = client.delete(f"/maintenance-rules/{created['id']}")

    assert response.status_code == 204
    assert client.get(
        f"/maintenance-rules/{created['id']}"
    ).status_code == 404


def test_delete_nonexistent_rule(client):
    response = client.delete("/maintenance-rules/999")

    assert response.status_code == 404


# Tareas de mantenimiento

def test_create_maintenance_task(client):
    response = client.post(
        "/maintenance-tasks",
        json=task_payload(),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["vehicle_id"] == 1
    assert data["name"] == "Revisar aceite"
    assert data["status"] == "pending"


def test_create_task_without_due_date_or_mileage(client):
    response = client.post(
        "/maintenance-tasks",
        json=task_payload(due_date=None, due_mileage=None),
    )

    assert response.status_code == 422


def test_create_task_with_invalid_vehicle_id(client):
    response = client.post(
        "/maintenance-tasks",
        json=task_payload(vehicle_id=0),
    )

    assert response.status_code == 422


def test_create_task_with_nonexistent_vehicle(client, monkeypatch):
    monkeypatch.setattr(
        maintenance_task_service,
        "verify_vehicle_exists",
        vehicle_not_found,
    )

    response = client.post(
        "/maintenance-tasks",
        json=task_payload(),
    )

    assert response.status_code == 422


def test_create_task_when_vehicles_service_is_unavailable(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        maintenance_task_service,
        "verify_vehicle_exists",
        vehicles_service_unavailable,
    )

    response = client.post(
        "/maintenance-tasks",
        json=task_payload(),
    )

    assert response.status_code == 503


def test_create_task_with_rule_for_same_vehicle(client):
    rule = create_rule(client)

    response = client.post(
        "/maintenance-tasks",
        json=task_payload(rule_id=rule["id"]),
    )

    assert response.status_code == 201
    assert response.json()["rule_id"] == rule["id"]


def test_create_task_with_nonexistent_rule(client):
    response = client.post(
        "/maintenance-tasks",
        json=task_payload(rule_id=999),
    )

    assert response.status_code == 422


def test_create_task_with_rule_belonging_to_another_vehicle(client):
    rule = create_rule(client, vehicle_id=2)

    response = client.post(
        "/maintenance-tasks",
        json=task_payload(vehicle_id=1, rule_id=rule["id"]),
    )

    assert response.status_code == 422


def test_list_maintenance_tasks(client):
    create_task(client)
    create_task(
        client,
        vehicle_id=2,
        name="Revisar neumáticos",
        due_date="2026-12-20",
    )

    response = client.get("/maintenance-tasks")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_tasks_by_vehicle(client):
    create_task(client)
    create_task(client, vehicle_id=2, name="Revisar neumáticos")

    response = client.get("/maintenance-tasks?vehicle_id=1")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["vehicle_id"] == 1


def test_list_tasks_by_status(client):
    task = create_task(client)

    response = client.patch(
        f"/maintenance-tasks/{task['id']}/complete",
        json={
            "completed_date": date.today().isoformat(),
            "completed_mileage": 50000,
        },
    )
    assert response.status_code == 200

    response = client.get("/maintenance-tasks?status=completed")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "completed"


def test_list_tasks_with_invalid_status(client):
    response = client.get("/maintenance-tasks?status=invalid")

    assert response.status_code == 422


def test_get_maintenance_task_by_id(client):
    created = create_task(client)

    response = client.get(f"/maintenance-tasks/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Revisar aceite"


def test_get_nonexistent_task(client):
    response = client.get("/maintenance-tasks/999")

    assert response.status_code == 404


def test_complete_maintenance_task(client):
    created = create_task(client)

    response = client.patch(
        f"/maintenance-tasks/{created['id']}/complete",
        json={
            "completed_date": "2026-10-22",
            "completed_mileage": 50000,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["completed_date"] == "2026-10-22"
    assert data["completed_mileage"] == 50000


def test_complete_task_without_mileage(client):
    created = create_task(client)

    response = client.patch(
        f"/maintenance-tasks/{created['id']}/complete",
        json={
            "completed_date": date.today().isoformat(),
            "completed_mileage": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["completed_mileage"] is None


def test_complete_already_completed_task_does_not_change_it(client):
    created = create_task(client)

    first = client.patch(
        f"/maintenance-tasks/{created['id']}/complete",
        json={
            "completed_date": "2026-10-20",
            "completed_mileage": 49000,
        },
    )
    assert first.status_code == 200

    second = client.patch(
        f"/maintenance-tasks/{created['id']}/complete",
        json={
            "completed_date": "2026-10-22",
            "completed_mileage": 50000,
        },
    )

    assert second.status_code == 200
    assert second.json()["completed_date"] == "2026-10-20"
    assert second.json()["completed_mileage"] == 49000


def test_complete_nonexistent_task(client):
    response = client.patch(
        "/maintenance-tasks/999/complete",
        json={
            "completed_date": date.today().isoformat(),
            "completed_mileage": 50000,
        },
    )

    assert response.status_code == 404


# Health checks

def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_live_endpoint(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "maintenance-planning-service",
    }


def test_health_ready_endpoint(client, monkeypatch):
    mock_connection = MagicMock()
    monkeypatch.setattr(
        main_module.engine,
        "connect",
        lambda: mock_connection,
    )

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "maintenance-planning-service",
        "database": "ok",
    }


def test_health_ready_when_database_is_unavailable(client, monkeypatch):
    def raise_database_error():
        raise SQLAlchemyError("Database unavailable")

    monkeypatch.setattr(
        main_module.engine,
        "connect",
        raise_database_error,
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "status": "error",
        "service": "maintenance-planning-service",
        "database": "unavailable",
    }
