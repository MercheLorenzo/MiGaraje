from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.repositories import vehicle_repository as repository
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


class VehicleNotFoundError(Exception):
    pass


class DuplicateLicensePlateError(Exception):
    pass


def create_vehicle(db: Session, data: VehicleCreate):
    try:
        return repository.create(db, data)
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateLicensePlateError from exc


def list_vehicles(db: Session):
    return repository.get_all(db)


def get_vehicle(db: Session, vehicle_id: int):
    vehicle = repository.get_by_id(db, vehicle_id)

    if vehicle is None:
        raise VehicleNotFoundError

    return vehicle


def update_vehicle(
    db: Session,
    vehicle_id: int,
    data: VehicleUpdate,
):
    vehicle = get_vehicle(db, vehicle_id)

    try:
        return repository.update(db, vehicle, data)
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateLicensePlateError from exc


def delete_vehicle(db: Session, vehicle_id: int):
    vehicle = get_vehicle(db, vehicle_id)
    repository.delete(db, vehicle)