from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)
from app.services.vehicle_service import (
    DuplicateLicensePlateError,
    VehicleNotFoundError,
    create_vehicle,
    delete_vehicle,
    get_vehicle,
    list_vehicles,
    update_vehicle,
)

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


def handle_integrity_error():
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="La matrícula ya está registrada.",
    )


@router.post(
    "",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: VehicleCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_vehicle(db, data)
    except DuplicateLicensePlateError:
        handle_integrity_error()


@router.get("", response_model=list[VehicleResponse])
def list_all(db: Session = Depends(get_db)):
    return list_vehicles(db)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_one(
    vehicle_id: int,
    db: Session = Depends(get_db),
):
    try:
        return get_vehicle(db, vehicle_id)
    except VehicleNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Vehículo no encontrado.",
        )


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update(
    vehicle_id: int,
    data: VehicleUpdate,
    db: Session = Depends(get_db),
):
    try:
        return update_vehicle(db, vehicle_id, data)
    except VehicleNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Vehículo no encontrado.",
        )
    except DuplicateLicensePlateError:
        handle_integrity_error()


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    vehicle_id: int,
    db: Session = Depends(get_db),
):
    try:
        delete_vehicle(db, vehicle_id)
    except VehicleNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Vehículo no encontrado.",
        )