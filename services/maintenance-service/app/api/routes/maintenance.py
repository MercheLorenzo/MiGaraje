from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.maintenance import (
    MaintenanceCreate,
    MaintenanceResponse,
    MaintenanceUpdate,
)
from app.services.maintenance_service import (
    MaintenanceNotFoundError,
    create_maintenance,
    delete_maintenance,
    get_maintenance,
    list_maintenances,
    list_vehicle_maintenances,
    update_maintenance,
)
from app.clients.vehicles_client import (
    VehicleNotFoundError,
    VehicleServiceUnavailableError,
)


router = APIRouter(prefix="/maintenances", tags=["Maintenance"])

def handle_vehicle_error(exc: Exception) -> HTTPException:
    if isinstance(exc, VehicleNotFoundError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El vehículo indicado no existe.",
        )

    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="No se ha podido verificar el vehículo.",
    )

@router.post(
    "",
    response_model=MaintenanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: MaintenanceCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_maintenance(db, data)
    except (
        VehicleNotFoundError,
        VehicleServiceUnavailableError,
    ) as exc:
        raise handle_vehicle_error(exc) from exc

@router.get("", response_model=list[MaintenanceResponse])
def list_all(db: Session = Depends(get_db)):
    return list_maintenances(db)


@router.get("/vehicle/{vehicle_id}", response_model=list[MaintenanceResponse])
def list_by_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
):
    if vehicle_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El identificador del vehículo debe ser positivo.",
        )

    return list_vehicle_maintenances(db, vehicle_id)


@router.get("/{maintenance_id}", response_model=MaintenanceResponse)
def get_one(
    maintenance_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_maintenance(db, maintenance_id)
    except MaintenanceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mantenimiento no encontrado.",
        )


@router.put("/{maintenance_id}", response_model=MaintenanceResponse)
def update(
    maintenance_id: int,
    data: MaintenanceUpdate,
    db: Session = Depends(get_db),
):
    try:
        return update_maintenance(db, maintenance_id, data)
    except MaintenanceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mantenimiento no encontrado.",
        )
    except (
        VehicleNotFoundError,
        VehicleServiceUnavailableError,
    ) as exc:
        raise handle_vehicle_error(exc) from exc


@router.delete(
    "/{maintenance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    maintenance_id: int,
    db: Session = Depends(get_db),
):
    try:
        delete_maintenance(db, maintenance_id)
    except MaintenanceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mantenimiento no encontrado.",
        )
