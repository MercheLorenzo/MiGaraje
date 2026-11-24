"""Asigna vehículos heredados sin propietario a una cuenta ya existente.

Uso por operador local, DENTRO del contenedor:
python -m app.tools.claim_legacy_vehicles --email tu@correo.es --vehicle-ids 1 2
No toma vehículos ya asignados a otras cuentas.
"""
import argparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.services_client import call
from app.db.session import SessionLocal
from app.models.account import User, VehicleOwner


def assign(db: Session, email: str, vehicle_ids: list[int]):
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if not user:
        raise ValueError("Primero registra esa cuenta desde MiGaraje")
    actual_ids = {v["id"] for v in call("vehicles", "GET", "/vehicles")}
    if not vehicle_ids or any(vid not in actual_ids or vid <= 0 for vid in vehicle_ids):
        raise ValueError("Alguno de los identificadores no corresponde a un vehículo existente")
    already_owned = db.scalars(select(VehicleOwner).where(VehicleOwner.vehicle_id.in_(vehicle_ids))).all()
    if already_owned:
        raise ValueError("Al menos uno de los vehículos ya está asignado a una cuenta. No se modificará nada")
    for vid in vehicle_ids:
        db.add(VehicleOwner(vehicle_id=vid, user_id=user.id))
    db.commit()
    return len(vehicle_ids)


def main():
    parser = argparse.ArgumentParser(description="Asignar vehículos sin propietario a una cuenta")
    parser.add_argument("--email", required=True, help="Correo de la cuenta ya registrada")
    parser.add_argument("--vehicle-ids", type=int, nargs="+", required=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        count = assign(db, args.email, args.vehicle_ids)
    print(f"Se han asociado {count} vehículos a {args.email}")


if __name__ == "__main__":
    main()
