from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vehicle import Vehicle
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


def create(db: Session, data: VehicleCreate) -> Vehicle:
    vehicle = Vehicle(**data.model_dump())

    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    return vehicle


def get_all(db: Session) -> list[Vehicle]:
    statement = select(Vehicle).order_by(Vehicle.id)
    return list(db.scalars(statement).all())


def get_by_id(db: Session, vehicle_id: int) -> Vehicle | None:
    return db.get(Vehicle, vehicle_id)


def update(
    db: Session,
    vehicle: Vehicle,
    data: VehicleUpdate,
) -> Vehicle:
    for field, value in data.model_dump().items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)

    return vehicle


def delete(db: Session, vehicle: Vehicle) -> None:
    db.delete(vehicle)
    db.commit()