"""Regresiones: una tarea vencida por km debe filtrar igual en API y web."""
from datetime import date, timedelta
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.clients.vehicles_client import VehicleServiceUnavailableError
from app.db.session import Base, get_db
from app.main import app
from app.services import maintenance_task_service

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
LocalSession = sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def client(monkeypatch):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override():
        with LocalSession() as db:
            yield db

    mileage = {1: 9000, 2: 30000}
    fetch = Mock(side_effect=lambda: dict(mileage))
    app.dependency_overrides[get_db] = override
    monkeypatch.setattr(maintenance_task_service, "verify_vehicle_exists", lambda _: None)
    monkeypatch.setattr(maintenance_task_service, "get_vehicle_mileages", fetch)
    try:
        with TestClient(app) as http:
            yield http, mileage, fetch
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)


def task_payload(**fields):
    data = {"vehicle_id": 1, "name": "Revisión por kilómetros", "due_mileage": 10000}
    data.update(fields)
    return data


def test_mileage_threshold_and_persisted_filters(client):
    http, mileage, fetch = client
    created = http.post("/maintenance-tasks", json=task_payload())
    assert created.status_code == 201, created.text
    task_id = created.json()["id"]

    # En el límite de 1000 km es próxima, pero NO vencida.
    assert [t["id"] for t in http.get("/maintenance-tasks?status=upcoming").json()] == [task_id]
    assert http.get("/maintenance-tasks?status=overdue").json() == []

    # En el km exacto sigue siendo próxima, tal como lo interpreta la web.
    mileage[1] = 10000
    assert http.get(f"/maintenance-tasks/{task_id}").json()["status"] == "upcoming"

    # Al SOBREPASAR los 10.000 km, el filtro overdue ya lo devuelve.
    mileage[1] = 10001
    result = http.get("/maintenance-tasks?status=overdue")
    assert result.status_code == 200, result.text
    assert [t["id"] for t in result.json()] == [task_id]
    assert http.get(f"/maintenance-tasks/{task_id}").json()["status"] == "overdue"

    # Si se corrige el kilometraje registrado, se recalcula desde el origen.
    mileage[1] = 100
    assert http.get("/maintenance-tasks?status=pending").json()[0]["id"] == task_id
    assert fetch.call_count >= 4


def test_date_or_mileage_with_overdue_precedence(client):
    http, mileage, _ = client
    future = date.today() + timedelta(days=60)
    yesterday = date.today() - timedelta(days=1)
    today = date.today()

    km_due = http.post("/maintenance-tasks", json=task_payload(due_date=future.isoformat()))
    assert km_due.status_code == 201, km_due.text
    date_due = http.post("/maintenance-tasks", json=task_payload(
        vehicle_id=2, due_mileage=50000, due_date=yesterday.isoformat()
    ))
    assert date_due.status_code == 201, date_due.text
    mileage[1] = 10001
    overdue_ids = {t["id"] for t in http.get("/maintenance-tasks?status=overdue").json()}
    assert overdue_ids == {km_due.json()["id"], date_due.json()["id"]}

    # Una tarea por fecha HOY es próxima, no vencida.
    due_today = http.post("/maintenance-tasks", json=task_payload(
        vehicle_id=2, due_mileage=None, due_date=today.isoformat()
    ))
    assert due_today.status_code == 201, due_today.text
    upcoming_ids = {t["id"] for t in http.get("/maintenance-tasks?status=upcoming").json()}
    assert due_today.json()["id"] in upcoming_ids


def test_completed_tasks_keep_their_status(client):
    http, mileage, _ = client
    created = http.post("/maintenance-tasks", json=task_payload()).json()
    response = http.patch(f"/maintenance-tasks/{created['id']}/complete", json={
        "completed_date": date.today().isoformat(), "completed_mileage": 10000
    })
    assert response.status_code == 200, response.text
    mileage[1] = 20000
    assert http.get("/maintenance-tasks?status=overdue").json() == []
    assert [t["id"] for t in http.get("/maintenance-tasks?status=completed").json()] == [created["id"]]


def test_vehicle_mileage_api_fails_cleanly(client):
    http, _, fetch = client
    created = http.post("/maintenance-tasks", json=task_payload())
    assert created.status_code == 201
    fetch.side_effect = VehicleServiceUnavailableError("servicio desconectado")
    assert http.get("/maintenance-tasks").status_code == 503
    assert http.get(f"/maintenance-tasks/{created.json()['id']}").status_code == 503


def test_completed_or_date_only_tasks_do_not_fetch_mileage(client):
    http, _, fetch = client
    created = http.post("/maintenance-tasks", json={
        "vehicle_id": 1, "name": "Solo fecha", "due_date": (date.today() + timedelta(days=90)).isoformat()
    })
    assert created.status_code == 201
    assert http.get("/maintenance-tasks").status_code == 200
    fetch.assert_not_called()
