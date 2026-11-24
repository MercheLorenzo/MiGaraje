"""Generación idempotente del siguiente vencimiento de una regla."""
from calendar import monthrange
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.maintenance_rule import MaintenanceRule
from app.models.maintenance_task import MaintenanceTask


def add_months(day:date,months:int)->date:
    absolute=day.year*12+day.month-1+months
    year,month=divmod(absolute,12)
    return date(year,month+1,min(day.day,monthrange(year,month+1)[1]))

def generate_task(db:Session,rule:MaintenanceRule):
    if not rule.is_active:return None
    existing=db.scalar(select(MaintenanceTask).where(MaintenanceTask.rule_id==rule.id,MaintenanceTask.status!="completed").limit(1))
    if existing:return existing
    start_date=rule.last_performed_date or date.today()
    # Se calculan ambos límites y vence al cumplirse cualquiera de ellos.
    possibilities=[]
    if rule.interval_days:possibilities.append(start_date+timedelta(days=rule.interval_days))
    if rule.interval_months:possibilities.append(add_months(start_date,rule.interval_months))
    due_date=min(possibilities) if possibilities else None
    due_mileage=(rule.last_performed_mileage+rule.interval_kilometers) if rule.interval_kilometers and rule.last_performed_mileage is not None else None
    if not due_date and due_mileage is None:
        # Para una regla basada exclusivamente en km se requiere km de última realización.
        return None
    task=MaintenanceTask(vehicle_id=rule.vehicle_id,rule_id=rule.id,name=rule.name,description=rule.description,due_date=due_date,due_mileage=due_mileage,status="pending")
    db.add(task);db.commit();db.refresh(task)
    return task
