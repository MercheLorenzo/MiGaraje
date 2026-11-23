from datetime import datetime,timedelta,timezone
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.notification import Notification
from app.schemas.notification import PreferencesBody,ScanBody
from app.services.notification_service import get_preferences,preference_response,serialize,scan,deliver_email
from app.core.config import settings
router=APIRouter(prefix="/notifications",tags=["Notificaciones"])

@router.get("/{user_id}")
def list_all(user_id:int,db:Session=Depends(get_db)):
    return [serialize(n) for n in db.scalars(select(Notification).where(Notification.user_id==user_id).order_by(Notification.created_at.desc()).limit(200)).all()]

@router.get("/{user_id}/preferences")
def preferences(user_id:int,db:Session=Depends(get_db)):
    return preference_response(get_preferences(db,user_id))

@router.put("/{user_id}/preferences")
def update_preferences(user_id:int,body:PreferencesBody,db:Session=Depends(get_db)):
    if any(d not in (1,7,30,90) for d in body.reminder_offsets_days) or len(set(body.reminder_offsets_days))!=len(body.reminder_offsets_days):
        raise HTTPException(422,"Selecciona recordatorios distintos entre 90, 30, 7 y 1 día")
    p=get_preferences(db,user_id);p.email_enabled=body.email_enabled;p.reminder_offsets=",".join(map(str,sorted(body.reminder_offsets_days,reverse=True)));db.commit()
    return preference_response(p)

@router.post("/{user_id}/scan")
def scan_notifications(user_id:int,body:ScanBody,db:Session=Depends(get_db)):
    try:return scan(db,user_id,body.vehicle_ids,body.email)
    except Exception as exc:raise HTTPException(503,"No se pueden consultar las tareas pendientes") from exc

@router.patch("/{user_id}/{notification_id}/read")
def read(user_id:int,notification_id:int,db:Session=Depends(get_db)):
    n=db.get(Notification,notification_id)
    if not n or n.user_id!=user_id:raise HTTPException(404,"Notificación no encontrada")
    n.is_read=True;db.commit();return serialize(n)

@router.post("/{user_id}/test")
def send_test(user_id:int,body:ScanBody,db:Session=Depends(get_db)):
    pref=get_preferences(db,user_id)
    now=datetime.now(timezone.utc)
    last=pref.test_sent_at
    if last and (now-last.replace(tzinfo=last.tzinfo or timezone.utc))<timedelta(minutes=10):
        raise HTTPException(429,"Puedes repetir la prueba cada 10 minutos")
    if not settings.smtp_host or not settings.smtp_from:raise HTTPException(503,"Configura SMTP antes de probar el correo")
    try:deliver_email(body.email,"MiGaraje · correo de prueba","Las notificaciones por correo de MiGaraje funcionan.")
    except Exception as exc:raise HTTPException(503,"No se ha podido enviar el correo de prueba") from exc
    pref.test_sent_at=now;db.commit()
    return {"message":"Correo de prueba enviado"}
