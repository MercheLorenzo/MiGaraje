import json
import sys
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


VEHICLES_URL = "http://localhost:8000"
MAINTENANCE_URL = "http://localhost:8001"
PLANNING_URL = "http://localhost:8002"
TEST_LICENSE_PLATE = f"INT-{uuid.uuid4().hex[:8].upper()}"


def request(method, url, payload=None):
    """Realiza una petición HTTP y devuelve el estado y el JSON recibido."""
    data = None

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )

    try:
        with urlopen(req, timeout=10) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None
    except HTTPError as exc:
        body = exc.read()
        return exc.code, json.loads(body) if body else None
    except URLError as exc:
        raise AssertionError(f"No se pudo conectar con {url}: {exc}") from exc


def check(description, method, url, payload, expected_status):
    status_code, body = request(method, url, payload)

    assert status_code == expected_status, (
        f"{description}: se esperaba HTTP {expected_status}, "
        f"pero se recibió HTTP {status_code}. Respuesta: {body}"
    )

    print(f"OK: {description} (HTTP {status_code})")
    return body


def main():
    # 1. Comprobar que los tres servicios están preparados.
    for service, url in [
        ("vehicles-service", VEHICLES_URL),
        ("maintenance-service", MAINTENANCE_URL),
        ("maintenance-planning-service", PLANNING_URL),
    ]:
        check(
            f"Disponibilidad de {service}",
            "GET",
            f"{url}/health/ready",
            None,
            200,
        )

    # 2. Crear un vehículo.
    vehicle = check(
        "Crear vehículo",
        "POST",
        f"{VEHICLES_URL}/vehicles",
        {
            "brand": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "license_plate": TEST_LICENSE_PLATE,
            "current_mileage": 25000,
        },
        201,
    )

    vehicle_id = vehicle["id"]

    # 3. Crear un mantenimiento.
    # El maintenance-service debe verificar el vehículo
    # consultando al vehicles-service real.
    check(
        "Crear mantenimiento asociado a un vehículo existente",
        "POST",
        f"{MAINTENANCE_URL}/maintenances",
        {
            "vehicle_id": vehicle_id,
            "maintenance_type": "Cambio de aceite",
            "date": "2026-11-07",
            "mileage": 25000,
            "description": "Cambio de aceite y revisión",
            "cost": "85.50",
            "products_used": "Aceite 5W30",
        },
        201,
    )

    # 4. Comprobar que maintenance-service rechaza un vehículo inexistente.
    check(
        "Rechazar mantenimiento de vehículo inexistente",
        "POST",
        f"{MAINTENANCE_URL}/maintenances",
        {
            "vehicle_id": 999999,
            "maintenance_type": "Revisión",
            "date": "2026-11-07",
            "mileage": 10000,
            "description": "Prueba de integración",
            "cost": "50.00",
        },
        422,
    )

    # 5. Crear una regla de mantenimiento.
    check(
        "Crear regla de mantenimiento",
        "POST",
        f"{PLANNING_URL}/maintenance-rules",
        {
            "vehicle_id": vehicle_id,
            "name": "Cambio periódico de aceite",
            "maintenance_type": "Cambio de aceite",
            "interval_months": 12,
            "interval_kilometers": 15000,
            "last_performed_date": "2026-11-07",
            "last_performed_mileage": 25000,
        },
        201,
    )

    # 6. Comprobar que planning-service rechaza un vehículo inexistente.
    check(
        "Rechazar regla para vehículo inexistente",
        "POST",
        f"{PLANNING_URL}/maintenance-rules",
        {
            "vehicle_id": 999999,
            "name": "Regla inválida",
            "maintenance_type": "Revisión",
            "interval_months": 12,
        },
        422,
    )

    # 7. Crear una tarea de mantenimiento.
    check(
        "Crear tarea de mantenimiento",
        "POST",
        f"{PLANNING_URL}/maintenance-tasks",
        {
            "vehicle_id": vehicle_id,
            "name": "Revisar presión de neumáticos",
            "due_date": "2026-12-07",
        },
        201,
    )

    # 8. Comprobar que planning-service rechaza una tarea
    # asociada a un vehículo inexistente.
    check(
        "Rechazar tarea para vehículo inexistente",
        "POST",
        f"{PLANNING_URL}/maintenance-tasks",
        {
            "vehicle_id": 999999,
            "name": "Tarea inválida",
            "due_date": "2026-12-07",
        },
        422,
    )

    print("\nTodas las pruebas de integración han finalizado correctamente.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError, ValueError) as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
