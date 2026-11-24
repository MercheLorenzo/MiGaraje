"""Informes de administración: solo GET, rol comprobado en servidor y documentado."""
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.account import User
from app.services.auth import current_user
from app.services import admin_reports

router = APIRouter(prefix="/api/admin", tags=["Administración"])


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Acceso exclusivo para administradores")
    return user


class AdminUserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: Literal["user", "admin"]
    created_at: datetime
    vehicle_count: int
    maintenance_count: int
    total_cost: float


class AdminVehicleOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    brand: str
    model: str
    year: int
    current_mileage: int
    owner_id: int | None
    owner_name: str | None
    owner_email: str | None
    maintenance_count: int
    total_cost: float


class AdminMaintenanceOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    vehicle_id: int
    date: str
    maintenance_type: str
    description: str
    cost: float
    owner_id: int | None
    owner_name: str | None
    owner_email: str | None
    vehicle_label: str


class GroupOut(BaseModel):
    category: str
    count: int
    total: float


class MonthOut(BaseModel):
    month: str
    count: int
    total: float


class OverviewOut(BaseModel):
    year: int | None
    user_count: int
    vehicle_count: int
    unassigned_vehicle_count: int
    maintenance_count: int
    total_cost: float
    average_cost: float
    categories: list[GroupOut]
    monthly: list[MonthOut]


@router.get("/overview", response_model=OverviewOut, summary="Estadísticas globales (solo administrador)")
def overview(year: int | None = Query(default=None, ge=1900, le=2100),
             _admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return admin_reports.report_overview(db, year=year)


@router.get("/users", response_model=list[AdminUserOut], summary="Consultar todos los usuarios y sus totales")
def users(_admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return admin_reports.report_users(db)


@router.get("/vehicles", response_model=list[AdminVehicleOut], summary="Consultar todos los vehículos y sus propietarios")
def vehicles(user_id: int | None = Query(default=None, gt=0),
             _admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return admin_reports.report_vehicles(db, user_id=user_id)


@router.get("/maintenances", response_model=list[AdminMaintenanceOut], summary="Consultar todos los mantenimientos")
def maintenances(user_id: int | None = Query(default=None, gt=0),
                 vehicle_id: int | None = Query(default=None, gt=0),
                 year: int | None = Query(default=None, ge=1900, le=2100),
                 _admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return admin_reports.report_maintenances(db, user_id=user_id, vehicle_id=vehicle_id, year=year)
