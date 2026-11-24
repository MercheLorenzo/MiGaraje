"""Promover o retirar el rol admin SIN endpoints públicos.

Dentro de Docker:
    docker compose exec gateway-service python -m app.scripts.set_admin --email usuario@example.com
Para retirar permisos:
    docker compose exec gateway-service python -m app.scripts.set_admin --email usuario@example.com --role user
"""
import argparse
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.account import User


def main():
    parser = argparse.ArgumentParser(description="Cambiar el rol de una cuenta existente")
    parser.add_argument("--email", required=True, help="Correo de una cuenta ya registrada")
    parser.add_argument("--role", choices=["user", "admin"], default="admin")
    args = parser.parse_args()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == args.email.strip().lower()))
        if not user:
            parser.error("No existe esa cuenta. Regístrala primero desde el frontend.")
        if user.role == args.role:
            print(f"La cuenta ya tiene rol {args.role}; no se ha modificado.")
            return
        user.role = args.role
        user.token_version += 1  # Revoca los JWT que fueron emitidos anteriormente.
        db.commit()
        print(f"Rol actualizado: {user.email} -> {args.role}. Cierra sesión y vuelve a entrar.")


if __name__ == "__main__":
    main()
