from datetime import date

from sqlalchemy.orm import Session

from app.clients.vehicles_client import get_vehicle_mileages, verify_vehicle_exists
from app.models.maintenance_task import MaintenanceTask
from app.models.maintenance_rule import MaintenanceRule
from app.services.scheduling_service import generate_task
from app.services.task_status import calculate_task_status
from app.repositories import maintenance_rule_repository
from app.repositories import maintenance_task_repository as repository
from app.schemas.maintenance_task import MaintenanceTaskCreate


class MaintenanceTaskNotFoundError(Exception):
    pass


class MaintenanceRuleReferenceError(Exception):
    pass


def create_task(
    db: Session,
    data: MaintenanceTaskCreate,
) -> MaintenanceTask:
    verify_vehicle_exists(data.vehicle_id)

    if data.rule_id is not None:
        rule = maintenance_rule_repository.get_by_id(db, data.rule_id)

        if rule is None or rule.vehicle_id != data.vehicle_id:
            raise MaintenanceRuleReferenceError

    return repository.create(db, data)


def refresh_task_statuses(db: Session, tasks: list[MaintenanceTask]) -> None:
    """Sincroniza el estado almacenado con fecha y kilometraje actuales.

    La consulta HTTP se hace una sola vez y solamente si hay tareas abiertas
    con vencimiento por km. Si el servicio de vehículos falla, no persistimos
    estados posiblemente incorrectos: la API devuelve 503.
    """
    open_tasks = [task for task in tasks if task.status != "completed"]
    if not open_tasks:
        return

    mileages = (
        get_vehicle_mileages()
        if any(task.due_mileage is not None for task in open_tasks)
        else {}
    )
    today = date.today()
    changed = False
    for task in open_tasks:
        new_status = calculate_task_status(
            task,
            today=today,
            current_mileage=mileages.get(task.vehicle_id),
        )
        if task.status != new_status:
            task.status = new_status
            db.add(task)
            changed = True
    if changed:
        db.commit()


def list_tasks(
    db: Session,
    vehicle_id: int | None = None,
    status: str | None = None,
) -> list[MaintenanceTask]:
    tasks = repository.get_all(db, vehicle_id, None)
    refresh_task_statuses(db, tasks)
    if status:
        tasks = [task for task in tasks if task.status == status]
    return tasks


def get_task(db: Session, task_id: int) -> MaintenanceTask:
    task = repository.get_by_id(db, task_id)

    if task is None:
        raise MaintenanceTaskNotFoundError

    return task


def complete_task(
    db: Session,
    task_id: int,
    completed_date: date,
    completed_mileage: int | None,
) -> MaintenanceTask:
    task = get_task(db, task_id)

    if task.status == "completed":
        return task

    task.status = "completed"
    task.completed_date = completed_date
    task.completed_mileage = completed_mileage

    result = repository.save(db, task)
    if task.rule_id:
        rule = db.get(MaintenanceRule, task.rule_id)
        if rule and rule.is_active:
            rule.last_performed_date = completed_date
            if completed_mileage is not None:
                rule.last_performed_mileage = completed_mileage
            db.commit()
            generate_task(db, rule)
    return result


def delete_task(db: Session, task_id: int) -> None:
    repository.delete(db, get_task(db, task_id))


def update_task(db:Session,task_id:int,data:MaintenanceTaskCreate)->MaintenanceTask:
    task=get_task(db,task_id)
    if task.status=="completed":raise ValueError("No se puede editar una tarea completada")
    verify_vehicle_exists(data.vehicle_id)
    if data.rule_id is not None:
        rule=maintenance_rule_repository.get_by_id(db,data.rule_id)
        if not rule or rule.vehicle_id!=data.vehicle_id:raise MaintenanceRuleReferenceError
    for field,value in data.model_dump().items():setattr(task,field,value)
    task.status="pending"
    return repository.save(db,task)
