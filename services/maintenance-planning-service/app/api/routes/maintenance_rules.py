from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.clients.vehicles_client import (
    VehicleNotFoundError,
    VehicleServiceUnavailableError,
)
from app.db.session import get_db
from app.schemas.maintenance_rule import (
    MaintenanceRuleCreate,
    MaintenanceRuleResponse,
    MaintenanceRuleUpdate,
)
from app.services.maintenance_rule_service import (
    MaintenanceRuleNotFoundError,
    create_rule,
    delete_rule,
    get_rule,
    list_rules,
    update_rule,
)

router = APIRouter(
    prefix="/maintenance-rules",
    tags=["Maintenance Rules"],
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
    response_model=MaintenanceRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: MaintenanceRuleCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_rule(db, data)
    except (
        VehicleNotFoundError,
        VehicleServiceUnavailableError,
    ) as exc:
        raise handle_vehicle_error(exc) from exc


@router.get("", response_model=list[MaintenanceRuleResponse])
def list_all(
    vehicle_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    return list_rules(db, vehicle_id)


@router.get("/{rule_id}", response_model=MaintenanceRuleResponse)
def get_one(
    rule_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_rule(db, rule_id)
    except MaintenanceRuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regla de mantenimiento no encontrada.",
        )


@router.put("/{rule_id}", response_model=MaintenanceRuleResponse)
def update(
    rule_id: int,
    data: MaintenanceRuleUpdate,
    db: Session = Depends(get_db),
):
    try:
        return update_rule(db, rule_id, data)
    except MaintenanceRuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regla de mantenimiento no encontrada.",
        )
    except (
        VehicleNotFoundError,
        VehicleServiceUnavailableError,
    ) as exc:
        raise handle_vehicle_error(exc) from exc


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    rule_id: int,
    db: Session = Depends(get_db),
):
    try:
        delete_rule(db, rule_id)
    except MaintenanceRuleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regla de mantenimiento no encontrada.",
        )
