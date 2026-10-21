from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.maintenance import Maintenance
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate


def create(db: Session, data: MaintenanceCreate) -> Maintenance:
    maintenance = Maintenance(**data.model_dump())
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    return maintenance


def get_all(db: Session) -> list[Maintenance]:
    statement = select(Maintenance).order_by(Maintenance.date.desc(), Maintenance.id.desc())
    return list(db.scalars(statement).all())


def get_by_id(db: Session, maintenance_id: int) -> Maintenance | None:
    return db.get(Maintenance, maintenance_id)


def get_by_vehicle(db: Session, vehicle_id: int) -> list[Maintenance]:
    statement = (
        select(Maintenance)
        .where(Maintenance.vehicle_id == vehicle_id)
        .order_by(Maintenance.date.desc(), Maintenance.id.desc())
    )
    return list(db.scalars(statement).all())


def update(
    db: Session,
    maintenance: Maintenance,
    data: MaintenanceUpdate,
) -> Maintenance:
    for field, value in data.model_dump().items():
        setattr(maintenance, field, value)

    db.commit()
    db.refresh(maintenance)
    return maintenance


def delete(db: Session, maintenance: Maintenance) -> None:
    db.delete(maintenance)
    db.commit()
