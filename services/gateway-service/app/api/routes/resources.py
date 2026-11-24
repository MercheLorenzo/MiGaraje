"""Explicit, documented CRUD endpoints for the public Gateway.

Routes retain the same URLs and behavior the frontend already uses; the former
/{kind} catch-all prevented FastAPI from showing individual Swagger operations.
"""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.services_client import call
from app.db.session import get_db
from app.models.account import User, VehicleOwner
from app.schemas.api_models import (
    CompleteTaskIn, MaintenanceIn, MaintenanceOut, RuleIn, RuleOut,
    TaskIn, TaskOut, VehicleIn, VehicleOut,
)
from app.services.auth import current_user

router = APIRouter(prefix="/api")


def owned_ids(db: Session, user: User) -> list[int]:
    return list(db.scalars(select(VehicleOwner.vehicle_id).where(VehicleOwner.user_id == user.id)).all())


def assert_owned(db: Session, user: User, vehicle_id: int):
    if vehicle_id not in owned_ids(db, user):
        raise HTTPException(404, "Vehículo no encontrado en tu garaje")


KINDS = {
    "maintenances": ("maintenance", "/maintenances"),
    "rules": ("planning", "/maintenance-rules"),
    "tasks": ("planning", "/maintenance-tasks"),
}


def existing(kind: str, record_id: int, db: Session, user: User):
    service, path = KINDS[kind]
    result = call(service, "GET", f"{path}/{record_id}")
    assert_owned(db, user, result["vehicle_id"])
    return result


def list_owned(kind: str, vehicle_id: int | None, user: User, db: Session, status: str | None = None):
    ids = owned_ids(db, user)
    if vehicle_id is not None:
        assert_owned(db, user, vehicle_id)
        ids = [vehicle_id]
    service, path = KINDS[kind]
    result = call(service, "GET", path, params={"status": status} if status is not None else None)
    return [item for item in result if item["vehicle_id"] in ids]


def create_owned(kind: str, body: dict, user: User, db: Session):
    vid = body["vehicle_id"]
    assert_owned(db, user, vid)
    if kind == "tasks" and body.get("rule_id"):
        rule = existing("rules", body["rule_id"], db, user)
        if rule["vehicle_id"] != vid:
            raise HTTPException(422, "La regla no pertenece a ese vehículo")
    service, path = KINDS[kind]
    return call(service, "POST", path, data=body)


def update_owned(kind: str, record_id: int, body: dict, user: User, db: Session):
    old = existing(kind, record_id, db, user)
    if body["vehicle_id"] != old["vehicle_id"]:
        raise HTTPException(422, "No puedes cambiar el vehículo del registro")
    if kind == "tasks" and body.get("rule_id"):
        rule = existing("rules", body["rule_id"], db, user)
        if rule["vehicle_id"] != old["vehicle_id"]:
            raise HTTPException(422, "La regla no pertenece al vehículo")
    service, path = KINDS[kind]
    return call(service, "PUT", f"{path}/{record_id}", data=body)


def delete_owned(kind: str, record_id: int, user: User, db: Session):
    old = existing(kind, record_id, db, user)
    if kind == "rules":
        tasks = call("planning", "GET", "/maintenance-tasks", params={"vehicle_id": old["vehicle_id"]})
        for task in tasks:
            if task["rule_id"] == record_id:
                call("notifications", "DELETE", f"/notifications/{user.id}/task/{task['id']}")
                call("planning", "DELETE", f"/maintenance-tasks/{task['id']}")
    if kind == "tasks":
        call("notifications", "DELETE", f"/notifications/{user.id}/task/{record_id}")
    service, path = KINDS[kind]
    return call(service, "DELETE", f"{path}/{record_id}")


# -------------------- Vehículos --------------------
@router.get("/vehicles", tags=["Vehículos"], summary="Listar mis vehículos", response_model=list[VehicleOut])
def vehicles(user: User = Depends(current_user), db: Session = Depends(get_db)):
    ids = set(owned_ids(db, user))
    return [v for v in call("vehicles", "GET", "/vehicles") if v["id"] in ids]


@router.post("/vehicles", tags=["Vehículos"], summary="Crear vehículo", response_model=VehicleOut, status_code=201)
def create_vehicle(body: VehicleIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = call("vehicles", "POST", "/vehicles", data=body.model_dump(mode="json"))
    db.add(VehicleOwner(vehicle_id=result["id"], user_id=user.id))
    try:
        db.commit()
    except Exception:
        db.rollback()
        call("vehicles", "DELETE", f"/vehicles/{result['id']}")
        raise
    return result


@router.get("/vehicles/{vehicle_id}", tags=["Vehículos"], summary="Consultar vehículo", response_model=VehicleOut)
def vehicle(vehicle_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    assert_owned(db, user, vehicle_id)
    return call("vehicles", "GET", f"/vehicles/{vehicle_id}")


@router.put("/vehicles/{vehicle_id}", tags=["Vehículos"], summary="Actualizar vehículo", response_model=VehicleOut)
def update_vehicle(vehicle_id: int, body: VehicleIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    assert_owned(db, user, vehicle_id)
    return call("vehicles", "PUT", f"/vehicles/{vehicle_id}", data=body.model_dump(mode="json"))


@router.delete("/vehicles/{vehicle_id}", tags=["Vehículos"], summary="Eliminar vehículo y sus registros", status_code=204)
def remove_vehicle(vehicle_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    assert_owned(db, user, vehicle_id)
    # Eliminar avisos del usuario antes de retirar el vehículo y sus registros.
    call("notifications", "DELETE", f"/notifications/{user.id}/vehicle/{vehicle_id}")
    for task in call("planning", "GET", "/maintenance-tasks", params={"vehicle_id": vehicle_id}):
        call("planning", "DELETE", f"/maintenance-tasks/{task['id']}")
    for rule in call("planning", "GET", "/maintenance-rules", params={"vehicle_id": vehicle_id}):
        call("planning", "DELETE", f"/maintenance-rules/{rule['id']}")
    for maint in call("maintenance", "GET", f"/maintenances/vehicle/{vehicle_id}"):
        call("maintenance", "DELETE", f"/maintenances/{maint['id']}")
    call("vehicles", "DELETE", f"/vehicles/{vehicle_id}")
    db.delete(db.get(VehicleOwner, vehicle_id))
    db.commit()


# -------------------- Mantenimientos --------------------
@router.get("/maintenances", tags=["Mantenimientos"], summary="Listar mantenimientos", response_model=list[MaintenanceOut])
def list_maintenances(vehicle_id: int | None = Query(default=None, gt=0), user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list_owned("maintenances", vehicle_id, user, db)


@router.post("/maintenances", tags=["Mantenimientos"], summary="Registrar mantenimiento", status_code=201, response_model=MaintenanceOut)
def create_maintenance(body: MaintenanceIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return create_owned("maintenances", body.model_dump(mode="json"), user, db)


@router.get("/maintenances/{record_id}", tags=["Mantenimientos"], summary="Consultar mantenimiento", response_model=MaintenanceOut)
def get_maintenance(record_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return existing("maintenances", record_id, db, user)


@router.put("/maintenances/{record_id}", tags=["Mantenimientos"], summary="Actualizar mantenimiento", response_model=MaintenanceOut)
def update_maintenance(record_id: int, body: MaintenanceIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return update_owned("maintenances", record_id, body.model_dump(mode="json"), user, db)


@router.delete("/maintenances/{record_id}", tags=["Mantenimientos"], summary="Eliminar mantenimiento", status_code=204)
def delete_maintenance(record_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    delete_owned("maintenances", record_id, user, db)


# -------------------- Reglas de mantenimiento --------------------
@router.get("/rules", tags=["Reglas periódicas"], summary="Listar reglas de mantenimiento", response_model=list[RuleOut])
def list_rules(vehicle_id: int | None = Query(default=None, gt=0), user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list_owned("rules", vehicle_id, user, db)


@router.post("/rules", tags=["Reglas periódicas"], summary="Crear regla periódica", status_code=201, response_model=RuleOut)
def create_rule(body: RuleIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return create_owned("rules", body.model_dump(mode="json"), user, db)


@router.get("/rules/{record_id}", tags=["Reglas periódicas"], summary="Consultar regla", response_model=RuleOut)
def get_rule(record_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return existing("rules", record_id, db, user)


@router.put("/rules/{record_id}", tags=["Reglas periódicas"], summary="Actualizar regla", response_model=RuleOut)
def update_rule(record_id: int, body: RuleIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return update_owned("rules", record_id, body.model_dump(mode="json"), user, db)


@router.delete("/rules/{record_id}", tags=["Reglas periódicas"], summary="Eliminar regla y tareas vinculadas", status_code=204)
def delete_rule(record_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    delete_owned("rules", record_id, user, db)


@router.post("/rules/{rule_id}/generate", tags=["Reglas periódicas"], summary="Generar tarea desde una regla", status_code=201, response_model=TaskOut)
def generate_rule_task(rule_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    existing("rules", rule_id, db, user)
    return call("planning", "POST", f"/maintenance-rules/{rule_id}/generate")


# -------------------- Tareas --------------------
@router.get("/tasks", tags=["Tareas"], summary="Listar tareas", response_model=list[TaskOut])
def list_tasks(vehicle_id: int | None = Query(default=None, gt=0),
               status: Literal["pending", "upcoming", "overdue", "completed"] | None = Query(default=None),
               user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list_owned("tasks", vehicle_id, user, db, status=status)


@router.post("/tasks", tags=["Tareas"], summary="Crear tarea", status_code=201, response_model=TaskOut)
def create_task(body: TaskIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return create_owned("tasks", body.model_dump(mode="json"), user, db)


@router.get("/tasks/{record_id}", tags=["Tareas"], summary="Consultar tarea", response_model=TaskOut)
def get_task(record_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return existing("tasks", record_id, db, user)


@router.put("/tasks/{record_id}", tags=["Tareas"], summary="Actualizar tarea", response_model=TaskOut)
def update_task(record_id: int, body: TaskIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return update_owned("tasks", record_id, body.model_dump(mode="json"), user, db)


@router.delete("/tasks/{record_id}", tags=["Tareas"], summary="Eliminar tarea", status_code=204)
def delete_task(record_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    delete_owned("tasks", record_id, user, db)


@router.patch("/tasks/{task_id}/complete", tags=["Tareas"], summary="Marcar tarea como completada", response_model=TaskOut)
def complete(task_id: int, body: CompleteTaskIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    existing("tasks", task_id, db, user)
    return call("planning", "PATCH", f"/maintenance-tasks/{task_id}/complete", data=body.model_dump(mode="json"))
