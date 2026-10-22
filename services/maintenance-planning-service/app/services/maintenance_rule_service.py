from sqlalchemy.orm import Session

from app.clients.vehicles_client import verify_vehicle_exists
from app.models.maintenance_rule import MaintenanceRule
from app.repositories import maintenance_rule_repository as repository
from app.schemas.maintenance_rule import (
    MaintenanceRuleCreate,
    MaintenanceRuleUpdate,
)


class MaintenanceRuleNotFoundError(Exception):
    pass


def create_rule(db: Session, data: MaintenanceRuleCreate) -> MaintenanceRule:
    verify_vehicle_exists(data.vehicle_id)
    return repository.create(db, data)


def list_rules(
    db: Session,
    vehicle_id: int | None = None,
) -> list[MaintenanceRule]:
    return repository.get_all(db, vehicle_id)


def get_rule(db: Session, rule_id: int) -> MaintenanceRule:
    rule = repository.get_by_id(db, rule_id)

    if rule is None:
        raise MaintenanceRuleNotFoundError

    return rule


def update_rule(
    db: Session,
    rule_id: int,
    data: MaintenanceRuleUpdate,
) -> MaintenanceRule:
    get_rule(db, rule_id)
    verify_vehicle_exists(data.vehicle_id)

    rule = repository.get_by_id(db, rule_id)
    return repository.update(db, rule, data)


def delete_rule(db: Session, rule_id: int) -> None:
    rule = get_rule(db, rule_id)
    repository.delete(db, rule)
