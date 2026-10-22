from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.clients.vehicles_client import (
    VehicleNotFoundError,
    VehicleServiceUnavailableError,
)
from app.db.session import get_db
from app.schemas.maintenance_task import (
    MaintenanceTaskComplete,
    MaintenanceTaskCreate,
    MaintenanceTaskResponse,
)
from app.services.maintenance_task_service import (
    MaintenanceRuleReferenceError,
    MaintenanceTaskNotFoundError,
    complete_task,
    create_task,
    get_task,
    list_tasks,
)

router = APIRouter(
    prefix="/maintenance-tasks",
    tags=["Maintenance Tasks"],
)


def handle_vehicle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, VehicleNotFoundError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El vehículo indicado no existe.",
        )

    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="No se ha podido verificar el vehículo.",
    )


@router.post(
    "",
    response_model=MaintenanceTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: MaintenanceTaskCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_task(db, data)
    except MaintenanceRuleReferenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="La regla indicada no existe o pertenece a otro vehículo.",
        ) from exc
    except (
        VehicleNotFoundError,
        VehicleServiceUnavailableError,
    ) as exc:
        raise handle_vehicle_error(exc) from exc


@router.get("", response_model=list[MaintenanceTaskResponse])
def list_all(
    vehicle_id: int | None = Query(default=None, gt=0),
    task_status: str | None = Query(
        default=None,
        alias="status",
        pattern="^(pending|upcoming|overdue|completed)$",
    ),
    db: Session = Depends(get_db),
):
    return list_tasks(db, vehicle_id, task_status)


@router.get("/{task_id}", response_model=MaintenanceTaskResponse)
def get_one(
    task_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_task(db, task_id)
    except MaintenanceTaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea de mantenimiento no encontrada.",
        )


@router.patch(
    "/{task_id}/complete",
    response_model=MaintenanceTaskResponse,
)
def mark_completed(
    task_id: int,
    data: MaintenanceTaskComplete,
    db: Session = Depends(get_db),
):
    try:
        return complete_task(
            db,
            task_id,
            data.completed_date,
            data.completed_mileage,
        )
    except MaintenanceTaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea de mantenimiento no encontrada.",
        )
