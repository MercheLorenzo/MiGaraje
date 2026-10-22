from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.maintenance_rule import MaintenanceRule
from app.schemas.maintenance_rule import (
    MaintenanceRuleCreate,
    MaintenanceRuleUpdate,
)


def create(db: Session, data: MaintenanceRuleCreate) -> MaintenanceRule:
    rule = MaintenanceRule(**data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def get_all(
    db: Session,
    vehicle_id: int | None = None,
) -> list[MaintenanceRule]:
    statement = select(MaintenanceRule)

    if vehicle_id is not None:
        statement = statement.where(
            MaintenanceRule.vehicle_id == vehicle_id
        )

    statement = statement.order_by(MaintenanceRule.id.desc())
    return list(db.scalars(statement).all())


def get_by_id(db: Session, rule_id: int) -> MaintenanceRule | None:
    return db.get(MaintenanceRule, rule_id)


def update(
    db: Session,
    rule: MaintenanceRule,
    data: MaintenanceRuleUpdate,
) -> MaintenanceRule:
    for field, value in data.model_dump().items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)
    return rule


def delete(db: Session, rule: MaintenanceRule) -> None:
    db.delete(rule)
    db.commit()
