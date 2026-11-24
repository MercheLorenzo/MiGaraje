import json
import smtplib
import ssl
from datetime import date,datetime,timedelta,timezone
from email.message import EmailMessage
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.notification import Notification,Preference
from app.clients.planning_client import tasks as fetch_tasks,vehicles as fetch_vehicles

OFFSETS=[90,30,7,1]

def get_preferences(db:Session,user_id:int)->Preference:
    prefs=db.get(Preference,user_id)
    if prefs is None:
        prefs=Preference(user_id=user_id,email_enabled=False,reminder_offsets="90,30,7,1")
        db.add(prefs);db.commit();db.refresh(prefs)
    return prefs

def preference_response(p):
    return {"email_enabled":p.email_enabled,"reminder_offsets_days":[int(n) for n in p.reminder_offsets.split(",") if n]}

def serialize(n:Notification):
    return {"id":n.id,"task_id":n.task_id,"vehicle_id":n.vehicle_id,"title":n.title,"body":n.body,"level":n.level,"is_read":n.is_read,"email_status":n.email_status,"created_at":n.created_at.isoformat()}

def deliver_email(to_address:str,subject:str,body:str):
    if not (settings.smtp_host and settings.smtp_from):raise RuntimeError("SMTP no configurado")
    msg=EmailMessage();msg["Subject"]=subject;msg["From"]=settings.smtp_from;msg["To"]=to_address;msg.set_content(body)
    with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=10) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        if settings.smtp_user:smtp.login(settings.smtp_user,settings.smtp_password)
        smtp.send_message(msg)

def scan(db:Session,user_id:int,vehicle_ids:list[int],email:str, *, all_tasks=None,all_vehicles=None):
    prefs=get_preferences(db,user_id)
    allowed=set(vehicle_ids)
    if not allowed:return {"created":0,"scanned":0}
    items=all_tasks if all_tasks is not None else fetch_tasks()
    cars=all_vehicles if all_vehicles is not None else fetch_vehicles()
    mileages={v["id"]:v["current_mileage"] for v in cars if v["id"] in allowed}
    today=date.today();created=0;scanned=0
    offsets=sorted([int(n) for n in prefs.reminder_offsets.split(",")],reverse=True)
    for task in items:
        if task["vehicle_id"] not in allowed or task["status"]=="completed":continue
        scanned+=1
        due=task.get("due_date")
        days=(date.fromisoformat(due)-today).days if due else None
        km=task.get("due_mileage");remaining_km=(km-mileages[task["vehicle_id"]]) if km is not None and task["vehicle_id"] in mileages else None
        if (days is not None and days<0) or (remaining_km is not None and remaining_km<0): stage="overdue";level="danger";timing="ya ha vencido"
        elif (days is not None and days==0) or (remaining_km is not None and remaining_km==0):stage="today";level="warning";timing="vence hoy"
        elif days is not None and days<=max(offsets):
            applicable=[o for o in offsets if days<=o]
            stage=f"{min(applicable)}d";level="warning" if days<=7 else "info";timing=f"vence en {days} días"
        elif remaining_km is not None and remaining_km<=1000:
            stage="1000km";level="warning";timing=f"está a {remaining_km} km del vencimiento"
        else:continue
        key=f"{user_id}:{task['id']}:{due or km}:{stage}"
        if db.scalar(select(Notification).where(Notification.dedupe_key==key)):continue
        n=Notification(user_id=user_id,vehicle_id=task["vehicle_id"],task_id=task["id"],dedupe_key=key,title=task["name"],body=f"El mantenimiento '{task['name']}' {timing}.",level=level,email_status="pending" if prefs.email_enabled else "disabled")
        db.add(n)
        try:db.commit();db.refresh(n)
        except IntegrityError:db.rollback();continue
        created+=1
        if prefs.email_enabled:
            try:deliver_email(email,f"MiGaraje · {n.title}",n.body);n.email_status="sent"
            except Exception:n.email_status="failed"
            db.commit()
    return {"created":created,"scanned":scanned}
