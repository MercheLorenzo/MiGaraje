"""Agregaciones globales desde el Gateway; las otras BBDD solo se consultan por API.

El acceso a estas funciones se limita a los endpoints que dependen de require_admin.
No se incluyen contraseñas ni hashes en las respuestas.
"""
from collections import defaultdict
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.clients.services_client import call
from app.models.account import User, VehicleOwner


def snapshot(db: Session):
    users = db.scalars(select(User).order_by(User.id)).all()
    owner_by_vehicle = dict(db.execute(select(VehicleOwner.vehicle_id, VehicleOwner.user_id)).all())
    user_by_id = {user.id: user for user in users}
    vehicles = call("vehicles", "GET", "/vehicles")
    maintenances = call("maintenance", "GET", "/maintenances")
    return users, owner_by_vehicle, user_by_id, vehicles, maintenances


def money(value):
    return round(float(value), 2)


def report_users(db: Session):
    users, owner_by_vehicle, _, vehicles, records = snapshot(db)
    ids = {v["id"] for v in vehicles}
    known_owners = {vid: owner_by_vehicle.get(vid) for vid in ids}
    counts = defaultdict(int)
    costs = defaultdict(lambda: Decimal("0"))
    for v in vehicles:
        counts[known_owners[v["id"]]] += 1
    mcounts = defaultdict(int)
    for r in records:
        uid = known_owners.get(r["vehicle_id"])
        mcounts[uid] += 1
        costs[uid] += Decimal(str(r["cost"]))
    return [{"id": u.id, "full_name": u.full_name, "email": u.email,
             "role": u.role, "created_at": u.created_at,
             "vehicle_count": counts[u.id], "maintenance_count": mcounts[u.id],
             "total_cost": money(costs[u.id])} for u in users]


def report_vehicles(db: Session, user_id: int | None = None):
    _, owner, user_by_id, vehicles, records = snapshot(db)
    counts = defaultdict(int)
    totals = defaultdict(lambda: Decimal("0"))
    for r in records:
        counts[r["vehicle_id"]] += 1
        totals[r["vehicle_id"]] += Decimal(str(r["cost"]))
    out = []
    for v in vehicles:
        uid = owner.get(v["id"])
        if user_id is not None and uid != user_id:
            continue
        u = user_by_id.get(uid)
        out.append({**v, "owner_id": uid, "owner_name": u.full_name if u else None,
                    "owner_email": u.email if u else None,
                    "maintenance_count": counts[v["id"]], "total_cost": money(totals[v["id"]])})
    return out


def report_maintenances(db: Session, user_id: int | None = None,
                        vehicle_id: int | None = None, year: int | None = None):
    _, owner, user_by_id, vehicles, records = snapshot(db)
    vehicle_by_id = {v["id"]: v for v in vehicles}
    out = []
    for r in records:
        uid = owner.get(r["vehicle_id"])
        if user_id is not None and uid != user_id:
            continue
        if vehicle_id is not None and r["vehicle_id"] != vehicle_id:
            continue
        if year is not None and str(r["date"])[:4] != str(year):
            continue
        u = user_by_id.get(uid)
        v = vehicle_by_id.get(r["vehicle_id"])
        out.append({**r, "owner_id": uid, "owner_name": u.full_name if u else None,
                    "owner_email": u.email if u else None,
                    "vehicle_label": f"{v['brand']} {v['model']}" if v else f"Vehículo #{r['vehicle_id']}"})
    return sorted(out, key=lambda row: (str(row["date"]), row["id"]), reverse=True)


def report_overview(db: Session, year: int | None = None):
    users, owner, _, vehicles, records = snapshot(db)
    selected = [r for r in records if year is None or str(r["date"])[:4] == str(year)]
    total = sum((Decimal(str(r["cost"])) for r in selected), Decimal("0"))
    groups = defaultdict(lambda: {"count": 0, "total": Decimal("0")})
    months = defaultdict(lambda: {"count": 0, "total": Decimal("0")})
    for r in selected:
        value = Decimal(str(r["cost"]))
        groups[r["maintenance_type"]]["count"] += 1
        groups[r["maintenance_type"]]["total"] += value
        key = str(r["date"])[:7]
        months[key]["count"] += 1
        months[key]["total"] += value
    return {
        "year": year,
        "user_count": len(users),
        "vehicle_count": len(vehicles),
        "unassigned_vehicle_count": sum(v["id"] not in owner for v in vehicles),
        "maintenance_count": len(selected),
        "total_cost": money(total),
        "average_cost": money(total / len(selected)) if selected else 0.0,
        "categories": [{"category": key, "count": v["count"], "total": money(v["total"])}
                       for key, v in sorted(groups.items(), key=lambda x: x[1]["total"], reverse=True)],
        "monthly": [{"month": key, "count": v["count"], "total": money(v["total"])}
                    for key, v in sorted(months.items())],
    }
