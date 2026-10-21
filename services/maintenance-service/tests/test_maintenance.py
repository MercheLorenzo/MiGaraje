from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base, get_db
from app.main import app


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


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db

    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)


def maintenance_payload(**overrides):
    payload = {
        "vehicle_id": 1,
        "maintenance_type": "oil_change",
        "date": date.today().isoformat(),
        "mileage": 45000,
        "description": "Cambio de aceite y filtro",
        "cost": "89.90",
        "products_used": "Aceite 5W-30 y filtro de aceite",
    }
    payload.update(overrides)
    return payload


def test_create_maintenance(client):
    response = client.post("/maintenances", json=maintenance_payload())

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["vehicle_id"] == 1
    assert data["maintenance_type"] == "oil_change"
    assert data["cost"] == "89.90"


def test_create_maintenance_without_products(client):
    payload = maintenance_payload(products_used=None)
    response = client.post("/maintenances", json=payload)

    assert response.status_code == 201
    assert response.json()["products_used"] is None


def test_create_maintenance_with_negative_mileage(client):
    response = client.post(
        "/maintenances",
        json=maintenance_payload(mileage=-1),
    )

    assert response.status_code == 422


def test_create_maintenance_with_negative_cost(client):
    response = client.post(
        "/maintenances",
        json=maintenance_payload(cost="-10.00"),
    )

    assert response.status_code == 422


def test_create_maintenance_with_invalid_vehicle_id(client):
    response = client.post(
        "/maintenances",
        json=maintenance_payload(vehicle_id=0),
    )

    assert response.status_code == 422


def test_list_maintenances(client):
    client.post("/maintenances", json=maintenance_payload())
    client.post(
        "/maintenances",
        json=maintenance_payload(
            vehicle_id=2,
            maintenance_type="repair",
            description="Cambio de batería",
            cost="120.00",
        ),
    )

    response = client.get("/maintenances")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_maintenance_by_id(client):
    created = client.post(
        "/maintenances",
        json=maintenance_payload(),
    ).json()

    response = client.get(f"/maintenances/{created['id']}")

    assert response.status_code == 200
    assert response.json()["description"] == "Cambio de aceite y filtro"


def test_get_nonexistent_maintenance(client):
    response = client.get("/maintenances/999")

    assert response.status_code == 404


def test_list_maintenances_by_vehicle(client):
    client.post(
        "/maintenances",
        json=maintenance_payload(vehicle_id=1),
    )
    client.post(
        "/maintenances",
        json=maintenance_payload(vehicle_id=2, description="Otra intervención"),
    )

    response = client.get("/maintenances/vehicle/1")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["vehicle_id"] == 1


def test_update_maintenance(client):
    created = client.post(
        "/maintenances",
        json=maintenance_payload(),
    ).json()

    updated_payload = maintenance_payload(
        description="Cambio de aceite completo",
        cost="99.50",
    )
    response = client.put(
        f"/maintenances/{created['id']}",
        json=updated_payload,
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Cambio de aceite completo"
    assert response.json()["cost"] == "99.50"


def test_update_nonexistent_maintenance(client):
    response = client.put(
        "/maintenances/999",
        json=maintenance_payload(),
    )

    assert response.status_code == 404


def test_delete_maintenance(client):
    created = client.post(
        "/maintenances",
        json=maintenance_payload(),
    ).json()

    response = client.delete(f"/maintenances/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/maintenances/{created['id']}").status_code == 404


def test_delete_nonexistent_maintenance(client):
    response = client.delete("/maintenances/999")

    assert response.status_code == 404


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
