from sqlalchemy.orm import Session

from app.clients.vehicles_client import (
    VehicleNotFoundError,
    VehicleServiceUnavailableError,
    verify_vehicle_exists,
)
from app.repositories import maintenance_repository as repository
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate


class MaintenanceNotFoundError(Exception):
    pass


def create_maintenance(db: Session, data: MaintenanceCreate):
    verify_vehicle_exists(data.vehicle_id)
    return repository.create(db, data)


def list_maintenances(db: Session):
    return repository.get_all(db)


def get_maintenance(db: Session, maintenance_id: int):
    maintenance = repository.get_by_id(db, maintenance_id)

    if maintenance is None:
        raise MaintenanceNotFoundError

    return maintenance


def list_vehicle_maintenances(db: Session, vehicle_id: int):
    return repository.get_by_vehicle(db, vehicle_id)


def update_maintenance(
    db: Session,
    maintenance_id: int,
    data: MaintenanceUpdate,
):
    maintenance = get_maintenance(db, maintenance_id)
    verify_vehicle_exists(data.vehicle_id)
    return repository.update(db, maintenance, data)


def delete_maintenance(db: Session, maintenance_id: int):
    maintenance = get_maintenance(db, maintenance_id)
    repository.delete(db, maintenance)
