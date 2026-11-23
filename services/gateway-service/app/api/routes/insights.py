"""Documented statistics and notifications on the authenticated public API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.routes.resources import assert_owned, owned_ids
from app.clients.services_client import call
from app.db.session import get_db
from app.models.account import User
from app.schemas.api_models import (
    CategoryOut, ComparisonOut, MailTestResult, MonthlyOut, NotificationOut,
    PreferencesIn, ScanResult, SummaryOut, VehicleStatsOut,
)
from app.services.auth import current_user

router = APIRouter(prefix="/api")


def report_data(report: str, year: int | None, vehicle_id: int | None, user: User, db: Session):
    ids = owned_ids(db, user)
    if vehicle_id is not None:
        assert_owned(db, user, vehicle_id)
        ids = [vehicle_id]
    return call("statistics", "GET", f"/statistics/{report}",
                params={"vehicle_ids": ",".join(map(str, ids)), "year": year})


@router.get("/statistics/summary", tags=["Estadísticas"], summary="Resumen de gastos", response_model=SummaryOut)
def summary(year: int | None = Query(default=None, ge=1900, le=2100),
            vehicle_id: int | None = Query(default=None, gt=0),
            user: User = Depends(current_user), db: Session = Depends(get_db)):
    return report_data("summary", year, vehicle_id, user, db)


@router.get("/statistics/monthly", tags=["Estadísticas"], summary="Gastos mensuales", response_model=list[MonthlyOut])
def monthly(year: int | None = Query(default=None, ge=1900, le=2100),
            vehicle_id: int | None = Query(default=None, gt=0),
            user: User = Depends(current_user), db: Session = Depends(get_db)):
    return report_data("monthly", year, vehicle_id, user, db)


@router.get("/statistics/categories", tags=["Estadísticas"], summary="Gastos por categoría", response_model=list[CategoryOut])
def categories(year: int | None = Query(default=None, ge=1900, le=2100),
               vehicle_id: int | None = Query(default=None, gt=0),
               user: User = Depends(current_user), db: Session = Depends(get_db)):
    return report_data("categories", year, vehicle_id, user, db)


@router.get("/statistics/comparison", tags=["Estadísticas"], summary="Comparación entre vehículos", response_model=list[ComparisonOut])
def comparison(year: int | None = Query(default=None, ge=1900, le=2100),
               vehicle_id: int | None = Query(default=None, gt=0),
               user: User = Depends(current_user), db: Session = Depends(get_db)):
    return report_data("comparison", year, vehicle_id, user, db)


@router.get("/statistics/vehicles/{vehicle_id}", tags=["Estadísticas"], summary="Estadísticas de un vehículo", response_model=VehicleStatsOut)
def stats_vehicle(vehicle_id: int, year: int | None = Query(default=None, ge=1900, le=2100),
                  user: User = Depends(current_user), db: Session = Depends(get_db)):
    assert_owned(db, user, vehicle_id)
    return call("statistics", "GET", f"/statistics/vehicles/{vehicle_id}", params={"year": year})


@router.get("/notifications", tags=["Notificaciones"], summary="Listar mis avisos", response_model=list[NotificationOut])
def notifications(user: User = Depends(current_user)):
    return call("notifications", "GET", f"/notifications/{user.id}")


@router.post("/notifications/scan", tags=["Notificaciones"], summary="Buscar vencimientos y generar avisos", response_model=ScanResult)
def scan(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return call("notifications", "POST", f"/notifications/{user.id}/scan",
                data={"vehicle_ids": owned_ids(db, user), "email": user.email})


@router.get("/notifications/preferences", tags=["Notificaciones"], summary="Consultar preferencias de avisos", response_model=PreferencesIn)
def get_prefs(user: User = Depends(current_user)):
    return call("notifications", "GET", f"/notifications/{user.id}/preferences")


@router.put("/notifications/preferences", tags=["Notificaciones"], summary="Actualizar preferencias de avisos", response_model=PreferencesIn)
def set_prefs(body: PreferencesIn, user: User = Depends(current_user)):
    return call("notifications", "PUT", f"/notifications/{user.id}/preferences", data=body.model_dump(mode="json"))


@router.patch("/notifications/{notification_id}/read", tags=["Notificaciones"], summary="Marcar aviso como leído", response_model=NotificationOut)
def mark_read(notification_id: int, user: User = Depends(current_user)):
    return call("notifications", "PATCH", f"/notifications/{user.id}/{notification_id}/read")


@router.post("/notifications/test", tags=["Notificaciones"], summary="Probar envío de correo SMTP", response_model=MailTestResult)
def test_mail(user: User = Depends(current_user)):
    return call("notifications", "POST", f"/notifications/{user.id}/test", data={"email": user.email})
