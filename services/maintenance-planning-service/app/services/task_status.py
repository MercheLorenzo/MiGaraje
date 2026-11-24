"""Única regla de vencimiento compartida por los listados y consultas REST.

Una tarea vence al sobrepasar *cualquiera* de sus límites (fecha o km).
La igualdad con el kilometraje es «próxima», como en el frontend actual.
"""
from datetime import date, timedelta

from app.models.maintenance_task import MaintenanceTask


def calculate_task_status(
    task: MaintenanceTask,
    *,
    today: date,
    current_mileage: int | None,
) -> str:
    if task.status == "completed":
        return "completed"

    overdue_date = task.due_date is not None and task.due_date < today
    overdue_km = (
        task.due_mileage is not None
        and current_mileage is not None
        and current_mileage > task.due_mileage
    )
    if overdue_date or overdue_km:
        return "overdue"

    upcoming_date = (
        task.due_date is not None
        and task.due_date <= today + timedelta(days=30)
    )
    upcoming_km = (
        task.due_mileage is not None
        and current_mileage is not None
        and current_mileage >= task.due_mileage - 1000
    )
    return "upcoming" if (upcoming_date or upcoming_km) else "pending"
