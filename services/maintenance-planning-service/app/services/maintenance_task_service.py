from datetime import date

from sqlalchemy.orm import Session

from app.clients.vehicles_client import verify_vehicle_exists
from app.models.maintenance_task import MaintenanceTask
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


def list_tasks(
    db: Session,
    vehicle_id: int | None = None,
    status: str | None = None,
) -> list[MaintenanceTask]:
    return repository.get_all(db, vehicle_id, status)


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

    return repository.save(db, task)
