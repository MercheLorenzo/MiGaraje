import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import app


# Base de datos SQLite independiente, mantenida en memoria.
TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
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
    # Crea un esquema limpio para cada prueba.
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    app.dependency_overrides[get_db] = override_get_db

    # No usamos el context manager para evitar ejecutar el
    # lifespan de la aplicación, que crea tablas en la BD normal.
    #with TestClient(app) as test_client:
        #yield test_client
    
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


def vehicle_payload(**overrides):
    data = {
        "brand": "Toyota",
        "model": "Corolla",
        "year": 2022,
        "license_plate": "1234ABC",
        "current_mileage": 45000,
    }
    data.update(overrides)
    return data


def test_create_vehicle(client):
    response = client.post("/vehicles", json=vehicle_payload())

    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["brand"] == "Toyota"
    assert data["model"] == "Corolla"
    assert data["license_plate"] == "1234ABC"


def test_create_vehicle_without_license_plate(client):
    payload = vehicle_payload(license_plate=None)

    response = client.post("/vehicles", json=payload)

    assert response.status_code == 201
    assert response.json()["license_plate"] is None


def test_create_vehicle_with_invalid_year(client):
    payload = vehicle_payload(year=1800)

    response = client.post("/vehicles", json=payload)

    assert response.status_code == 422


def test_create_vehicle_with_negative_mileage(client):
    payload = vehicle_payload(current_mileage=-10)

    response = client.post("/vehicles", json=payload)

    assert response.status_code == 422


def test_list_vehicles(client):
    client.post("/vehicles", json=vehicle_payload())
    client.post(
        "/vehicles",
        json=vehicle_payload(
            brand="Seat",
            model="Ibiza",
            license_plate="5678BCD",
        ),
    )

    response = client.get("/vehicles")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_vehicle_by_id(client):
    created = client.post(
        "/vehicles",
        json=vehicle_payload(),
    ).json()

    response = client.get(f"/vehicles/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_nonexistent_vehicle(client):
    response = client.get("/vehicles/9999")

    assert response.status_code == 404


def test_update_vehicle(client):
    created = client.post(
        "/vehicles",
        json=vehicle_payload(),
    ).json()

    updated_payload = vehicle_payload(
        brand="Toyota",
        model="Yaris",
        year=2024,
        current_mileage=12000,
    )

    response = client.put(
        f"/vehicles/{created['id']}",
        json=updated_payload,
    )

    assert response.status_code == 200
    assert response.json()["model"] == "Yaris"
    assert response.json()["year"] == 2024
    assert response.json()["current_mileage"] == 12000


def test_update_nonexistent_vehicle(client):
    response = client.put(
        "/vehicles/9999",
        json=vehicle_payload(),
    )

    assert response.status_code == 404


def test_delete_vehicle(client):
    created = client.post(
        "/vehicles",
        json=vehicle_payload(),
    ).json()

    response = client.delete(f"/vehicles/{created['id']}")

    assert response.status_code == 204

    get_response = client.get(f"/vehicles/{created['id']}")
    assert get_response.status_code == 404


def test_delete_nonexistent_vehicle(client):
    response = client.delete("/vehicles/9999")

    assert response.status_code == 404


def test_duplicate_license_plate(client):
    client.post("/vehicles", json=vehicle_payload())

    duplicate = vehicle_payload(
        brand="Seat",
        model="Ibiza",
    )

    response = client.post("/vehicles", json=duplicate)

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "La matrícula ya está registrada."
    )


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
