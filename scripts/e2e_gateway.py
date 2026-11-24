#!/usr/bin/env python3
"""Smoke test REAL de MiGaraje a través de su API pública y el frontend.

Crea dos usuarios y registros temporales. Para impedir su ejecución por error
sobre datos reales, exige MIGARAJE_E2E_ALLOW_WRITES=1. Recomendado únicamente
para CI o una instalación local de pruebas (se eliminan los vehículos al final,
pero las cuentas de prueba permanecen en la base de datos).

Dependencias: biblioteca estándar de Python 3.12.
"""
import json
import os
import sys
import uuid
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = os.getenv("MIGARAJE_E2E_API", "http://127.0.0.1:8090").rstrip("/")
WEB = os.getenv("MIGARAJE_E2E_WEB", "http://127.0.0.1:8081").rstrip("/")


def http(method, path, *, token=None, body=None, base=API):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    req = Request(f"{base}{path}", method=method, headers=headers, data=data)
    try:
        with urlopen(req, timeout=25) as resp:
            status = resp.status
            raw = resp.read()
    except HTTPError as e:
        status, raw = e.code, e.read()
    except URLError as e:
        raise AssertionError(f"No se puede conectar con {base}{path}: {e}") from e
    try:
        result = json.loads(raw) if raw else None
    except ValueError:
        result = raw.decode("utf-8", errors="replace")
    return status, result


def expect(method, path, code, *, token=None, body=None, base=API):
    actual, result = http(method, path, token=token, body=body, base=base)
    assert actual == code, (
        f"{method} {path}: se esperaba {code}, se recibió {actual}. "
        f"Respuesta: {str(result)[:700]}"
    )
    return result


def check(name):
    print(f"OK: {name}", flush=True)


def main():
    if os.environ.get("MIGARAJE_E2E_ALLOW_WRITES") != "1":
        raise RuntimeError(
            "Prueba bloqueada: se crean cuentas y datos. Actívala únicamente "
            "en un entorno desechable con MIGARAJE_E2E_ALLOW_WRITES=1."
        )

    expect("GET", "/health/ready", 200)
    page = expect("GET", "/", 200, base=WEB)
    assert isinstance(page, str) and "MiGaraje" in page
    check("Gateway y frontend de producción disponibles")

    paths = expect("GET", "/openapi.json", 200)["paths"]
    assert all(x in paths for x in (
        "/api/vehicles", "/api/maintenances", "/api/rules", "/api/tasks",
        "/api/statistics/summary", "/api/notifications/scan",
    ))
    check("Swagger contiene los endpoints REST explícitos")

    run_id = uuid.uuid4().hex[:12]
    password = "MiGaraje_CI_Secreta_2026!"
    accounts = []
    for index in (1, 2):
        email = f"migaraje-ci-{run_id}-{index}@example.com"
        session = expect("POST", "/api/auth/register", 201, body={
            "full_name": f"Prueba CI {index}", "email": email, "password": password,
        })
        assert session["user"]["email"] == email
        login = expect("POST", "/api/auth/login", 200, body={
            "email": email, "password": password,
        })
        accounts.append(login["token"])
    a, b = accounts
    expect("GET", "/api/vehicles", 401)
    assert expect("GET", "/api/auth/me", 200, token=a)["full_name"] == "Prueba CI 1"
    check("Registro, login y protección JWT")

    vehicle = {
        "brand": "Seat", "model": "Ibiza", "year": 2021,
        "license_plate": f"CI{run_id[:8].upper()}", "current_mileage": 10000,
    }
    car = expect("POST", "/api/vehicles", 201, token=a, body=vehicle)
    vid = car["id"]
    assert len(expect("GET", "/api/vehicles", 200, token=a)) == 1
    assert expect("GET", "/api/vehicles", 200, token=b) == []
    expect("GET", f"/api/vehicles/{vid}", 404, token=b)
    check("Crear vehículo y comprobar aislamiento entre usuarios")

    maintenance = {
        "vehicle_id": vid, "maintenance_type": "oil_change",
        "date": date.today().isoformat(), "mileage": 10000,
        "description": "Cambio de aceite CI", "cost": "95.50",
    }
    maint = expect("POST", "/api/maintenances", 201, token=a, body=maintenance)
    assert len(expect("GET", "/api/maintenances", 200, token=a)) == 1
    expect("GET", f"/api/maintenances/{maint['id']}", 404, token=b)
    report = expect("GET", f"/api/statistics/summary?year={date.today().year}", 200, token=a)
    assert abs(float(report["total_cost"]) - 95.5) < 0.01, report
    assert report["maintenance_count"] == 1, report
    others = expect("GET", f"/api/statistics/summary?year={date.today().year}", 200, token=b)
    assert others["maintenance_count"] == 0, others
    check("Mantenimiento, estadísticas e independencia de datos")

    rule = expect("POST", "/api/rules", 201, token=a, body={
        "vehicle_id": vid, "name": "Aceite cada 500 km", "maintenance_type": "oil_change",
        "interval_kilometers": 500, "last_performed_mileage": 10000,
    })
    task = expect("POST", f"/api/rules/{rule['id']}/generate", 201, token=a)
    tid = task["id"]
    assert task["due_mileage"] == 10500 and task["due_date"] is None, task
    upcoming = expect("GET", "/api/tasks?status=upcoming", 200, token=a)
    assert any(t["id"] == tid for t in upcoming), upcoming
    assert not any(t["id"] == tid for t in expect("GET", "/api/tasks?status=overdue", 200, token=a))

    vehicle["current_mileage"] = 10501
    expect("PUT", f"/api/vehicles/{vid}", 200, token=a, body=vehicle)
    overdue = expect("GET", "/api/tasks?status=overdue", 200, token=a)
    assert any(t["id"] == tid for t in overdue), overdue
    assert expect("GET", f"/api/tasks/{tid}", 200, token=a)["status"] == "overdue"
    assert expect("GET", "/api/tasks?status=overdue", 200, token=b) == []
    check("Regla por km, filtro de próximas/vencidas y consistencia GET individual")

    prefs = expect("GET", "/api/notifications/preferences", 200, token=a)
    assert "email_enabled" in prefs
    expect("PUT", "/api/notifications/preferences", 200, token=a, body={
        "email_enabled": False, "reminder_offsets_days": [30, 7, 1],
    })
    scan = expect("POST", "/api/notifications/scan", 200, token=a)
    assert scan["created"] >= 1, scan
    notices = expect("GET", "/api/notifications", 200, token=a)
    assert any(n["task_id"] == tid for n in notices), notices
    assert expect("POST", "/api/notifications/scan", 200, token=a)["created"] == 0
    notice = next(n for n in notices if n["task_id"] == tid)
    marked = expect("PATCH", f"/api/notifications/{notice['id']}/read", 200, token=a)
    assert marked["is_read"]
    assert expect("GET", "/api/notifications", 200, token=b) == []
    check("Avisos por km, deduplicación, marcado como leído y aislamiento")

    finished = expect("PATCH", f"/api/tasks/{tid}/complete", 200, token=a, body={
        "completed_date": date.today().isoformat(), "completed_mileage": 10501,
    })
    assert finished["status"] == "completed"
    assert any(t["id"] == tid for t in expect("GET", "/api/tasks?status=completed", 200, token=a))
    assert not any(t["id"] == tid for t in expect("GET", "/api/tasks?status=overdue", 200, token=a))
    check("Completar tarea y generar siguiente mantenimiento")

    expect("DELETE", f"/api/vehicles/{vid}", 204, token=a)
    assert expect("GET", "/api/vehicles", 200, token=a) == []
    assert expect("GET", "/api/maintenances", 200, token=a) == []
    assert expect("GET", "/api/rules", 200, token=a) == []
    assert expect("GET", "/api/tasks", 200, token=a) == []
    assert expect("GET", "/api/notifications", 200, token=a) == []
    check("Borrado integral de vehículo y limpieza de registros/avisos")
    print("\nPRUEBA E2E COMPLETA: OK", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, RuntimeError, KeyError, TypeError, ValueError) as exc:
        print(f"ERROR E2E: {exc}", file=sys.stderr)
        sys.exit(1)
