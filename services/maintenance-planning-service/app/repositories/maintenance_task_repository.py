from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.maintenance_task import MaintenanceTask
from app.schemas.maintenance_task import MaintenanceTaskCreate


def create(db: Session, data: MaintenanceTaskCreate) -> MaintenanceTask:
    task = MaintenanceTask(
        **data.model_dump(),
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_all(
    db: Session,
    vehicle_id: int | None = None,
    status: str | None = None,
) -> list[MaintenanceTask]:
    statement = select(MaintenanceTask)

    if vehicle_id is not None:
        statement = statement.where(
            MaintenanceTask.vehicle_id == vehicle_id
        )

    if status is not None:
        statement = statement.where(
            MaintenanceTask.status == status
        )

    statement = statement.order_by(
        MaintenanceTask.due_date.asc(),
        MaintenanceTask.id.desc(),
    )
    return list(db.scalars(statement).all())


def get_by_id(db: Session, task_id: int) -> MaintenanceTask | None:
    return db.get(MaintenanceTask, task_id)


def save(db: Session, task: MaintenanceTask) -> MaintenanceTask:
    db.commit()
    db.refresh(task)
    return task
